# Description: dialog management
import os, logging, json, re
from datetime import datetime
from pathlib import Path
import pandas as pd
from . import model, utils, google_sheet
import streamlit as st
from gspread import Worksheet, Spreadsheet
from gspread_pandas import Spread
from streamlit.runtime.uploaded_file_manager import UploadedFile
from functools import lru_cache

# 管理对话历史，存储在云端Google Drive里面
# 文件夹：·CHAT_FOLDER·
CHAT_FOLDER = 'chatbot'
# 里面每个spreadsheet对应每个用户，表格名称和用户名相同
# 每个表格里面有一个history sheet， header为[time, title, sheet]
HISTORY_SHEET_NAME = 'history'
HISTORY_HEADER = ['time', 'title', 'sheet']
# 其余sheet为dialog，名称对应history的sheet
DIALOG_HEADER = ['role', 'name', 'content', 'time', 'task', 'suggestions', 'actions', 'medias', 'status']
# Objects 对应关系
# | dataclass   |   local var | cloud       | comment  |
# |     -       |       -     | spreadsheet | 用户文件  |
# | history     |   history   | sheet       | 对话记录  |
# |[AppMessage] |conversation | dialog      | 对话      |
# | AppMessage  |   message   | row         | 消息      |

client = google_sheet.init_client()

# init prompt
system_prompt = [
    {"role": "system", "content": f"你是星尘小助手，Your name is Stardust AI Bot. 你是由星尘数据的CEO Derek创造的，你的底层是基于Transformer的技术研发。你会解答各种AI专业问题，如果你不能回答，请让用户访问“stardust.ai”。今天是{datetime.now()}"},
    {"role": "system", "content": "星尘数据（Stardust）成立于2017年5月，公司在北京，是行业领先的数据标注和数据策略公司。星尘数据将专注AI数据技术，通过Autolabeling技术、数据策略专家服务和数据闭环系统服务，为全球人工智能企业特别是自动驾驶行业和大模型应用落地提供“燃料”，最终实现AI的平民化。"},
]

suggestion_prompt = {"role": "system", "content": f'请在你的回答的最后面给出3个启发性问题，让用户可以通过问题进一步理解该概念，并确保用户能继续追问。格式格式为：{utils.SUGGESTION_TOKEN}: ["启发性问题1", "启发性问题2", "启发性问题3"]。请注意：这个启发性问题列表放在最后，且用一行展示，不要换行。'}
search_prompt = {"role": "system", "content": f'如果用户的问题是常识性的问题，请直接回答，不用调用function检索。今天是{datetime.now()}'}

staff_prompt = lambda user: [{"role": "assistant", "content": f"你好，{user}，请问有什么可以帮助你？"}]
guest_prompt = lambda user: [{"role": "system", "content": f'用户是访客，名字为{user}，请用非常精简的方式回答问题。'},
                             {'role': 'assistant', 'content': f'欢迎您，{user}！'}]
TIME_FORMAT = '%Y-%m-%d_%H-%M-%S'


# init dialog for UI
def init_dialog(username):
    # history: 所有对话标题的索引，[time, title, file]
    # conversation: 对话的具体内容列表，[{role, name, time, content, suggestion},...]
    if "conversation" not in st.session_state:
        # 初始化当前对话
        history = get_history(username)
        # 初始化对话列表
        st.session_state.dialog_history = history.col_values(2)[1:]
        if not st.session_state.dialog_history:
            # 没有历史记录或创建新对话，增加“新对话”至title
            dialog_title = new_dialog(username)
            st.session_state.selected_title = dialog_title
            st.rerun()
        elif 'new_title' in st.session_state:
            # 点击新增dialog按钮，通过“new_title”来传递逻辑
            st.session_state.selected_title = st.session_state.new_title
            del st.session_state.new_title
        elif 'chat_title_selection' in st.session_state:
            # select the title according to "chat_title_selection" UI selection
            st.session_state.selected_title = st.session_state.chat_title_selection
        # if current selected title in UI doesn't exist (due to deletion), select a new title
        if 'selected_title' not in st.session_state or st.session_state.selected_title not in st.session_state.dialog_history:
            st.session_state.selected_title = st.session_state.dialog_history[0]
            
        # get对话记录
        messages = get_messages(username, st.session_state.selected_title)
        st.session_state.conversation = messages
    return st.session_state.conversation


## conversation: list[Message] -> chat: dict -> save to file
def append_dialog(username, title, message:model.AppMessage):
    from .controller import openai_image_types
    dialog = get_dialog(username, title)
    # create chat entry as a dict
    message_dict = message.model_dump() 
    message_dict = {k:v for k ,v in message_dict.items() if k in DIALOG_HEADER}
    assert message_dict, f'Empty chat: {message}'
    # convert medias to local file
    if message.medias:
        media_uri_list = [m._file_urls for m in message.medias]
        first_url = media_uri_list[0]
        filename, mime_type = utils.parse_file_info(first_url)
        if len(media_uri_list) == 1 and mime_type.split('/')[-1] in openai_image_types:
            message_dict['medias'] = f'=IMAGE("{first_url}")'
        else:
            message_dict['medias'] = media_uri_list
    message_value = convert_update_value(message_dict)
    res = dialog.append_row(message_value, value_input_option='USER_ENTERED')
    return res

# get messages from a dialog
def get_messages(username, title):
    '''get messages used for UI'''
    dialog_sheet = get_dialog(username, title)
    records = dialog_sheet.get_records(value_render_option='FORMULA')
    # convert to Message object
    messages = []
    for c in records:
        try:
            msg = model.AppMessage(**c)
            messages.append(msg)
        except Exception as e:
            logging.error(f'Error when loading chat: {c} \n Error: {e}')
    return messages


