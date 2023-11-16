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


task_params = {
    model.Task.ChatSearch.value: openai.task_params,
    model.Task.ChatGPT.value: openai.task_params,
    model.Task.GPT4.value: openai.task_params,
    model.Task.GPT4V.value: openai.task_params,
    model.Task.text2img.value: imagegen.task_params,
    model.Task.ASR.value: asr.task_params,
    model.Task.BingAI.value: bing.task_params,
}


# 对输入进行应答
def gen_response(query=None):
    task = st.session_state.task
    assert task in Task.values(), NotImplementedError(task)
    # remove suggestion
    if st.session_state.conversation:
        st.session_state.conversation[-1].suggestions = None
        st.session_state.conversation[-1].actions = None
        
    # get task and input
    user_input = query or st.session_state.input_text
    attachment = st.session_state.get('attachment')
    if not user_input and attachment:
        user_input = attachment.name
    if not user_input:
        return
    
    # create user query
    query_message = Message(
        role = model.Role.user.name,
        name = st.session_state.name, 
        content = user_input, 
        task = model.Task(task).name, 
        time = datetime.now(),
        medias = attachment
    )
    # display and update db
    st.session_state.conversation.append(query_message)
    dialog.update_conversation(st.session_state.name, st.session_state.selected_title, query_message)

    # response
    print(f'Start task({task}): {st.session_state.conversation[-1].content}')
    if task in [Task.ChatGPT.value, Task.GPT4.value, Task.GPT4V.value]:
        queue = openai.chat_stream(conversation=st.session_state.conversation, 
                                    task=task,
                                    attachment=attachment,
                                    guest=st.session_state.guest)
        if openai.DEBUG:
            queue.append('controller: queue returned\n\n')
        bot_response = Message(
            role= Role.assistant.name,
            content = '', 
            queue = queue,
            time = datetime.now(),
            task = model.Task(task).name,
            name = task_params[task][task]['model'],
        )
        st.session_state.conversation.append(bot_response)
    elif task == Task.ChatSearch.value:
        logging.info(f'chat search: {user_input}')
        queue = openai.chat_with_search(conversation=st.session_state.conversation, task=task)
        bot_response = Message(
            role= Role.assistant.name,
            content = '', 
            queue = queue,
            time = datetime.now(),
            task = model.Task(task).name,
            name = task_params[task][task]['model'],
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
            name = task_params[task][task]['model'],
        )
        st.session_state.conversation.append(bot_response)
    elif task == Task.text2img.value:
        toast = st.toast('正在绘制', icon='🖌️')
        with st.spinner('正在绘制'):
            urls = imagegen.gen_image(user_input)
            bot_response = Message(
                role= Role.assistant.name,
                content = None ,
                task = model.Task(task),
                name = task_params[task][task]['model'],
                time = datetime.now(),
                medias = urls
            )
            toast.toast('绘制完成，正在下载', icon='🤩')
            st.session_state.conversation.append(bot_response)
        toast.toast('下载完成', icon='😄')
        finish_reply(bot_response)
    elif task == Task.ASR.value:
        with st.spinner('正在识别'):
            transcription = asr.transcript(attachment)
            bot_response = Message(
                role= Role.assistant.name,
                content = transcription,
                task = model.Task(task),
                name = task_params[task][task]['model'],
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
    # if message.thread: # terminate streaming thread
    #     message.thread.join()
    #     message.thread = None
    # else:
    #     logging.info(f'{message.name}: {message.content}')
    dialog.update_conversation(st.session_state.name, st.session_state.selected_title, message)
    print('-'*50)
    

def display_media(media):
    media_type = media.type.split('/')[0]
    if media.type in gpt_media_types or media_type == model.MediaType.image.name:
        media_type == model.MediaType.image
        st.image(media, use_column_width='always')
    elif media.type in asr_media_types or media_type == model.MediaType.audio.name:
        media_type == model.MediaType.audio
        st.audio(media)
    elif media.type == 'mp4' or media_type == model.MediaType.video.name:
        media_type == model.MediaType.video
        st.video(media)
    else:
        raise NotImplementedError(media.tpye)
    return media_type


def call_functions(message):
    functions = message.functions
    queue = message.queue
    
    
## 处理提示
def parse_suggestions(content:str):
    if not content:
        return None, None
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




