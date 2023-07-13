from retry import retry
import requests, json, re, logging
# import streamlit as st
import threading
from collections import deque
from enum import Enum, unique
try:
    from . import utils, chat
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
except:
    pass

# 参数
url = 'https://api.openai.com/v1/chat/completions'
model = 'gpt-3.5-turbo'  # gpt-3.5-turbo-0301
temperature = 0.7
roles2keep = ['system', 'user', 'assistant']
keys_keep = ['role', 'content']

@unique
class Task(Enum): # 还没用
    chat = '对话'
    BingAI = 'BingAI'
    text2img = '文字做图'
    ASR = '语音识别'
    @classmethod
    def names(cls):
        return [c.name for c in cls]
    @classmethod
    def values(cls):
        return [c.value for c in cls]
    
if __name__ == '__main__':
    print(Task.names())
    print(Task.values())

def chat_len(conversations):
    chat_string = ' '.join(c['content'] for c in conversations)
    # count tokens
    try:
        count = len(tokenizer.encode(chat_string))
    except:
        count = len(chat_string)
    return count


# adapter for gradio
def history2chat(history:list[dict]) -> list[list]:
    chatbot = []
    roles = ['user', 'assistant']
    history_ = [c for c in history if c['role'] in roles]
    for i, chat in enumerate(history_):
        if i % 2 == 0:
            chatbot.append([None, None])
        if chat['role'] == roles[0]:
            chatbot[i//2][0] = chat['content']
        elif chat['role'] == roles[1]:
            chatbot[i//2][1] = chat['content']
    return chatbot

# receiving streaming server-sent events（异步）
def chat_stream(conversations:list, username:str, guest=True):
    max_length = 500 if guest else 2000
    chat_history = [{k: c[k] for k in keys_keep}
                    for c in conversations if c['role'] in roles2keep]
    while chat_len(chat_history) > max_length and len(chat_history) > 1:
        chat_history.pop(0)
    chat_history.append(chat.suggestion_prompt)
    print(f'sending conversations rounds: {len(chat_history)}, length:{chat_len(chat_history)}')
    # create a queue to store the responses
    queue = deque()
    data = {
        'model': model,
        'messages': chat_history,
        'stream': True,
        # 'temperature': temperature,
    }
    header = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {utils.get_openai_key(username)}'
    }
    # p = mp.Process(target=get_response, args=(q, header, data))
    thread = threading.Thread(target=get_response, args=(header, data, queue))
    thread.daemon = True
    thread.start()
    return queue
    
    
## OpenAI请求(同步)
# @retry(tries=3, delay=1)
# def chat(conversations):
#     max_length = 500 if st.session_state.guest else 2000
#     # 过滤
#     chat_history = [{k: c[k] for k in keys_keep}
#                     for c in conversations if c['role'] in roles2keep]
#     while chat_len(chat_history) > max_length:
#         chat_history.pop(0)
#     data = {
#         'model': model,
#         'messages': chat_history,
#         # 'temperature': temperature,
#     }
#     header = {
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {utils.get_openai_key()}'
#     }
#     res = requests.post(url, headers=header, json=data)
#     choices = res.json()['choices']
#     message = choices[0]['message']
#     return message


def get_response(header, data, queue):
    response = requests.post(url, headers=header, json=data, stream=True, timeout=60)
    if response.ok:
        for line in response.iter_lines():
            if not line:
                continue
            if line == utils.FINISH_TOKEN.encode():
                queue.append(utils.FINISH_TOKEN)
                print('\n'+'-'*60)
                return
            try:
                key, value = line.decode().split(':', 1)
                value = json.loads(value.strip())
                if key == 'data':
                    content = value['choices'][0]['delta'].get('content')
                    if content:
                        queue.append(content)
                        print(content, end='')
                else:
                    raise Exception(line.decode())
            except Exception as e:
                print(e)
    else:
        estring = f'出错啦，请重试: {response.status_code}, {response.reason}'
        logging.error(json.dumps(data, indent=2))
        queue.append(estring)
        queue.append(utils.FINISH_TOKEN)
        return


def is_markdown(text):
    # all markdown syntax
    patterns = [
        r'\n\d\.\s',  # ordered list
        r'\*\*|__',  # bold
        r'\n-\s',  # unordered list
        r'\n>\s',  # blockquote
        r'\n#+\s',  # header
        r'`(.*?)`',  # inline code
        r'\n`{3}.*?\\n`{3}',  # code block
        r'\n---\n',  # horizontal rule
        r'\!\[(.*?)\]\((.*?)\)',  # image
    ]
    matches = [re.findall(pattern, text) for pattern in patterns]
    is_md = any(matches)
    return is_md


