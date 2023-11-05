import pandas as pd
import streamlit as st
import os, re, time, ast
from datetime import datetime
from pathlib import Path
from retry import retry
from functools import wraps
from collections import defaultdict
from . import model


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


def url2html(urls):
    # convert urls to html tags
    html_tags = ""
    for i, url in enumerate(urls):
        html_tags += f"<p><a href='{url}' target='_top'><img src='{url}' height='150px' alt=图{i}></a><p>"
    return html_tags



## 管理秘钥
import json, toml
@cached()
def default_openai_key(task):
    with open('.streamlit/secrets.toml', 'r') as f:
        data = toml.load(f)
    if task == 'GPT4':
        key = data.get('gpt4-key')
    else:
        key = data.get(f'openai-key')
    return key

@cached()
def get_openai_key(username, task=None):
    openai_key_file = f'secrets/{username}/openai_key.json'
    if os.path.exists(openai_key_file):
        key = json.load(open(openai_key_file, 'r'))['openai_key']
    else:
        # 只有在没有秘钥的时候才会使用默认秘钥，在这里可以拿到特殊GPT4秘钥
        key = default_openai_key(task)
    return key

@cached()
def get_bingai_key(username, return_json=False):
    bing_key_file = f'secrets/{username}/bing_key.json'
    if not os.path.exists(bing_key_file):
        return None
    print(f'bing_key_file: {bing_key_file}')
    with open(bing_key_file, 'r') as f:
        key = f.read()
    if return_json:
        return json.loads(key)
    else:
        return key

## user auth
sheet_url = st.secrets["public_gsheets_url"]
from shillelagh.backends.apsw.db import connect

# user management
@cached(timeout=600)
@retry(tries=3, delay=2, backoff=2)
def get_db():
    msg = st.toast('正在连接数据库，请稍等...')
    conn = connect(":memory:")
    cursor = conn.cursor()
    query = f'SELECT * FROM "{sheet_url}"'
    rows = cursor.execute(query)
    rows = rows.fetchall()
    df = pd.DataFrame(rows, columns=['姓名', '访问码', '截止日期'])
    msg.toast('数据库连接成功！')
    print(f'Fetched {len(df)} records')
    time.sleep(1)
    return df


if __name__ == '__main__':
    db = get_db()
    print(db)