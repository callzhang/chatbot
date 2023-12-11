import oss2
import requests
import os, re, time,logging, ast
from transformers import GPT2Tokenizer
from collections import defaultdict
from functools import wraps
from datetime import datetime, timedelta
import streamlit as st
from io import BytesIO
from functools import lru_cache


# Create an OSS service
auth = oss2.Auth(st.secrets.accessKeyId, st.secrets.accessKeySecret)
bucket_name = 'stardust-public'
endpoint = 'oss-cn-hangzhou.aliyuncs.com'
bucket = oss2.Bucket(auth, endpoint=endpoint, bucket_name=bucket_name)

## logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)  # Set the minimum level of log messages to capture
# Create a file handler to write logs to a file
file_handler = logging.FileHandler('log.txt')
file_handler.setLevel(logging.DEBUG)  # Set the minimum level for file logging
# Create a console handler to print logs to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set the minimum level for console logging
# Create a formatter and set it for both handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

## token size
tokenizer = GPT2Tokenizer.from_pretrained("gpt2") # local_files_only?
def token_size(text:str):
    if not text:
        return 0
    if not isinstance(text, str):
        text = str(text)
        print(f'Warning: text is not str, converted to str: {text}')
    return len(tokenizer.encode(text))

def truncate_text(text, max_len=1024):
    tokens = tokenizer.tokenize(text)
    text_t = tokenizer.convert_tokens_to_string(tokens[:max_len])
    return text_t

## cache management
def cached(timeout=3600):
    # thread safe cache
    cache = defaultdict()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
    
            if key not in cache or time.time() - cache[key]['time'] > timeout:
                result = func(*args, **kwargs)
                cache[key] = {'result': result, 'time': time.time()}
            return cache[key]['result']

        wrapper.cache = cache
        # f.clear_cache() to clear the cache
        wrapper.clear_cache = cache.clear
        # f.delete_cache(key) to delete the cache of key
        wrapper.delete_cache = cache.pop
        return wrapper

    return decorator

## Markdown
# utls to markdown
def url2markdown(urls):
    md_formated = ""
    for i, url in enumerate(urls):
        md_formated += f"""![图{i+1}]({url})\n\n"""
    # print(f'md_formated: {md_formated}')
    return md_formated


# check if string is in markdown format
def is_markdown(text):
    # all markdown syntax
    patterns = [
        r'\n\d\.\s',  # ordered list
        r'\*\*|__',  # bold
        r'\n-\s',  # unordered list
        r'\n>\s',  # blockquote
        r'\n#+\s',  # header
        r'`(.*?)`',  # inline code
        r'\n`{3}.*?\\n`{3}',  # code block
        r'\n---\n',  # horizontal rule
        r'\!\[(.*?)\]\((.*?)\)',  # image
    ]
    matches = [re.findall(pattern, text) for pattern in patterns]
    is_md = any(matches)
    return is_md


def url2html(urls):
    # convert urls to html tags
    html_tags = ""
    for i, url in enumerate(urls):
        html_tags += f"<p><a href='{url}' target='_top'><img src='{url}' height='150px' alt=图{i}></a><p>"
    return html_tags


# file utils
from urllib.parse import urlparse
import mimetypes
def parse_file_info(path_or_str):
    if isinstance(path_or_str, str):
        path_or_str = urlparse(path_or_str).path
    filename = os.path.basename(path_or_str)
    mime_type, encoding = mimetypes.guess_type(filename)
    # filetype = os.path.splitext(filename)[-1].replace('.','')
    return filename, mime_type

# excel 
def excel_num_to_datetime(excel_num):
    # Excel's epoch starts on December 30, 1899
    epoch = datetime(1899, 12, 30)

    # Split the number into days and fractional days
    days = int(excel_num)
    fractional_day = excel_num - days

    # Convert the fractional day to seconds
    seconds_in_day = 24 * 60 * 60
    total_seconds = int(fractional_day * seconds_in_day)

    # Calculate hours, minutes, and seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Convert the Excel number to a datetime
    converted_date = epoch + \
        timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return converted_date


# oss
from streamlit.runtime.uploaded_file_manager import UploadedFile
def save_uri_to_oss(uri:str|UploadedFile, prefix=''):
    if prefix and prefix.endswith('/'):
        prefix += '/'
    if isinstance(uri, UploadedFile):
        fileObj = uri
        file_content = fileObj.getvalue()
        file_name = fileObj.name
        file_type = fileObj.type.split('/')[-1]
        object_name = f'{file_name}.{file_type}'
    elif isinstance(uri, str):
        assert endpoint not in uri, f'Double upload: {uri}, please check your code!'
        object_name, mime = parse_file_info(uri)
        if uri.startswith('http'):
            # Download the file from the URL
            response = requests.get(uri)
            if not response.ok:
                raise Exception(f'Failed to download file from url: {uri}, reason:\n {response.text}')
            file_content = response.content
        elif os.path.exists(uri):
            with open(uri, 'rb') as f:
                file_content = f.read()

    # Upload the file to OSS
    object_path = f'data/chatbot/{prefix}{object_name}'
    bucket.put_object(object_path, file_content)
    # http://stardust-public.oss-cn-hangzhou.aliyuncs.com/data/mart/5fb60bfa-43f6-44e7-94c0-8683eb9ee99a.jpeg
    oss_url = f"https://{bucket_name}.{endpoint}/{object_path}"
    print(f'Uploaded to OSS: {oss_url}')
    return oss_url, file_content


