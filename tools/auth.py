import pandas as pd
import streamlit as st
import os, time
from . import model, utils
from retry import retry


## 管理秘钥
import json, toml
@utils.cached()
def get_default_key(task):
    with open('.streamlit/secrets.toml', 'r') as f:
        data = toml.load(f)
    if task == model.Task.GPT4.name:
        key = data.get('gpt4-key')
    elif task == model.Task.GPT4V.name:
        key = data.get('gpt4v-key')
    else:
        key = data.get(f'openai-key')
    return key


@utils.cached()
def get_openai_key(task=None, username=None):
    username=st.session_state.name
    my_openai_key_file = f'secrets/{username}/openai_key.json'
    if os.path.exists(my_openai_key_file):
        key = json.load(open(my_openai_key_file, 'r'))['openai_key']
    else:
        # 只有在没有秘钥的时候才会使用默认秘钥，在这里可以拿到特殊GPT4秘钥
        key = get_default_key(task)
    return key


@utils.cached()
def get_bingai_key(return_json=False):
    username=st.session_state.name
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


def get_apify_token():
    with open('.streamlit/secrets.toml', 'r') as f:
        data = toml.load(f)
    return data.get('apify_token')

## user auth
sheet_url = st.secrets["public_gsheets_url"]
from shillelagh.backends.apsw.db import connect

# user management
@utils.cached(timeout=600)
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