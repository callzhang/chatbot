import pandas as pd
import streamlit as st
import datetime, os, re, logging, ast
from functools import cache
from collections import defaultdict
from pathlib import Path

WIDE_LAYOUT_THRESHOLD = 400
SUGGESTION_TOKEN = '[SUGGESTION]'
FINISH_TOKEN = 'data: [DONE]'
RETRY_TOKEN = '[RETRY]'
TIMEOUT = 30
CHAT_LOG_ROOT = Path('chats')

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



# 导出对话内容到 markdown
def conversation2markdown(conversation, name):
    history = pd.DataFrame(conversation).query('role not in ["system", "audio"]')
    # export markdown
    md_formated = f"""# {name}的对话记录
## 日期：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n
---
"""
    for i, c in history.iterrows():
        role, content, task, model = c['role'], c['content'], c.get('task'), c.get('model')
        if role == "user":
            md_formated += f"""**{name}({task}): {content}**\n\n"""
        elif role in ["assistant"]:
            md_formated += f"""星尘小助手({model}): {content}\n\n"""
        elif role == "DALL·E":
            md_formated += f"""星尘小助手({model}): {content}\n\n"""
        else:
            pass
    # with open('export.md', 'w') as f:
    #     f.write(md_formated)
    return md_formated.encode('utf-8').decode()


# cached function to get history
# @st.cache_data(ttl=600)  # update every 10 minute
def get_history(name, to_dict=False):
    history_file = CHAT_LOG_ROOT/f'{name}.md'
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            chat_log = f.read()
    else:
        chat_log = ''
        
    # find all occurance of '---' and split the string
    chat_splited = re.split(r'\n\n---*\n\n', chat_log)
    date_patten = r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]" #r"\d{4}-\d{2}-\d{2}"
    query_pattern = f'{name}（(.+)）: (.+)\*\*'
    replay_pattern = r'星尘小助手（(.+)）: (.+)'
    chat_history = defaultdict(list)
    for chat in chat_splited:
        datetime_str = re.findall(date_patten, chat)
        queries = re.findall(query_pattern, chat, flags=re.DOTALL)
        replies = re.findall(replay_pattern, chat, flags=re.DOTALL)
        if not queries or not replies:
            print(f'empty chat: {chat}')
            continue
        if datetime_str:
            t = datetime.datetime.strptime(datetime_str[0][1:-1], '%Y-%m-%d %H:%M:%S')
            date_str = t.strftime('%Y-%m-%d')
        elif chat.strip():
            date_str = '无日期'
        else:
            continue
        
        # convert to v2 data
        if not to_dict:
            chat_history[date_str].append(chat)
        else:
            for task, query in queries:
                chat_history[date_str].append({
                    'role': 'user',
                    'time': t,
                    'name': name,
                    'task': task,
                    'content': query
                })
            for bot, reply in replies:
                content, suggestions = parse_suggestions(reply)
                chat_history[date_str].append({
                    'role': 'assistant',
                    'time': t,
                    'name': bot,
                    'task': task[0],
                    'content': content,
                    'suggestions': suggestions
                })
    return chat_history

## 对话内容的管理
# history: 所有对话标题的索引，[time, title, file]
# conversation: 对话的具体内容列表，[{role, name, time, content, suggestion},...]

def update_chat_log(name, title, chat):
    os.makedirs(CHAT_LOG_ROOT/name, exist_ok=True)
    chat_log_file = CHAT_LOG_ROOT/name/f'{title}.csv'
    if not os.path.exists(chat_log_file):
        # need to update chat history first
        append_chat_history(name, title)
        # create chat log
        chat_log = pd.DataFrame([chat])
    else:
        chat_log = pd.read_csv(chat_log_file)
        chat_log.append(chat, ignore_index=True)
        chat_log
    chat_log.to_csv(chat_log_file)


def get_chat_history(name):
    history_file = CHAT_LOG_ROOT/name/'history.csv'
    if os.path.exists(history_file):
        history = pd.read_csv(history_file)
    else:
        history = pd.DataFrame(columns=['time', 'title', 'file'])
    return history

def append_chat_history(name, title):
    history = get_chat_history(name)
    history.append({
        'time': datetime.datetime.now(),
        'title': title,
        'file': CHAT_LOG_ROOT/name/title
    }, ignore_index=True)
    history.to_csv(CHAT_LOG_ROOT/name/'history.csv')
    

def get_conversation(file_name):
    conversations_df = pd.read_csv(file_name).fillna('')
    conversations_df.suggestions = conversations_df.suggestions.apply(lambda s:eval(s) if s else [])
    conversations = conversations_df.to_dict('records')
    return conversations


def render_markdown(conversations, title=''):
    conversations_md = f'# {title}\n'
    for i, chat in enumerate(conversations):
        if chat['role'] == 'user':
            conversations_md += '---\n'
            conversations_md += f"**[{chat['time']}] {chat['name']}（{chat['task']}）： {chat['content']}**\n\n"
        elif chat['role'] == 'assistant':
            conversations_md += f"星尘小助手（{chat['name']}）： {chat['content']}\n\n"
    return conversations_md


import shutil
def zip_folder(folder_path, output_path):
    filename = shutil.make_archive(output_path, "zip", folder_path)
    return filename

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

# user
sheet_url = st.secrets["public_gsheets_url"]
from shillelagh.backends.apsw.db import connect

@cache
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