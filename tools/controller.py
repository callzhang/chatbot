import streamlit as st
from . import model, utils
from datetime import datetime
from . import dialog, openai, bing, imagegen, speech
import logging
import time, base64
from streamlit.runtime.uploaded_file_manager import UploadedFile, UploadedFileRec

Task = model.Task
Role = model.Role
Message = model.AppMessage

openai_image_types = openai.accepted_image_types
speech_media_types = speech.accepted_types


task_params = {
    model.Task.ChatSearch.value: openai.task_params,
    model.Task.ChatGPT.value: openai.task_params,
    model.Task.GPT4.value: openai.task_params,
    model.Task.GPT4V.value: openai.task_params,
    model.Task.text2img.value: imagegen.task_params,
    model.Task.ASR.value: speech.task_params,
    model.Task.BingAI.value: bing.task_params,
    model.Task.TTS.value: speech.task_params
}

## display assistant message
def show_streaming_message(message: Message, message_placeholder):
    i = st.session_state.conversation.index(message)
    last = i == len(st.session_state.conversation) - 1
    role, content, medias =  message.role, message.content, message.medias
    status_placeholder = message_placeholder.empty()
    text_placeholder = message_placeholder.empty()
    if message.queue is not None:
        status_container = None
        while (queue := message.queue) is not None:  # streaming
            while queue.qsize() > 0:
                item = queue.get()
                message.time = datetime.now()
                if isinstance(item, str):
                    if item == model.FINISH_TOKEN:
                        finish_reply(message)
                        break
                    message.content += item
                elif isinstance(item, dict):  # network error
                    if v := item.get(model.SERVER_ERROR):
                        message.content += f'\n\n{v}'
                        message.actions = {model.RETRY_ACTION: '重试'}
                        finish_reply(message)
                    elif functions := item.get(model.TOOL_RESULT):
                        # message.content += f'```{json.dumps(v, indent=2, ensure_ascii=False)}```'
                        message.functions += functions
                        # finish_reply(message)
                    elif v := item.get(model.STATUS):
                        if not status_container: #init
                            status_container = status_placeholder.status('正在检索', expanded=True)
                        help = item.get(model.HELP)
                        status_container.markdown(v, help=help)
                        message.status.append(item)
                else:
                    raise Exception(f'Unknown content type: {type(content)}')
            # 超时
            if (datetime.now() - message.time).total_seconds() > model.TIMEOUT:
                message.content += '\n\n请求超时，请重试...'
                message.actions = {model.RETRY_ACTION: '重试'}
                finish_reply(message)
                break
            # 渲染
            content_full = message.content.replace(utils.SUGGESTION_TOKEN, '')
            text_placeholder.markdown(content_full + "▌")
            time.sleep(0.1)
        # remove msg and status
        text_placeholder.empty()
        status_placeholder.empty()
    
    # show non-streaming message
    if message.status: # show status
        with status_placeholder.status('正在检索') as status:
            for s in message.status:
                status.markdown(s.get(model.STATUS), help=s.get(model.HELP))
            status.update(label='检索完成', state="complete", expanded=False)

    # media
    content = message.content
    suggestions = message.suggestions
    if medias:
        for media in medias:
            display_media(media, container=message_placeholder)
    # suggestion
    if not suggestions:
        content, suggestions = utils.parse_suggestions(content)
        message.suggestions = suggestions
        message.content = content
    if suggestions and last:
        suggestions = set(suggestions)
        for suggestion in suggestions:
            message_placeholder.button('👉🏻'+utils.truncate_text(suggestion,50), help=suggestion,
                        on_click=gen_response, kwargs={'query': suggestion})
    # text content
    if content:
        text_placeholder.markdown(content)
    # actions: only "retry" is supported
    if (actions := message.actions) and last:
        for action, text in actions.items():
            message_placeholder.button(
                text, on_click=handle_action, args=(action,))
    if last and not message.medias and message.content:
        if message_placeholder.button('🔈', help='朗读'):
            st.toast('▶️正在转译语音')
            data = speech.text_to_speech(message.content)
            rec = UploadedFileRec(
                file_id=message.content[:20],
                name=message.content[:20],
                type='audio/mp3',
                data=data.getvalue(),
            )
            voice = UploadedFile(rec, None)
            message.medias = model.AppMessage.set_medias(voice)
            dialog.update_message(st.session_state.name, st.session_state.selected_title, message, create=False)
            play_audio(voice, message_placeholder, autoplay=True)
        

