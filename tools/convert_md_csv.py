import os, pandas as pd, sys, re, datetime
from pathlib import Path
from . import utils
from collections import defaultdict

def convert_md_csv():
    chat_folder = Path('chats')
    files = chat_folder.glob('*.md')
    for md in files:
        fn = os.path.basename(md)
        name = fn.split('.')[0]
        histories = utils.get_history(name, to_dict=True)
        if not histories:
            print(f'Not history found for [{fn}]')
            continue
        target_folder = chat_folder/name
        conversations = []
        os.makedirs(target_folder, exist_ok=True)
        for date_str, chats in histories.items():
            csv_file = target_folder/f'{date_str}.csv'
            df = pd.DataFrame(chats)
            # df.sort_values(by='time', inplace=True)
            df.to_csv(csv_file)
            conversations.append({
                'time': df.time.min(),
                'title': date_str,
                'file': csv_file
            })
        chat_history = pd.DataFrame(conversations).sort_values('title', ascending=False)
        chat_history.to_csv(target_folder/'history.csv')
        print(f'Chat converted: {md}')

# cached function to get history
# @st.cache_data(ttl=600)  # update every 10 minute
def get_history(name, to_dict=False):
    history_file = utils.CHAT_LOG_ROOT/f'{name}.md'
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
                content, suggestions = utils.parse_suggestions(reply)
                chat_history[date_str].append({
                    'role': 'assistant',
                    'time': t,
                    'name': bot,
                    'task': task[0],
                    'content': content,
                    'suggestions': suggestions
                })
    return chat_history