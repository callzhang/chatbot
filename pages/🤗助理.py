from openai import OpenAI
import streamlit as st
from functools import lru_cache
from tools import utils, dialog
from datetime import datetime

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=st.secrets["openai-key"],
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

if user_input := st.chat_input('请输入问题'):
    with st.chat_message('human'):
        st.write(user_input)
    with st.spinner('Thinking...'):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            stream=True,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input},
            ]
        )
        with st.chat_message('ai'):
            # st.write(response.choices[0].message.content)
            tpl = st.empty()
            collected_messages = ''
            for chunk in response:
                chunk_message = chunk.choices[0].delta.content  # extract the message
                if chunk_message:
                    print(chunk_message, end='')
                    collected_messages += chunk_message  # save the message
                    tpl.write(collected_messages)

        # st.session_state.conversation.append(dialog.Message(
        #     role = dialog.Role.ai.name,
        #     name = 'ai', 
        #     content = response.choices[0].text, 
        #     task = dialog.Task.ChatGPT.name, 
        #     time = datetime.now(),
        # ))
        # dialog.update_conversation(st.session_state.name, st.session_state.selected_title, st.session_state.conversation[-1])