## 对输入进行应答
def gen_response(query=None):
    task = st.session_state.task
    assert task in Task.values(), NotImplementedError(task)
    # remove suggestion
    if 'conversation' in st.session_state and st.session_state.conversation:
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
    dialog.update_message(st.session_state.name, st.session_state.selected_title, query_message, create=True)

    # response
    print(f'Start task({task}): {st.session_state.conversation[-1].content}')
    if task in [Task.ChatGPT.value, Task.GPT4.value, Task.GPT4V.value]:
        queue = openai.chat_stream(conversation=st.session_state.conversation, 
                                    task=task,
                                    attachment=attachment,
                                    guest=st.session_state.guest)
        if openai.DEBUG:
            queue.put('controller: queue returned\n\n')
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
            task = model.Task(task).name,
            name = task_params[task][task]['model'],
        )
        st.session_state.conversation.append(bot_response)
    elif task == Task.text2img.value:
        toast = st.toast('正在绘制', icon='🖌️')
        with st.spinner('正在绘制'):
            urls, revised_prompts = imagegen.gen_image(user_input)
            bot_response = Message(
                role= Role.assistant.name,
                content = '\n\n'.join(revised_prompts),
                task = model.Task(task).name,
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
            transcription = speech.transcript(attachment)
            bot_response = Message(
                role= Role.assistant.name,
                content = transcription,
                task = model.Task(task).name,
                name = task_params[task][task]['model'],
                time = datetime.now()
            )
            st.session_state.conversation.append(bot_response)
            finish_reply(bot_response)
    elif task == Task.TTS.value:
        with st.spinner('正在转译'):
            speech_obj = speech.text_to_speech(user_input)
            speech_data = speech_obj.getvalue()
            filename = f'{user_input[:20]}.mp3'
            filetype = 'audio/mp3'
            rec = UploadedFileRec(
                    file_id=str(speech_data)[:20],
                    name=filename,
                    type=filetype,
                    data=speech_data,
                )
            speech_file = UploadedFile(rec, None)
            bot_response = Message(
                role=Role.assistant.name,
                content=None,
                task=model.Task(task).name,
                name = task_params[task][task]['model'],
                time = datetime.now(),
                medias=speech_file
            )
            st.session_state.conversation.append(bot_response)
            finish_reply(bot_response)
    else:
        raise NotImplementedError(task)
    
    return query_message, bot_response


def handle_action(action_token, *args):
    if action_token == model.RETRY_ACTION:
        bot_response = delete_last_message()
        user_prompt = delete_last_message()
        if bot_response.role == Role.assistant.name and user_prompt.role == Role.user.name:
            user_input = user_prompt.content
            gen_response(query=user_input)
    if action_token == model.MODIFY_ACTION:
        bot_response = delete_last_message()
        user_prompt = delete_last_message()
        if bot_response.role == Role.assistant.name and user_prompt.role == Role.user.name:
            user_input = user_prompt.content
            # st.session_state.input_text = user_input
            container = args[0]
            def update_input():
                new_input = st.session_state.new_input
                if new_input and new_input != user_input:
                    gen_response(new_input)
            container.text_input('New Input:', value=user_input, on_change=update_input, key='new_input')
    else:
        raise NotImplementedError(action_token)
    

from io import BytesIO
def play_audio(bobj:BytesIO, container=None, autoplay=False):
    b64_audio = base64.b64encode(bobj.getvalue()).decode()
    autoplay_tag = 'autoplay' if autoplay else ''
    audio_html = f"""
    <audio controls {autoplay_tag}>
        <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    """
    if container:
        container.markdown(audio_html, unsafe_allow_html=True)
    else:
        st.markdown(audio_html, unsafe_allow_html=True)
    
def finish_reply(message):
    message.queue = None
    dialog.update_message(st.session_state.name, st.session_state.selected_title, message, create=True)
    print('-'*50)
    

def display_media(media, container=st):
    media_type = media.type.split('/')[0]
    if media.type in openai_image_types or media_type == model.MediaType.image.name:
        container.image(media, use_column_width='always')
    elif media.type in speech_media_types or media_type == model.MediaType.audio.name:
        play_audio(media, container=container)
    elif media.type == 'mp4' or media_type == model.MediaType.video.name:
        container.video(media)
    else:
        raise NotImplementedError(media.tpye)


def call_functions(message):
    functions = message.functions
    queue = message.queue
    
    
def delete_last_message():
    msg = st.session_state.conversation.pop(-1)
    dialog.delete_message(st.session_state.name, st.session_state.selected_title)
    return msg
