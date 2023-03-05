import streamlit as st
from streamlit_chat import message
import requests

# 设置页面标题
st.title("🪐星尘小助手")

url = 'https://api.openai.com/v1/chat/completions'
key = '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'
model = 'gpt-3.5-turbo'
temperature = 0.7
with open('names.txt', 'r') as f:
    names = [n.strip() for n in f.readlines()]
my_name = st.text_input('请输入你的名字')
if my_name == '':
    st.stop()
elif my_name not in names:
    st.warning(f'请输入正确的名字以使用本系统, {names}')
    st.stop()
    

# 定义一个列表，用于保存对话内容。role：system，user，assistant
if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "system", "content": "你的名字叫‘星尘小助手’，Your name is Stardust AI Bot. You are created by Derek, CEO of Stardust. 你会解答各种专业问题。如果不能回答，请让user访问“stardust.ai”"},
        {"role": "assistat", "content": f"你好，{my_name}，请问有什么问题我可以解答？"},
        # {"role": "system", "content": "You are created by Derek, CEO of Stardust."},
    ]


def get_chatgpt_response(user_input):
    data = {
        'model': model,
        'messages': st.session_state.conversation[-4:]
    }
    header = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    }
    res = requests.post(url, headers=header, json=data)
    choices = res.json()['choices']
    message = choices[0]['message']
    return message


def gen_response():
    user_input = st.session_state.input_text
    st.session_state.input_text = ""
    st.session_state.conversation.append({"role": "user", "content": user_input})
    with st.spinner('正在思考'):
        bot_response = get_chatgpt_response(user_input)
    st.session_state.conversation.append(bot_response)


# 显示对话内容
md_formated = ""
print(st.session_state.conversation)
for i, c in enumerate(st.session_state.conversation):
    if c['role'] == "system":
        pass
    elif c['role'] == "user":
        # md_formated += f"\n你：{c['content']}"
        message(c['content'], is_user=True, key=str(i),
                avatar_style='initials', seed=my_name[-2:])
    elif c['role'] == "assistant":
        # md_formated += f"\n星尘小助手：{c['content']}"
        message(c['content'], key=str(i), avatar_style='jdenticon')
# st.markdown(md_formated)

# 添加文本输入框和提交按钮
user_input = st.text_input("输入你的问题：", 
                           help='输入你的问题，然后回车提交按钮。', 
                           max_chars=200, 
                           key='input_text',
                           on_change=gen_response)


