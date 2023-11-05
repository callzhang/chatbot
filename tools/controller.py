import streamlit as st
from tools import model, utils
from datetime import datetime
from . import dialog, openai, bing, imagegen, asr
import logging
import re, ast

Task = model.Task
Role = model.Role
Message = model.AppMessage

gpt_media_types = openai.accepted_attachment_types
asr_media_types = asr.accepted_types


# 对输入进行应答
def gen_response(query=None):
    # remove suggestion
    if 'suggestions' in st.session_state.conversation[-1]:
        st.session_state.conversation[-1].pop('suggestions')
    if 'action' in st.session_state.conversation[-1]:
        st.session_state.conversation[-1].pop('action')
        
    # get task and input
    task = st.session_state.task
    if task in Task.values():
        user_input = query or st.session_state.input_text
        user_input = user_input.strip() or st.session_state.get('attachment').name
        if not user_input:
            return
    else:
        raise NotImplementedError(task)

    # gen user query
    print(f'{st.session_state.name}({task}): {user_input}')
    attachment = st.session_state.get('attachment')
    query_message = Message(
        role = "user",
        name = st.session_state.name, 
        content = user_input, 
        task = task, 
        time = datetime.now(),
        medias = [attachment] if attachment is not None and not isinstance(attachment, list) else None
    )
    # display and update db
    st.session_state.conversation.append(query_message)
    dialog.update_conversation(st.session_state.name, st.session_state.selected_title, query_message)

    # response
    if task in [Task.ChatGPT.value, Task.GPT4.value, Task.GPT4V.value]:
        queue = openai.chat_stream(conversations=st.session_state.conversation, 
                                    username=st.session_state.name, 
                                    task=task, 
                                    guest=st.session_state.guest)
        bot_response = Message(
            role= Role.assistant.name,
            content = '', 
            queue = queue,
            time = datetime.now(),
            task = task,
            name = task,
        )
        st.session_state.conversation.append(bot_response)
    elif task == Task.BingAI.value:
        if 'bing' not in st.session_state:
            logging.warning('Initiating BingAI, please wait...')
            # show loading
            st.session_state.bing = bing.BingAI(name=st.session_state.name)
        queue, thread = st.session_state.bing.chat_stream(user_input)
        bot_response = Message(
            role= Role.assistant.name,
            content = '', 
            queue = queue, 
            thread = thread,
            time = datetime.now(),
            name = task
        )
        st.session_state.conversation.append(bot_response)
    elif task == Task.text2img.value:
        with st.spinner('正在绘制'):
            urls = imagegen.gen_image(user_input)
            bot_response = Message(
                role= Role.assistant.name,
                content = None ,
                task = task,
                name = 'DALL·E',
                time = datetime.now(),
                medias = urls
            )
            st.session_state.conversation.append(bot_response)
            finish_reply(bot_response)
    elif task == Task.ASR.value:
        with st.spinner('正在识别'):
            assert attachment.type in asr_media_types
            transcription = asr.transcript(attachment)
            bot_response = Message(
                role= Role.assistant.name,
                content = transcription,
                task = task,
                name = 'Whisper',
                time = datetime.now()
            )
            st.session_state.conversation.append(bot_response)
            finish_reply(bot_response)
    else:
        raise NotImplementedError(task)


def handle_action(action_token):
    if action_token == model.RETRY_TOKEN:
        bot_response = st.session_state.conversation.pop(-1)
        user_prompt = st.session_state.conversation.pop(-1)
        if bot_response.role == Role.assistant.name and user_prompt.role == Role.user.name:
            user_input = user_prompt.content
            gen_response(query=user_input)
    else:
        raise NotImplementedError(action_token)
    
    

def finish_reply(message):
    message.queue = None
    if message.thread: # terminate streaming thread
        message.thread.join()
        message.thread = None
    else:
        logging.info(f'{message.name}: {message.content}')
    dialog.update_conversation(st.session_state.name, st.session_state.selected_title, message)
    print('-'*50)
    
    
    
## 处理提示
def parse_suggestions(content:str):
    reply = content
    suggestions = []
    if model.SUGGESTION_TOKEN in content:
        pattern1 = r'(\[SUGGESTION\]:\s?)(\[.+\])'
        pattern2 = r'(\[SUGGESTION\]:\s?)(.{3,})'
        pattern3 = r'\[SUGGESTION\]|启发性问题:\s*'
        pattern31 = r'(-\s|\d\.\s)(.+)'
        matches1 = re.findall(pattern1, reply)
        matches2 = re.findall(pattern2, reply)
        matches3 = re.findall(pattern3, reply)
        
        if matches1:
            for m in matches1:
                reply = reply.replace(''.join(m), '')
                try:
                    suggestions += ast.literal_eval(m[1])
                except:
                    print('==>Error parsing suggestion:<===\n', content)
        elif len(matches2)>=3:
            for m in matches2:
                reply = reply.replace(''.join(m), '')
                suggestions.append(m[1].strip())
        elif matches3:
            # assume only one match
            replies = content.split(matches3[0])
            reply = replies[0]
            for r in replies[1:]:
                match31 = re.findall(pattern31, r)
                suggestions += [m[1].strip() for m in match31]
                for m in match31:
                    r = r.replace(''.join(m), '')
                reply += r

    return reply, suggestions

def filter_suggestion(content:str):
    pattern = r'\[?SUGGESTION\].*$'
    content = '\n'.join(re.split(pattern, content, re.MULTILINE))
    return content




