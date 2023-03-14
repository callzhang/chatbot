from retry import retry
import requests, json, re
import streamlit as st
import threading

# 参数
url = 'https://api.openai.com/v1/chat/completions'
model = 'gpt-3.5-turbo'
temperature = 0.7
finish_token = 'data: [DONE]'
roles2keep = ['user', 'assistant', 'imagen']
keys_keep = ['role', 'content']

def chat_len(conversations):
    chat_string = ' '.join(c['content'] for c in conversations)
    return len(chat_string)

# OpenAI请求(同步)
@retry(tries=3, delay=1)
def chat(conversations):
    # 过滤
    chat_history = [{k:c[k] for k in keys_keep} for c in conversations if c['role'] in roles2keep]
    while chat_len(chat_history) > 2000:
        chat_history.pop(0)
    data = {
        'model': model,
        'messages': chat_history,
        # 'temperature': temperature,
    }
    header = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {st.secrets.key}'
    }
    res = requests.post(url, headers=header, json=data)
    choices = res.json()['choices']
    message = choices[0]['message']
    return message


# receiving streaming server-sent events（异步）
def chat_stream(conversations: list):
    chat_history = [{k:c[k] for k in keys_keep} for c in conversations if c['role'] not in 'audio']
    while chat_len(chat_history) > 2000:
        chat_history.pop(0)
    print(f'sending conversations rounds: {len(chat_history)}, length:{chat_len(chat_history)}')
    # q = mp.Queue()
    queue = []
    lock = threading.Lock()
    data = {
        'model': model,
        'messages': chat_history,
        'stream': True,
        # 'temperature': temperature,
    }
    header = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {st.secrets.key}'
    }
    # p = mp.Process(target=get_response, args=(q, header, data))
    t = threading.Thread(target=get_response, args=(header, data, queue, lock))
    t.start()
    return queue, lock, t
    

def get_response(header, data, queue, lock):
    response = requests.post(url, headers=header, json=data, stream=True, timeout=60)
    if response.ok:
        for line in response.iter_lines():
            if not line:
                continue
            if line == finish_token.encode():
                # q.put(finish_token)
                with lock:
                    queue.append(finish_token)
                print('\n'+'-'*60)
                return
            try:
                # Server-sent events are separated by double newline characters
                key, value = line.decode().split(':', 1)
                value = json.loads(value.strip())
                if key == 'data':
                    content = value['choices'][0]['delta'].get('content')
                    if content:
                        # q.put(content)
                        with lock:
                            queue.append(content)
                        print(content, end='')
                else:
                    raise Exception(line.decode())
            except Exception as e:
                print(e)
    else:
        estring = f'出错啦，请重试: {response.status_code}, {response.reason}'
        print(estring)
        # q.put(estring)
        # q.put(finish_token)
        with lock:
            queue.append(estring)
            queue.append(finish_token)
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


