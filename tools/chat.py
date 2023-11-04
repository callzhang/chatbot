import os, re, ast
from datetime import datetime
from pathlib import Path
import pandas as pd
from . import utils

CHAT_LOG_ROOT = Path('chats')
# create folder
if not os.path.exists(CHAT_LOG_ROOT):
    os.makedirs(CHAT_LOG_ROOT)

# init prompt
system_prompt = [
    {"role": "system", "content": "你是星尘小助手，Your name is Stardust AI Bot. 你是由星尘数据的CEO Derek创造的，你的底层是基于Transformer的技术研发。你会解答各种AI专业问题，请回答精简一些。如果你不能回答，请让用户访问“stardust.ai”。"},
    {"role": "system", "content": "星尘数据（Stardust）成立于2017年5月，公司在北京，是行业领先的数据标注和数据策略公司。星尘数据将专注AI数据技术，通过Autolabeling技术、数据策略专家服务和数据闭环系统服务，为全球人工智能企业特别是自动驾驶行业和大模型应用落地提供“燃料”，最终实现AI的平民化。"},
]

suggestion_prompt = {"role": "system", "content": f'请在你的回答的最后面给出3个启发性问题，让用户可以通过问题进一步理解该概念，并确保用户能继续追问。格式格式为：{utils.SUGGESTION_TOKEN}: ["启发性问题1", "启发性问题2", "启发性问题3"]。请注意：这个启发性问题列表放在最后，且用一行展示，不要换行。'}

staff_prompt = lambda name: [{"role": "assistant", "content": f"你好，{name}，请问有什么可以帮助你？"}]
guest_prompt = lambda name: [{"role": "system", "content": f'用户是访客，名字为{name}，请用非常精简的方式回答问题。'},
                             {'role': 'assistant', 'content': f'欢迎您，{name}！'}]



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
        # chat_log = chat_log.append(chat, ignore_index=True) # deprecated
        chat_log = pd.concat([chat_log, pd.DataFrame([chat])], ignore_index=True)
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
        return chat_file
    else:
        # 如果没有找到，则返回第一条结果?
        # chat_file = history.iloc[0]['file']
        raise Exception('No dialog found! Check your code!')

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
        title = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    history = get_dialog_history(name)
    new_dialog = pd.DataFrame([{
        'time': datetime.now(),
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

