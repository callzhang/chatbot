# Description: dialog management

import os, logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from . import model
import streamlit as st

CHAT_LOG_ROOT = Path('chats')
CHAT_SAVE_KEYS = ['role', 'name', 'content', 'time', 'task', 'suggestions', 'actions', 'medias', 'status']
# create folder
if not os.path.exists(CHAT_LOG_ROOT):
    os.makedirs(CHAT_LOG_ROOT)

# init prompt
system_prompt = [
    {"role": "system", "content": "你是星尘小助手，Your name is Stardust AI Bot. 你是由星尘数据的CEO Derek创造的，你的底层是基于Transformer的技术研发。你会解答各种AI专业问题，如果你不能回答，请让用户访问“stardust.ai”。"},
    {"role": "system", "content": "星尘数据（Stardust）成立于2017年5月，公司在北京，是行业领先的数据标注和数据策略公司。星尘数据将专注AI数据技术，通过Autolabeling技术、数据策略专家服务和数据闭环系统服务，为全球人工智能企业特别是自动驾驶行业和大模型应用落地提供“燃料”，最终实现AI的平民化。"},
]

suggestion_prompt = {"role": "system", "content": f'请在你的回答的最后面给出3个启发性问题，让用户可以通过问题进一步理解该概念，并确保用户能继续追问。格式格式为：{model.SUGGESTION_TOKEN}: ["启发性问题1", "启发性问题2", "启发性问题3"]。请注意：这个启发性问题列表放在最后，且用一行展示，不要换行。'}

staff_prompt = lambda user: [{"role": "assistant", "content": f"你好，{user}，请问有什么可以帮助你？"}]
guest_prompt = lambda user: [{"role": "system", "content": f'用户是访客，名字为{user}，请用非常精简的方式回答问题。'},
                             {'role': 'assistant', 'content': f'欢迎您，{user}！'}]



## 对话内容的管理
# dialog history: 所有对话标题的索引，[time, title, file]
# conversation: dialog对话的具体内容，由多个`AppMessage`组成，[AppMessage,...], 注意，chat是用于存储到本地文件的临时对象
# chat: 对话中的一条信息：{role, name, time, content, suggestion, medias}

# init dialog for UI
def init_dialog(username):
    # history: 所有对话标题的索引，[time, title, file]
    # conversation: 对话的具体内容列表，[{role, name, time, content, suggestion},...]
    if "conversation" not in st.session_state:
        # 初始化当前对话
        dialog_history = get_dialog_history(username)
        # 初始化对话列表
        st.session_state.dialog_history = dialog_history['title'].tolist()
        # 没有历史记录或创建新对话，增加“新对话”至title
        if not st.session_state.dialog_history:
            new_dialog(username)
            st.rerun()
        elif 'new_chat' in st.session_state:
            st.session_state.selected_title = st.session_state.new_chat
            del st.session_state.new_chat
        elif 'chat_title_selection' in st.session_state:
            st.session_state.selected_title = st.session_state.chat_title_selection
            if st.session_state.selected_title not in st.session_state.dialog_history:
                st.session_state.selected_title = st.session_state.dialog_history[0]
        else:
            st.session_state.selected_title = st.session_state.dialog_history[0]
            
        # get对话记录
        conversation = get_conversation(username, st.session_state.selected_title)
        if conversation:
            assert isinstance(conversation[0], model.AppMessage)
        st.session_state.conversation = conversation
    return st.session_state.conversation


## conversation: list[Message] -> chat: dict -> save to file
def update_conversation(username, title, message:model.AppMessage):
    dialog_file = get_dialog_file(username, title)
    # create chat entry as a dict
    chat_entry = message.dict()
    chat_entry = {k:v for k ,v in chat_entry.items() if k in CHAT_SAVE_KEYS}
    assert chat_entry, f'Empty chat: {message}'
    # convert medias to local file
    if message.medias:
        media_uri_list = [save_files_to_uri_list(m) for m in message.medias]
        chat_entry['medias'] = media_uri_list
    # convert chat_entry to dataframe
    chat_entry = pd.DataFrame([chat_entry])
    if not os.path.exists(dialog_file):
        # create chat log
        chat_entry.to_csv(dialog_file)
    else:
        chat_log = pd.read_csv(dialog_file, index_col=0)
        # chat_log = chat_log.append(chat, ignore_index=True) # deprecated
        chat_log = pd.concat([chat_log, chat_entry], ignore_index=True)
    chat_log.to_csv(dialog_file)
    
