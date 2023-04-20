import pandas as pd
import streamlit as st
import datetime, os, re, logging, ast
from functools import cache
from pathlib import Path
from retry import retry

WIDE_LAYOUT_THRESHOLD = 1000
SUGGESTION_TOKEN = '[SUGGESTION]'
FINISH_TOKEN = 'data: [DONE]'
RETRY_TOKEN = '[RETRY]'
TIMEOUT = 30
CHAT_LOG_ROOT = Path('chats')
LOGIN_CODE = 'login_code'

# create folder
if not os.path.exists(CHAT_LOG_ROOT):
    os.makedirs(CHAT_LOG_ROOT)

# init prompt
system_prompt = [
    {"role": "system", "content": "你是星尘小助手，Your name is Stardust AI Bot. 你是由星尘数据的CEO Derek创造的，你的底层是基于Transformer的技术研发。你会解答各种AI专业问题，请回答精简一些。如果你不能回答，请让用户访问“stardust.ai”。"},
    {"role": "system", "content": "星尘数据（Stardust）成立于2017年5月，公司在北京，是行业领先的数据标注和数据策略公司。星尘数据将专注AI数据技术，通过Autolabeling技术、数据策略专家服务和数据闭环系统服务，为全球人工智能企业特别是自动驾驶行业提供“燃料”，最终实现AI的平民化。"},
]

suggestion_prompt = {"role": "system", "content": f'请在你的回答的最后面给出3个启发性问题，让用户可以通过问题进一步理解该概念，并确保用户能继续追问。启发性问题格式为：{SUGGESTION_TOKEN}: ["问题1", "问题2", "问题3"]'}

staff_prompt = lambda name: [{"role": "assistant", "content": f"你好，{name}，请问有什么可以帮助你？"}]
guest_prompt = lambda name: [{"role": "system", "content": f'用户是访客，名字为{name}，请用非常精简的方式回答问题。'},
                             {'role': 'assistant', 'content': '欢迎您，访客！'}]


## 对话内容的管理
# dialog history: 所有对话标题的索引，[time, title, file]
# conversation: 对话的具体内容，由多个chat组成，[chat,...]
# chat: 对话中的一条信息：{role, name, time, content, suggestion}

def update_conversation(name, title, chat):
    dialog_file = get_dialog_file(name, title)
    if not os.path.exists(dialog_file):
        # create chat log
        chat_log = pd.DataFrame([chat])
        chat_log.to_csv(dialog_file)
    else:
        chat_log = pd.read_csv(dialog_file, index_col=0)
        chat_log = chat_log.append(chat, ignore_index=True)
    chat_log.to_csv(dialog_file)
    
def get_conversation(name, title):
    file_name = get_dialog_file(name, title)
    if not os.path.exists(file_name):
        return []
    conversations_df = pd.read_csv(file_name, index_col=0).fillna('')
    if 'suggestions' in conversations_df:
        conversations_df.suggestions = conversations_df.suggestions.apply(lambda s:eval(s) if s else [])
    conversations = conversations_df.to_dict('records')
    return conversations
    
def get_dialog_file(name, title):
    history = get_dialog_history(name)
    dialog = history.query('title==@title')
    if len(dialog):
        chat_file = dialog.iloc[0]['file']
    else:
        chat_file = history.iloc[0]['file']
    return chat_file

# dialog
def get_dialog_history(name):
    history_file = CHAT_LOG_ROOT/name/'history.csv'
    if os.path.exists(history_file):
        history = pd.read_csv(history_file, index_col=0)
    else:
        history = pd.DataFrame(columns=['time', 'title', 'file'])
    return history

def new_dialog(name, title=None):
    if not title:
        title = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    history = get_dialog_history(name)
    new_dialog = pd.DataFrame([{
        'time': datetime.datetime.now(),
        'title': title,
        'file': CHAT_LOG_ROOT/name/f'{title}.csv'
    }])
    history = pd.concat([new_dialog, history], ignore_index=True)
    os.makedirs(CHAT_LOG_ROOT/name, exist_ok=True)
    history.to_csv(CHAT_LOG_ROOT/name/'history.csv')
    return title
    
def edit_dialog_name(name, old_title, new_title):
    history = get_dialog_history(name)
    chat = history.query('title==@old_title')
    history.loc[chat.index, 'title'] = new_title
    history.to_csv(CHAT_LOG_ROOT/name/'history.csv')
    
def delete_dialog(name, title):
    history = get_dialog_history(name)
    chat = history.query('title==@title')
    history.drop(chat.index.values, inplace=True)
    history.to_csv(CHAT_LOG_ROOT/name/'history.csv')




## Markdown
# 导出对话内容到 markdown
def conversation2markdown(conversation, title=""):
    history = pd.DataFrame(conversation).query('role not in ["system", "audio"]')
    # export markdown
    md_formated = f"""# 关于“{title}”的对话记录
*导出日期：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n
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
@cache
def default_key():
    with open('.streamlit/secrets.toml', 'r') as f:
        data = toml.load(f)
    return data['key']

@cache
def get_openai_key(username):
    openai_key_file = f'secrets/{username}/openai_key.json'
    if not username or not os.path.exists(openai_key_file):
        return default_key()
    key = json.load(open(openai_key_file, 'r'))['openai_key']
    return key

@cache
def get_bingai_key(username):
    bing_key_file = f'secrets/{username}/bing_key.json'
    if not username or not os.path.exists(bing_key_file):
        return None
    print(f'bing_key_file: {bing_key_file}')
    return bing_key_file

## user auth
sheet_url = st.secrets["public_gsheets_url"]
from shillelagh.backends.apsw.db import connect


@st.cache_data(ttl=600)
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