# 处理提示
SUGGESTION_TOKEN = '[SUGGESTION]'
def parse_suggestions(content: str):
    if not content:
        return None, None
    reply = content
    suggestions = []
    # pattern = r'(\[.+\])' #fallback
    if SUGGESTION_TOKEN in content or '启发性问题' in content:
        pattern1 = r'((\[SUGGESTION\]|启发性问题)[:：]?\s*).*?(\[.+?\])'
        pattern2 = r'((\[SUGGESTION\]|启发性问题)[:：]?\s*)(.{5,})'
        pattern3 = r'((\[SUGGESTION\]|启发性问题)[:：]?\s*)'
        pattern31 = r'(-\s|\d\.\s?)(.+)'
        matches1 = re.findall(pattern1, reply, re.DOTALL)
        matches2 = re.findall(pattern2, reply)
        matches3 = re.findall(pattern3, reply)
        if matches1:# 匹配[]所有内容
            for m in matches1:
                # reply = reply.replace(''.join(m), '')
                for c in m:
                    reply = reply.replace(c, '')
                try:
                    suggestions += ast.literal_eval(m[2])
                except:
                    print('==>Error parsing suggestion:<===\n', content)
        elif len(matches2) >= 3:#匹配多行[SUGGESTION]:...
            for m in matches2:
                for c in m:
                    reply = reply.replace(c, '')
                suggestions.append(m[2].strip())
        elif matches3:#匹配关键词
            # assume only one match
            reply = reply.replace(matches3[0][0], '')
            contents = content.split(matches3[0][0])
            remove_lines = []
            for c in contents[1:]:
                match31 = re.findall(pattern31, c, re.MULTILINE)
                suggestions += [m[1].strip() for m in match31]
                remove_lines += [''.join(m) for m in match31]
            for s in remove_lines:
                reply = reply.replace(s, '')
        if not suggestions:
            print(f'Failed to detect suggestion for content:\n{content}')

    return reply, suggestions


def filter_suggestion(content: str):
    pattern = r'\[?SUGGESTION\].*$'
    content = '\n'.join(re.split(pattern, content, re.MULTILINE))
    return content


if __name__ == '__main__':
    # print(token_size('hello world'))
    # print(truncate_text('These smaller models provide a good balance between performance and resource usage, making them suitable for environments where computational resources are a concern. Remember that while smaller models are faster and use less memory, they might not capture the nuances of language as effectively as larger models like GPT-2 or BERT-base.', 5))
    
    # save_uri_to_oss('voice.mp3', 'Derek')
    
    # suggestion
    content = '''根据最新paper《A Survey of Large Language Models》，近年来，大型语言模型在自然语言处理领域取得了重大进展。这项研究主要关注大型预训练语言模型（PLMs），它们通过在大规模语料库上进行Transformer模型的预训练，展现出解决各种自然语言处理任务的强大能力。研究人员发现通过增加模型大小可以提高性能，并且在参数规模超过一定水平后，这些扩大的语言模型不仅带来显著的性能提升，还展现出一些小规模语言模型所没有的特殊能力。这些被称为大型语言模型（LLMs）的扩大规模的语言模型已成为学术界和工业界的研究热点。

该研究从大型语言模型的背景、关键发现和主流技术等四个方面进行了综述。它聚焦于大型语言模型的预训练、适应性调整、利用和容量评估四个主要方面。此外，该研究还总结了为开发大型语言模型提供的可用资源，并讨论了未来方向的剩余问题。

另外，一个重要的进展是ChatGPT的推出，这备受社会广泛关注。大型语言模型的技术演进对整个AI社区产生了重要影响，将彻底改变我们开发和使用AI算法的方式。

在另一篇文章中，介绍了几篇关于了解大型语言模型架构、提高大型语言模型性能、以及满足用户需求的论文，还列举了一些类似于ChatGPT的替代作品。这些论文将有助于加深对大型语言模型的理解和启发。

总的来说，这些文章和论文对于了解大型语言模型的发展和应用具有重要意义，并且显示出大型语言模型在自然语言处理领域的潜力和前景。

:["了解大型语言模型的发展有助于实现哪些自然语言处理的应用？", "大型语言模型与传统语言模型的区别在哪里？", "大型语言模型的未来发展方向是什么？"]'''
    content, suggestion = parse_suggestions(content)
    print(suggestion)