def get_conversation(username, title):
    dialog_filepath = get_dialog_file(username, title)
    if not os.path.exists(dialog_filepath):
        conversation = init_conversation(username, title)
    else:
        conversation_df = pd.read_csv(dialog_filepath, index_col=0, parse_dates=['time']).fillna('')
        conversation_df.dropna(subset=['time'], inplace=True)
        conversation_df.replace('', None, inplace=True)
        conversation = conversation_df.to_dict('records')
    # convert to Message object
    messages = []
    for c in conversation:
        try:
            msg = model.AppMessage(**c)
            messages.append(msg)
        except Exception as e:
            logging.error(f'Error when loading chat: {c} \n Error: {e}')
    return messages


def init_conversation(username, title):
    dialog_filepath = get_dialog_file(username, title)
    assert not os.path.exists(dialog_filepath), f'dialog exists: {dialog_filepath}'
    # update system prompt
    conversation = system_prompt.copy()
    if st.session_state.guest:
        conversation += guest_prompt(username)
    else:
        conversation += staff_prompt(username)
    # save to file
    conversation_df = pd.DataFrame(conversation)
    conversation_df['time'] = datetime.now()
    conversation_df['task'] = None
    conversation_df['name'] = 'system'
    conversation_df.to_csv(dialog_filepath)
    conversation = conversation_df.to_dict('records')
    return conversation


# dialog
def get_dialog_file(username, title):
    history = get_dialog_history(username)
    dialog = history.query('title==@title')
    if len(dialog):
        chat_file = dialog.iloc[0]['file']
        return chat_file
    else:
        raise Exception('No dialog found! Check your code!')
    
    
def get_dialog_history(username):
    history_file = CHAT_LOG_ROOT/username/'history.csv'
    if os.path.exists(history_file):
        history = pd.read_csv(history_file, index_col=0)
    else:
        history = pd.DataFrame(columns=['time', 'title', 'file'])
    return history


def new_dialog(username, dialog_title=None):
    if not dialog_title:
        dialog_title = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    history = get_dialog_history(username)
    new_dialog = pd.DataFrame([{
        'time': datetime.now(),
        'title': dialog_title,
        'file': CHAT_LOG_ROOT/username/f'{dialog_title}.csv'
    }])
    history = pd.concat([new_dialog, history], ignore_index=True)
    os.makedirs(CHAT_LOG_ROOT/username, exist_ok=True)
    history.to_csv(CHAT_LOG_ROOT/username/'history.csv')
    return dialog_title
    
    
def edit_dialog_name(username, old_title, new_title):
    history = get_dialog_history(username)
    chat = history.query('title==@old_title')
    history.loc[chat.index, 'title'] = new_title
    history.to_csv(CHAT_LOG_ROOT/username/'history.csv')
    
    
def delete_dialog(username, title):
    history = get_dialog_history(username)
    chat = history.query('title==@title')
    history.drop(chat.index.values, inplace=True)
    history.to_csv(CHAT_LOG_ROOT/username/'history.csv')


## file attachment, convert to local file when saving
def allocate_file_path(filename):
    username = st.session_state.name
    filepath = CHAT_LOG_ROOT/username/filename
    while os.path.exists(filepath):
        filename_idx = filename.split('.')[0].split('_')[-1]
        try:
            filename_idx = int(filename_idx)
            filename_idx += 1
        except:
            filename_idx = 1
        filename = filename.split('.')[0] + f'_{filename_idx}.' + filename.split('.')[1]
        filepath = CHAT_LOG_ROOT/username/filename
        logging.info(f'file exists, allocate a new one: {filepath}')
    return filepath


from streamlit.runtime.uploaded_file_manager import UploadedFile
def save_files_to_uri_list(file: UploadedFile):
    filepath = allocate_file_path(file.name)
    with open(filepath, 'wb') as f:
        f.write(file.getvalue())
    return str(filepath)


# export
# 导出对话内容到 markdown
def conversation2markdown(messages:list[model.AppMessage], title=""):
    if not messages:
        return ''
    conversation = [m.dict() for m in messages]
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
        elif role == '':
            pass
        else:
            raise Exception(f'Unhandled chat: {c}')
    return md_formated.encode('utf-8').decode()
