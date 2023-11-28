import oss2
import requests
import os, re, time,logging
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
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
def token_size(text):
    if not text:
        return 0
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
def save_uri_to_oss(uri:str|BytesIO, prefix=''):
    if prefix and prefix.endswith('/'):
        prefix += '/'
    if isinstance(uri, BytesIO):
        file_content = uri.getvalue()
        object_name = f'tts_{datetime.now()}.mp3'
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
    return oss_url, file_content

if __name__ == '__main__':
    # print(token_size('hello world'))
    # print(truncate_text('These smaller models provide a good balance between performance and resource usage, making them suitable for environments where computational resources are a concern. Remember that while smaller models are faster and use less memory, they might not capture the nuances of language as effectively as larger models like GPT-2 or BERT-base.', 5))
    
    save_uri_to_oss('voice.mp3', 'Derek')