# dialog
def get_dialog(username:str, title:str) -> Worksheet:
    '''Find the dialog file from history
    :param username: the user to search for
    :param title: the title of the dialog
    :returns: the sheet object contains the whole dialog
    '''
    history = get_history(username)
    cell = history.find(title, in_column=2)
    dialog_title = history.cell(cell.row, 3).value
    all_sheets = [s.title for s in history.spreadsheet.worksheets()]
    if dialog_title in all_sheets:
        dialog = history.spreadsheet.worksheet(dialog_title)
    else:
        new_dialog(username, dialog_title)
        dialog = history.spreadsheet.worksheet(dialog_title)
    return dialog


@lru_cache
def get_history(username) -> Worksheet:
    # history_file = CHAT_LOG_ROOT/username/'history.csv'
    record_file = Spread(username, sheet='history', client=client, create_sheet=True, create_spread=True)
    # history = history.sheet_to_df(index=None, formula_columns=['medias'])
    if not record_file.sheet.get_values():
        sh1 = record_file.spread.worksheet('Sheet1')
        record_file.spread.del_worksheet(sh1)
        record_file.sheet.append_row(HISTORY_HEADER)
        record_file.spread.share('leizhang0121@gmail.com', perm_type='user', role='writer')
    return record_file.sheet


def new_dialog(username, dialog_title=None) -> str:
    if not dialog_title:
        dialog_title = datetime.now().strftime(TIME_FORMAT)
    history = get_history(username)
    all_historys = history.col_values(2)[1:]
    if dialog_title in history.col_values(2):
        all_sheets = [s.title for s in history.spreadsheet.worksheets()]
        if dialog_title in all_sheets:
            print(f'dialog title {dialog_title} exists!')
            return dialog_title
    else:
        row = [datetime.now().isoformat(), dialog_title, dialog_title]
        if not all_historys:
            history.append_row(row, value_input_option='USER_ENTERED')
        else:
            history.insert_row(row, index=2, value_input_option='USER_ENTERED')
    # create sheet
    new_dialog = history.spreadsheet.add_worksheet(dialog_title, 1, 1)
    new_dialog.append_row(DIALOG_HEADER)
    # update system prompt
    conversation = system_prompt.copy()
    if st.session_state.guest:
        conversation += guest_prompt(username)
    else:
        conversation += staff_prompt(username)
    # update to sheet
    conversation_df = pd.DataFrame(conversation)
    conversation_df['time'] = datetime.now()
    conversation_df['task'] = None
    conversation_df['name'] = 'system'
    records = conversation_df.to_dict(orient='records')
    message_values = [convert_update_value(r) for r in records]
    new_dialog.append_rows(message_values, value_input_option='USER_ENTERED')
    return dialog_title
    
    
def edit_dialog_name(username, old_title, new_title):
    history = get_history(username)
    cell = history.find(old_title, in_column=2)
    history.update_cell(row=cell.row, col=cell.col, value=new_title)
    
    
def delete_dialog(username, title):
    history = get_history(username)
    cell = history.find(title, in_column=2)
    sheet = history.cell(row=cell.row, col=3).value
    dialog = history.spreadsheet.worksheet(sheet)
    history.spreadsheet.del_worksheet(dialog)
    history.delete_rows(cell.row)


def convert_update_value(record: dict):
    message_value = [(str(record[k]) if k in record and record[k] else None) or None for k in DIALOG_HEADER]
    return message_value

## file attachment, convert to local file when saving
# def allocate_file_path(filename):
#     username = st.session_state.name
#     filepath = CHAT_LOG_ROOT/username/filename
#     while os.path.exists(filepath):
#         filename_idx = filename.split('.')[0].split('_')[-1]
#         try:
#             filename_idx = int(filename_idx)
#             filename_idx += 1
#         except:
#             filename_idx = 1
#         filename = filename.split('.')[0] + f'_{filename_idx}.' + filename.split('.')[1]
#         filepath = CHAT_LOG_ROOT/username/filename
#         logging.info(f'file exists, allocate a new one: {filepath}')
#     return filepath


# def save_files_to_uri_list(file: UploadedFile):
#     filepath = allocate_file_path(file.name)
#     with open(filepath, 'wb') as f:
#         f.write(file.getvalue())
#     return str(filepath)


## -------- assistant session ---------
THREAD_FILE = 'threads.csv'
def get_threads(username):
    threads_history_file = CHAT_LOG_ROOT/username/THREAD_FILE
    if os.path.exists(threads_history_file):
        history = pd.read_csv(threads_history_file, index_col=0)
    else:
        history = pd.DataFrame(columns=['time', 'title', 'thread_id', 'assistant_id'])
    return history


def new_thread(username, thread_id, assistant_id, title=None):
    history = get_threads(username)
    new_dialog = pd.DataFrame([{
        'time': datetime.now(),
        'title': title if title else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'thread_id': thread_id,
        'assistant_id': assistant_id,
    }])
    history = pd.concat([new_dialog, history], ignore_index=True)
    os.makedirs(CHAT_LOG_ROOT/username, exist_ok=True)
    history.to_csv(CHAT_LOG_ROOT/username/THREAD_FILE)
    return title


def delete_thread(username, thread_id):
    history = get_history(username)
    chat = history.query('thread_id==@thread_id')
    history.drop(chat.index.values, inplace=True)
    history.to_csv(CHAT_LOG_ROOT/username/THREAD_FILE)


## ----------- Utils -----------
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

