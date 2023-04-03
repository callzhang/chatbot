import pandas as pd
import streamlit as st
import datetime, os

WIDE_LAYOUT_THRESHOLD = 400
SUGGESTION_TOKEN = '[SUGGESTION]'
FINISH_TOKEN = 'data: [DONE]'
RETRY_TOKEN = '[RETRY]'
TIMEOUT = 30

# create folder
if not os.path.exists('chats'):
    os.makedirs('chats')

# init prompt
init_prompt = [
    {"role": "system", "content": "你是星尘小助手，Your name is Stardust AI Bot. 你是由星尘数据的CEO Derek创造的，你的底层是基于Transformer的技术研发。你会解答各种AI专业问题，请回答精简一些。如果你不能回答，请让用户访问“stardust.ai”"},
    {"role": "system", "content": "星尘数据（Stardust）成立于2017年5月，公司在北京，是行业领先的数据标注和数据策略公司。星尘数据将专注AI数据技术，通过Autolabeling技术、数据策略专家服务和数据闭环系统服务，为全球人工智能企业特别是自动驾驶行业提供“燃料”，最终实现AI的平民化。"},
]

suggestion_prompt = {"role": "system", "content": f'请在你的回答后面给出3个启发性问题，让用户可以通过问题进一步理解该概念，并确保用户能继续追问。启发性问题格式为：{SUGGESTION_TOKEN}: ["问题1", "问题2", "问题3"]'}

staff_prompt = lambda name: [{"role": "assistant", "content": f"你好，{name}，请问有什么可以帮助你？"}]
guest_prompt = lambda name: [{"role": "system", "content": f'用户是访客，名字为{name}，请用非常精简的方式回答问题。'},
                             {'role': 'assistant', 'content': '欢迎您，访客！'}]



# 导出对话内容
def convert_history(conversation):
    history = pd.DataFrame(conversation).query('role not in ["system", "audio"]')
    # export markdown
    md_formated = f"""# {st.session_state.name}的对话记录
## 日期：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n
---
"""
    for i, c in history.iterrows():
        role, content, task, model = c['role'], c['content'], c.get('task'), c.get('model')
        if role == "user":
            md_formated += f"""**{st.session_state.name}({task}): {content}**\n\n"""
        elif role in ["assistant"]:
            md_formated += f"""星尘小助手({model}): {content}\n\n"""
        elif role == "DALL·E":
            md_formated += f"""星尘小助手({model}): {content}\n\n"""
        else:
            pass
    # with open('export.md', 'w') as f:
    #     f.write(md_formated)
    return md_formated.encode('utf-8').decode()


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


## 管理秘钥
import json
@st.cache(ttl=600)
def get_openai_key():
    if not st.session_state.get('name'):
        return st.secrets.key
    openai_key_file = f'secrets/{st.session_state.name}/openai_key.json'
    if not os.path.exists(openai_key_file):
        return st.secrets.key
    key = json.load(open(openai_key_file, 'r'))['openai_key']
    return key

@st.cache(ttl=600)
def get_bingai_key():
    if not st.session_state.get('name'):
        return None
    bing_key_file = f'secrets/{st.session_state.name}/bing_key.json'
    if not os.path.exists(bing_key_file):
        return None
    print(f'bing_key_file: {bing_key_file}')
    return bing_key_file
