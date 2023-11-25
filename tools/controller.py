import streamlit as st
from tools import model, utils
from datetime import datetime
from . import dialog, openai, bing, imagegen, asr
import logging
import re, ast, time

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

## display assistant message
def show_streaming_message(message: Message, message_placeholder):
    i = st.session_state.conversation.index(message)
    role, content, medias =  message.role, message.content, message.medias
    status_placeholder = message_placeholder.empty()
    text_placeholder = message_placeholder.empty()
    if message.queue is not None:
        status_container = None
        while (queue := message.queue) is not None:  # streaming
            while queue.qsize() > 0:
                char = queue.get()
                message.time = datetime.now()
                if isinstance(char, str):
                    if char == model.FINISH_TOKEN:
                        finish_reply(message)
                        break
                    message.content += char
                elif isinstance(char, dict):  # network error
                    if v := char.get(model.SERVER_ERROR):
                        message.content += f'\n\n{v}'
                        message.actions = {'重试': model.RETRY_TOKEN}
                        finish_reply(message)
                    elif functions := char.get(model.TOOL_RESULT):
                        # message.content += f'```{json.dumps(v, indent=2, ensure_ascii=False)}```'
                        message.functions += functions
                        # finish_reply(message)
                    elif v := char.get(model.STATUS):
                        if not status_container: #init
                            status_container = status_placeholder.status('正在检索', expanded=True)
                        help = char.get(model.HELP)
                        status_container.markdown(v, help=help)
                        message.status.append(v)
                else:
                    raise Exception(f'Unknown content type: {type(content)}')
            # 超时
            if (datetime.now() - message.time).total_seconds() > model.TIMEOUT:
                message.content += '\n\n请求超时，请重试...'
                message.actions = {'重试': model.RETRY_TOKEN}
                finish_reply(message)
                break
            # 渲染
            content_full = message.content.replace(model.SUGGESTION_TOKEN, '')
            text_placeholder.markdown(content_full + "▌")
            time.sleep(0.1)
        # remove msg and status
        text_placeholder.empty()
        status_placeholder.empty()
    
    # show non-streaming message
    if message.status: # show status
        with status_placeholder.status('正在检索') as status:
            for s in message.status:
                status.write(s)
            status.update(label='检索完成', state="complete", expanded=False)

    # media
    content = message.content
    suggestions = message.suggestions
    if medias:
        for media in medias:
            display_media(media)
    # suggestion
    if content and (model.SUGGESTION_TOKEN in content or '启发性问题:' in content):
        content, suggestions = parse_suggestions(content)
        message.suggestions = suggestions
        message.content = content
    if suggestions and i == len(st.session_state.conversation) - 1:
        suggestions = set(suggestions)
        for suggestion in suggestions:
            message_placeholder.button('👉🏻'+suggestion[:30], help=suggestion,
                        on_click=gen_response, kwargs={'query': suggestion})
    # text content
    if content:
        text_placeholder.markdown(content)
    # actions: only "retry" is supported
    if (actions := message.actions) and i == len(st.session_state.conversation) - 1:
        for action, token in actions.items():
            message_placeholder.button(action, on_click=handle_action, args=(token,))

## 对输入进行应答
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
    
    return query_message, bot_response


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
    if model.SUGGESTION_TOKEN in content or '启发性问题:' in content:
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



if __name__ == '__main__':
    content = '''作为基于Transformer技术的AI助手，我有以下能力：

1. 自然语言处理（NLP）：我可以理解和生成自然语言文本，并通过语义理解和语言生成技术来回答问题、提供信息和进行对话。

2. 知识检索和推理：我可以从广泛的知识库中检索和提取信息，包括事实、定义、解释、统计数据等，并进行推理和逻辑推断。

3. 问题解答和咨询：我可以回答各种AI相关的问题，包括机器学习、深度学习、计算机视觉、自然语言处理等领域，并提供咨询和建议。

4. 数据标注和数据策略：作为星尘数据的AI助手，我可以帮助解答与数据标注和数据策略相关的问题，包括数据集的构建、标注质量控制、标注工具选择等方面。

5. 提供相关资源和指导：如果我无法回答你的问题，我会建议你访问星尘数据的官方网站（stardust.ai），那里会有更多关于AI和数据领域的资源和指导。

启发性问题:
- 你能给我提供一些关于自然语言处理的应用领域吗？
- 在数据标注过程中，如何确保标注质量？
- 你能向我解释一下深度学习是如何工作的吗？'''
    content, suggestion = parse_suggestions(content)
    print(content)
