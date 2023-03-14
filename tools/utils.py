import pandas as pd
import streamlit as st
import datetime

# init prompt
init_prompt = [
    {"role": "system", "content": "你是星尘小助手，Your name is Stardust AI Bot. 你是由星尘数据的CEO Derek创造的，你的底层是基于Transformer的技术研发。你会解答各种AI专业问题，请回答精简一些。如果你不能回答，请让用户访问“stardust.ai”"},
    {"role": "system", "content": "星尘数据（Stardust）成立于2017年5月，是行业领先的数据标注和数据策略公司。星尘数据将专注AI数据技术，通过Autolabeling技术、数据策略专家服务和数据闭环系统服务，为全球人工智能企业特别是自动驾驶行业提供“燃料”，最终实现AI的平民化。"},
]

staff_prompt = lambda name: [{"role": "assistant", "content": f"你好，{name}，请问有什么可以帮助你？"}]
guest_prompt = lambda name: [{"role": "system", "content": f'和你对话的是访客，名字为{name}，请用非常精简的方式回答问题。'},
                             {'role': 'assistant', 'content': '欢迎您，访客！'}]



# 导出对话内容
def convert_history(conversation):
    history = pd.DataFrame(conversation).query('role not in ["system", "audio"]')
    # export markdown
    md_formated = f"""# {st.session_state.name}的对话记录
## 日期：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---
"""
    for i, c in history.iterrows():
        role, content = c['role'], c['content']
        if role == "user":
            md_formated += f"""**{st.session_state.name}: {content}**\n\n"""
        elif role in ["assistant"]:
            md_formated += f"""星尘小助手: {content}\n\n"""
        elif role == "imagen":
            md_formated += f"""星尘小助手: {content}\n\n"""
        else:
            pass
    # with open('export.md', 'w') as f:
    #     f.write(md_formated)
    return md_formated