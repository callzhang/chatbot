import pandas as pd
import streamlit as st
import os, re, time, ast
from datetime import datetime
from pathlib import Path
from retry import retry
from functools import wraps
from collections import defaultdict

WIDE_LAYOUT_THRESHOLD = 1000
SUGGESTION_TOKEN = '[SUGGESTION]'
FINISH_TOKEN = 'data: [DONE]'
RETRY_TOKEN = '[RETRY]'
TIMEOUT = 30
LOGIN_CODE = 'login_code'


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
# 导出对话内容到 markdown
def conversation2markdown(conversation, title=""):
    history = pd.DataFrame(conversation).query('role not in ["system", "audio"]')
    # export markdown
    md_formated = f"""# 关于“{title}”的对话记录
*导出日期：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n
"""
    for i, c in history.iterrows():
        role, content, task, name, time = c['role'], c['content'], c.get('task'), c.get('name'), c.get('time')
        if role == "user":
            md_formated += '---\n'
            md_formated += f"""**[{time}]{name}({task}): {content}**\n\n"""
        elif role in ["assistant"]:
            md_formated += f"""星尘小助手({name}): {content}\n\n"""
        elif role == "DALL·E":
            md_formated += f"""星尘小助手({name}): {content}\n\n"""
        else:
            raise Exception(f'Unhandled chat: {c}')
    return md_formated.encode('utf-8').decode()


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


## 处理提示
def parse_suggestions(content:str):
    reply = content
    suggestions = []
    if SUGGESTION_TOKEN in content:
        pattern1 = r'(\[SUGGESTION\]:\s?)(\[.+\])'
        pattern2 = r'(\[SUGGESTION\]:\s?)(.{3,})'
        pattern3 = r'\[SUGGESTION\]|启发性问题:\s*'
        pattern31 = r'(-\s|\d\.\s)(.+)'
        matches1 = re.findall(pattern1, reply)
        matches2 = re.findall(pattern2, reply)
        matches3 = re.findall(pattern3, reply)
        
        if matches1:
            for m in matches1:
                reply = reply.replace(''.join(m), '')
                try:
                    suggestions += ast.literal_eval(m[1])
                except:
                    print('==>Error parsing suggestion:<===\n', content)
        elif len(matches2)>=3:
            for m in matches2:
                reply = reply.replace(''.join(m), '')
                suggestions.append(m[1].strip())
        elif matches3:
            # assume only one match
            replies = content.split(matches3[0])
            reply = replies[0]
            for r in replies[1:]:
                match31 = re.findall(pattern31, r)
                suggestions += [m[1].strip() for m in match31]
                for m in match31:
                    r = r.replace(''.join(m), '')
                reply += r

    return reply, suggestions

def filter_suggestion(content:str):
    pattern = r'\[?SUGGESTION\].*$'
    content = '\n'.join(re.split(pattern, content, re.MULTILINE))
    return content

## 管理秘钥
import json, toml
@cached()
def default_key():
    with open('.streamlit/secrets.toml', 'r') as f:
        data = toml.load(f)
    return data['key']

@cached()
def get_openai_key(username, fallback=True):
    openai_key_file = f'secrets/{username}/openai_key.json'
    if not os.path.exists(openai_key_file):
        if fallback:
            return default_key()
        else:
            return None
    key = json.load(open(openai_key_file, 'r'))['openai_key']
    return key

@cached()
def get_bingai_key(username, file_only=False):
    bing_key_file = f'secrets/{username}/bing_key.json'
    if not os.path.exists(bing_key_file):
        return None
    print(f'bing_key_file: {bing_key_file}')
    if file_only:
        return bing_key_file
    with open(bing_key_file, 'r') as f:
        key = f.read()
    return key

## user auth
sheet_url = st.secrets["public_gsheets_url"]
from shillelagh.backends.apsw.db import connect

# user management
@cached(timeout=600)
@retry(tries=3, delay=2, backoff=2)
def get_db():
    print('connecting to google sheet...')
    conn = connect(":memory:")
    cursor = conn.cursor()
    query = f'SELECT * FROM "{sheet_url}"'
    rows = cursor.execute(query)
    rows = rows.fetchall()
    df = pd.DataFrame(rows, columns=['姓名', '访问码', '截止日期'])
    print(f'Fetched {len(df)} records')
    return df


if __name__ == '__main__':
    db = get_db()
    print(db)