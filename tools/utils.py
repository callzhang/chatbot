import os, re
from transformers import GPT2Tokenizer

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

# token size
def token_size(text):
    return len(tokenizer.encode(text))

def truncate_text(text, max_len=1024):
    tokens = tokenizer.tokenize(text)
    text_t = tokenizer.convert_tokens_to_string(tokens[:max_len])
    return text_t

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


if __name__ == '__main__':
    print(token_size('hello world'))
    print(truncate_text('These smaller models provide a good balance between performance and resource usage, making them suitable for environments where computational resources are a concern. Remember that while smaller models are faster and use less memory, they might not capture the nuances of language as effectively as larger models like GPT-2 or BERT-base.', 5))
    