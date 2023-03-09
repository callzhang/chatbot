from retry import retry
import requests, json, re
import streamlit as st
import multiprocess as mp 

# 参数
url = 'https://api.openai.com/v1/chat/completions'
model = 'gpt-3.5-turbo'
temperature = 0.7
finish_token = 'data: [DONE]'

# init prompt
init_prompt = [
    {"role": "system", "content": "你是星尘小助手，Your name is Stardust AI Bot. 你是由星尘数据的CEO Derek创造的，你的底层是基于Transformer的技术研发。你会解答各种AI专业问题，也可以根据指令绘制图像，或者识别语音。如果你不能回答，请访问“stardust.ai”"},
    {"role": "system", "content": "星尘数据（Stardust）成立于2017年5月，是行业领先的数据标注和数据策略公司。星尘数据将专注AI数据技术，通过Autolabeling技术、数据策略专家服务和数据闭环系统服务，为全球人工智能企业特别是自动驾驶行业提供“燃料”，最终实现AI的平民化。"},
    {"role": "assistant", "content": f"你好，请问有什么问题我可以解答？"},
]

keys_keep = ['role', 'content']

def chat_len(conversations):
    chat_string = ' '.join(c['content'] for c in conversations)
    return len(chat_string)

# OpenAI请求(同步)
@retry(tries=3, delay=1)
def chat(conversations):
    # 过滤
    chat_history = [{k:c[k] for k in keys_keep} for c in conversations if c['role'] not in 'audio']
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
    q = mp.Queue()
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
    p = mp.Process(target=get_response, args=(q, header, data))
    p.start()
    return q
    

def get_response(q, header, data):
    response = requests.post(url, headers=header, json=data, stream=True, timeout=60)
    if response.ok:
        for line in response.iter_lines():
            if not line:
                continue
            if line == finish_token.encode():
                q.put(finish_token)
                print('\n'+'-'*60)
                return
            try:
                # Server-sent events are separated by double newline characters
                key, value = line.decode().split(':', 1)
                value = json.loads(value.strip())
                if key == 'data':
                    content = value['choices'][0]['delta'].get('content')
                    if content:
                        q.put(content)
                        print(content, end='')
                else:
                    raise Exception(line.decode())
            except Exception as e:
                print(e)
    else:
        estring = f'出错啦，请重试: {response.status_code}, {response.reason}'
        print(estring)
        q.put(estring)
        q.put(finish_token)
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
    prompt = init_prompt.append({
        'role': 'user',
        'content': '请写一首关于星尘的诗'
    })
    chat_stream(init_prompt)