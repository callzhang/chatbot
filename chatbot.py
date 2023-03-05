import streamlit as st
from streamlit_chat import message
import requests, json
from retry import retry

# 设置页面标题
st.set_page_config(page_title="星尘小助手", page_icon="🪐", layout="centered", initial_sidebar_state="collapsed", menu_items={
             'Get Help': 'https://stardust.ai',
            #  'Report a bug': "https://www.extremelycoolapp.com/bug",
             'About': "# 星尘小助手. \n *仅限员工使用，请勿外传!*"
    })
st.title("🪐星尘小助手")

# 参数
url = 'https://api.openai.com/v1/chat/completions'
key = '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'
model = 'gpt-3.5-turbo'
temperature = 0.7

# 名字
with open('names.txt', 'r') as f:
    names = [n.strip() for n in f.readlines()]
name_pl = st.empty()
if 'my_name' not in st.session_state:
    if 'name' in st.session_state and st.session_state.name != '':
        st.session_state.my_name = st.session_state.name
    else:
        st.session_state.name = name_pl.text_input('请输入你的名字', key='my_name')
else:
    st.session_state.name = st.session_state.my_name
if st.session_state.name == '':
    st.stop()
elif st.session_state.name not in names:
    st.warning(f'请输入正确的名字以使用本系统, {names}')
    st.stop()
else:
    name_pl.empty()
    

# 定义一个列表，用于保存对话内容。role：system，user，assistant
if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "system", "content": "你的名字叫‘星尘小助手’，Your name is Stardust AI Bot. You are created by Derek, CEO of Stardust. 你会解答各种AI专业问题。如果你不能回答，请让用户访问“stardust.ai”"},
        {"role": "system", "content": "星尘数据（Stardust）成立于2017年5月，是行业领先的数据标注和数据策略公司。星尘数据将专注AI数据技术，通过Autolabeling技术、数据策略专家服务和数据闭环系统服务，为全球人工智能企业特别是自动驾驶行业提供“燃料”，最终实现AI的平民化。"},
        {"role": "assistant", "content": f"你好，{st.session_state.name}，请问有什么问题我可以解答？"},
    ]

# OpenAI请求
@retry(tries=3, delay=1)
def get_chatgpt_response():
    conversation = st.session_state.conversation.copy()
    while len(json.dumps(conversation)) > 4000:
        conversation.pop(0)
    # print(f'conversation length: {len(json.dumps(conversation))}')
    data = {
        'model': model,
        'messages': conversation,
        # 'temperature': temperature,
    }
    header = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    }
    res = requests.post(url, headers=header, json=data)
    choices = res.json()['choices']
    message = choices[0]['message']
    return message

# 显示对话内容
md_formated = ""
for i, c in enumerate(st.session_state.conversation):
    if c['role'] == "system":
        pass
    elif c['role'] == "user":
        # md_formated += f"\n你：{c['content']}"
        message(c['content'], is_user=True, key=str(i),
                avatar_style='initials', seed=st.session_state.name[-2:])
    elif c['role'] == "assistant":
        # md_formated += f"\n星尘小助手：{c['content']}"
        message(c['content'], key=str(i), avatar_style='jdenticon')
    else:
        raise Exception(c)


# 刷新对话内容
def gen_response():
    user_input = st.session_state.input_text
    print(f'{st.session_state.name}: {user_input}')
    st.session_state.input_text = ""
    st.session_state.conversation.append({"role": "user", "content": user_input})
    with st.spinner('正在思考'):
        bot_response = get_chatgpt_response()
        print(f'星尘小助手: {bot_response["content"]}')
    with open(f'chats/{st.session_state.name}.txt', 'a') as f:
        f.write(f'{st.session_state.name}: {user_input}\n')
        f.write(f'星尘小助手: {bot_response["content"]}\n')
    st.session_state.conversation.append(bot_response)


# 添加文本输入框和提交按钮
user_input = st.text_input("输入你的问题：", 
                           help='输入你的问题，然后按回车提交。', 
                           max_chars=500,
                           key='input_text',
                           on_change=gen_response)

# if st.button('开始新的话题'):
#     del st.session_state.conversation