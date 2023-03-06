from retry import retry
import requests, json, re
import streamlit as st

# 参数
url = 'https://api.openai.com/v1/chat/completions'
model = 'gpt-3.5-turbo'
temperature = 0.7

# init prompt
init_prompt = [
    {"role": "system", "content": "你的名字叫星尘小助手，Your name is Stardust AI Bot. 你是由星尘数据的CEO Derek创造的。你会解答各种AI专业问题，也可以根据指令绘制图像，或者识别语音。如果你不能回答，请让用户访问“stardust.ai”"},
    {"role": "system", "content": "星尘数据（Stardust）成立于2017年5月，是行业领先的数据标注和数据策略公司。星尘数据将专注AI数据技术，通过Autolabeling技术、数据策略专家服务和数据闭环系统服务，为全球人工智能企业特别是自动驾驶行业提供“燃料”，最终实现AI的平民化。"},
    {"role": "assistant", "content": f"你好，请问有什么问题我可以解答？"},
]


# OpenAI请求
@retry(tries=3, delay=1)
def chat(conversations):
    chat_history = [c for c in conversations if c['role'] not in 'audio']
    while len(json.dumps(chat_history)) > 2000:
        chat_history.pop(0)
    # print(f'conversation length: {len(json.dumps(conversation))}')
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
