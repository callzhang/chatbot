# https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models

from retry import retry
import requests, json, re, logging
import threading
from collections import deque
import streamlit as st
from . import dialog, utils, model
try:
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
except:
    pass

# 参数
task_params = {
    model.Task.ChatGPT.value: {
        'model': 'gpt-3.5-turbo',
        'url': 'https://api.openai.com/v1/chat/completions',
        'max_tokens': 8000,
    },
    model.Task.GPT4.value: {
        'model': 'gpt-4',
        'url': 'https://yeqiu-gpt4-3.xyhelper.cn/v1/chat/completions',
        'max_tokens': 8000,
    },
    model.Task.GPT4V.value: {
        'model': 'gpt-4v',
        'url': 'http://121.127.44.50:8100/v1/chat/gpt4v',
        'max_tokens': 4000,
    }
}
temperature = 0.7
roles2keep = ['system', 'user', 'assistant']
key2keep = ['role', 'content']
accepted_attachment_types = ['png', 'jpg', 'jpeg']

# function calling
functions = [
    {
        "name": "google_search",
        "description": "Search inormation on Google",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
            },
            "required": ["query"],
        },
    },
]

def chat_len(conversations):
    chat_string = ' '.join(c['content'] for c in conversations if c['content'])
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
def chat_stream(conversations:list, username:str, task:str, attachment=None, guest=True):
    max_length = 500 if guest else 4000
    chat_history = [{k: c.dict()[k] for k in key2keep}
                    for c in conversations if c.role in roles2keep and c.content]
    while chat_len(chat_history) > max_length and len(chat_history) > 1:
        if chat_history[0]['role'] in ['assistant', 'user']:
            st.toast(f"历史数据过长，舍弃: {chat_history[0]['content'][:10]}")
        chat_history.pop(0)
    chat_history.append(dialog.suggestion_prompt)
    print(f"sending conversations rounds: {len(chat_history)}, length:{chat_len(chat_history)}")

    # create a queue to store the responses
    queue = deque()
    
    params = task_params[task]
    url = params['url']

    model = params['model']
    data = {
        'messages': chat_history,
        'stream': True,
        'temperature': temperature,
        'url': url,
        'model': model,
        'file': attachment
    }
    header = {
        'Authorization': f'Bearer {utils.get_openai_key(username, task)}'
    }
    # p = mp.Process(target=get_response, args=(q, header, data))
    thread = threading.Thread(target=get_response, args=(header, data, queue))
    # thread.daemon = True
    thread.start()
    return queue
    

def get_response(header, data, queue):
    url = data.pop('url')
    file = data.pop('file')
    if not file:
        # header['Content-Type'] = 'application/json'
        response = requests.post(url, headers=header, json=data, stream=True, timeout=60)
    else: # gpt4v
        data2 = {'stream': True}
        message = ''
        for k in range(len(data['messages'])-1, 0, -1):
            if data['messages'][k]['role'] == model.Role.user.name:
                message = data['messages'][k]['content']
                break
        data2['message'] = message
        fobject = {'file': (file.name, file)}
        # header['Content-Type'] = 'multipart/form-data' # The issue is that the Content-Type header in your request is missing the boundary parameter, which is crucial for the server to parse the multipart form data correctly. The requests library in Python should add this parameter automatically when you pass data through the files parameter. It seems like the Content-Type header is being set manually somewhere which is overriding the automatically set header by requests. Make sure that you are not setting the Content-Type header manually anywhere in your code or in any middleware that might be modifying the request.
        response = requests.post(url, headers=header, data=data2, files=fobject, stream=data2['stream'], timeout=300)
    if response.ok:
        for line in response.iter_lines():
            if not line:
                continue
            if line == model.FINISH_TOKEN.encode():
                queue.append(model.FINISH_TOKEN)
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
        estring = f'出错啦，请重试: {response.status_code}, {response.text}'
        logging.error(json.dumps(data, indent=2, ensure_ascii=False))
        queue.append({model.SERVER_ERROR: estring})
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

if __name__ == '__main__':
    # WIP: test gpt4v
    messages = '请识别图中所有物体，并理解它们的关系。'
    with open('temp/CF49A632-6E10-4AA3-944F-F4FDA54AF003.png', 'rb') as f:
        attachment = f.read()
    chat_stream(messages, username='test', task='GPT4V', attachment=attachment)
