from gspread_pandas import Spread, Client
import pandas as pd
import streamlit as st
import os, time
from . import model, utils, google_sheet
from retry import retry
from datetime import datetime, timedelta

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
    
    username=st.session_state.name if 'name' in st.session_state else 'NA'
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
client = google_sheet.init_client()
sheet_url = st.secrets["public_gsheets_url"]
# 用户名	访问码	截止日期
@utils.cached(timeout=600)
@retry(tries=3, delay=2, backoff=2)
def get_user_db():
    db = Spread(sheet_url, client=client)
    df = db.sheet_to_df()
    df['截止日期'] = pd.to_datetime(df['截止日期'])
    print(f'Fetched {len(df)} user records')
    return df

def validate_code(code:str):
    user_db = get_user_db()
    access_data = user_db.query('访问码==@code')
    authenticated = False
    username = code
    cookie_exp_date = datetime.now() + timedelta(days=10)# set cookie expire date to 10 days later
    if len(access_data):
        username = access_data.index.values[0]
        expiration = access_data['截止日期'].iloc[0]
        if datetime.now().date() < expiration.date():
            # login success
            authenticated = True
            st.session_state.guest = False
            cookie_exp_date = datetime(expiration.year, expiration.month, expiration.day, 23, 59, 59)
    elif user_db.query('用户名==@code'):
        #登录码=用户名，增加一层防护
        username = "Visitor_"+code
    return username, cookie_exp_date, authenticated


def add_user(username:str, code:str, expiration:str):
    user_db = get_user_db()
    if username in user_db.index:
        st.error(f'用户{username}已存在')
        return
    user_db.loc[username] = [code, expiration]
    db = Spread(sheet_url, client=client)
    db.df_to_sheet(user_db, index=True, sheet='用户信息', start='A1', replace=True)
    st.success(f'用户{username}添加成功！')
    
def delete_user(username:str):
    user_db = get_user_db()
    if username not in user_db.index:
        st.error(f'用户{username}不存在')
        return
    user_db.drop(username, inplace=True)
    db = Spread(sheet_url, client=client)
    db.df_to_sheet(user_db, index=True, sheet='用户信息', start='A1', replace=True)
    st.success(f'用户{username}删除成功！')
    

if __name__ == '__main__':
    db = get_user_db()
    print(db)