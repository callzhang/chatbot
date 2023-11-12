from openai import OpenAI
import streamlit as st
from functools import lru_cache
from tools import utils, dialog

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key="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",
)

# assistant = client.beta.assistants.create(
#     name="Math Tutor",
#     instructions="You are a personal math tutor. Write and run code to answer math questions.",
#     tools=[{"type": "code_interpreter"}],
#     model="gpt-4-1106-preview"
# )

if 'current_assistant' not in st.session_state:
    st.session_state.current_assistant = None

@utils.cached(timeout=600)
def get_assistant_list():
    assistants = client.beta.assistants.list()
    assistants = [a for a in assistants]
    return assistants

with st.sidebar:
    # assistant
    with st.spinner('Loading assistants...'):
        assistants = get_assistant_list()
        if not st.session_state.current_assistant and assistants:
            st.session_state.current_assistant = assistants[0]
    assistant_names = [a.name for a in assistants]
    if idx := st.selectbox('选择助理', options=assistant_names, index=0, key='assistant'):
        st.session_state.current_assistant = assistants[assistant_names.index(idx)]
    st.button('➕创建助理')
            
    # refresh assistant list
    if st.button('↻'):
        get_assistant_list.clear_cache()
        st.rerun()


st.title(st.session_state.current_assistant.name)
st.caption(st.session_state.current_assistant.instructions)

with st.chat_message('ai'):
    st.write('你好，我是你的助理，有什么可以帮忙的？')

st.chat_input('请输入问题')