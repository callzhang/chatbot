from gspread_pandas import Spread, Client
import pandas as pd
import streamlit as st
import os, time
from . import model, utils, google_sheet
from retry import retry
from datetime import datetime, timedelta
from dateutil.parser import parse

## 管理秘钥
import json, toml
@utils.cached()
def get_default_key(task):
    key = st.secrets.get('openai-key')
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
user_table_header = ['访问码', '截止日期', '信息检索', '对话', '语音识别', '文本朗读', '文字做图', 'GPT4', 'GPT4V', 'Assistant']

@utils.cached(timeout=600)
@retry(tries=3, delay=2, backoff=2)
def get_user_db():
    db = Spread(sheet_url, client=client)
    df = db.sheet_to_df()
    df['截止日期'] = df['截止日期'].apply(parse)
    true_value = lambda x: x == 'TRUE' or x is True
    df[user_table_header[2:]] = df[user_table_header[2:]].applymap(true_value)
    print(f'Fetched {len(df)} user records')
    return df


@utils.cached()
@retry(tries=3, delay=2, backoff=2)
def get_admin_db():
    db = Spread(sheet_url, client=client, sheet='admin')
    df = db.sheet_to_df()
    print(f'Fetched {len(df)} admin records')
    return df

def admin_task(username, task):
    db = get_user_db()
    if username in db.index:
        return task in db.loc[username, '权限']
    else:
        return False

def is_admin(username, action=None):
    db = get_admin_db()
    query = f'@username in index'
    if action:
        query += f' and @action==True'
    res = db.query(query)
    return not res.empty
    
    
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
    elif not user_db.query('用户名==@code').empty:
        #登录码=用户名，增加一层防护
        username = "Visitor_"+code
    return username, cookie_exp_date, authenticated


def add_user(username:str, code:str, expiration:datetime):
    user_db = get_user_db()
    if username in user_db.index:
        st.error(f'用户{username}已存在')
        return False
    if not user_db.query(f'访问码==@code').empty:
        st.error(f'访问码【{code}】不安全，请重新输入')
        return False
    user_db.loc[username] = [code, expiration] + [True]*5 + [False]*3
    user_db['截止日期'] = pd.to_datetime(user_db['截止日期'])
    db = Spread(sheet_url, client=client)
    db.df_to_sheet(user_db, index=True, sheet='用户信息', start='A1', replace=True)
    return True

def update_user(username:str, rows):
    user_db = get_user_db()
    if username not in user_db.index:
        st.error(f'用户{username}不存在')
        return False
    # check code duplication
    code = rows[0]
    if not user_db.query(f'index!=@username and 访问码==@code').empty:
        st.error(f'访问码{code}已存在')
        return False
    user_db.loc[username] = rows
    user_db['截止日期'] = pd.to_datetime(user_db['截止日期'])
    db = Spread(sheet_url, client=client)
    db.df_to_sheet(user_db, index=True, sheet='用户信息', start='A1', replace=True)
    return True
    
def delete_user(username:str):
    user_db = get_user_db()
    if username not in user_db.index:
        st.error(f'用户{username}不存在')
        return False
    user_db.drop(username, inplace=True)
    db = Spread(sheet_url, client=client)
    db.df_to_sheet(user_db, index=True, sheet='用户信息', start='A1', replace=True)
    return True

def user_task_list(username:str):
    user_db = get_user_db()
    if username not in user_db.index:
        return {
            '信息检索': True,
            '对话': True,
            '语音识别': True,
            '文本朗读': True,
            '文字做图': False,
            'GPT4': True,
            'GPT4V': False,
            'Assistant': False,
        }
    return user_db.loc[username][2:].to_dict()

if __name__ == '__main__':
    db = get_user_db()
    print(db)