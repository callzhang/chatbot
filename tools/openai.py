# https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models

from retry import retry
import requests, json, re, logging
import threading, multiprocessing
# from collections import deque
from queue import Queue
import streamlit as st
from . import dialog, auth, model, apify, utils
from openai import OpenAI
from urllib.parse import urlparse
from datetime import datetime

DEBUG = st.secrets.debug
STREAMING = st.secrets.streaming
client = OpenAI(api_key=st.secrets["openai-key"], timeout=30)

# 参数
task_params = {
    model.Task.ChatSearch.value: {
        'model': 'gpt-3.5-turbo-1106', #'gpt-3.5-turbo',
        'url': 'https://api.openai.com/v1/chat/completions',
        'max_tokens': 16000,
        'max_web_content': 4000
    },
    model.Task.ChatGPT.value: {
        'model': 'gpt-3.5-turbo-1106',  # 'gpt-3.5-turbo',
        'url': 'https://api.openai.com/v1/chat/completions',
        'max_tokens': 4000,
    },
    model.Task.GPT4.value: {
        'model': 'gpt-4',
        # 'url': 'https://yeqiu-gpt4-3.xyhelper.cn/v1/chat/completions',
        'url': 'https://api.openai.com/v1/chat/completions',
        'max_tokens': 8000,
    },
    model.Task.GPT4V.value: {
        'model': 'gpt-4-vision-preview',
        # 'url': 'http://121.127.44.50:8100/v1/chat/gpt4v',
        'url': 'https://api.openai.com/v1/chat/completions',
        'max_tokens': 4000,
    }
}
TEMPERATURE = 0.7
ROLES2KEEP = ['system', 'user', 'assistant']
KEYS2KEEP = ['role', 'content', 'medias']
IMAGE_TYPES = ['png', 'jpg', 'jpeg']


## ------------receiving streaming server-sent events（异步）------------
def create_chat(conversation:list, task:str, guest=True):
    chat_history = conversation2history(conversation, guest, task)
    queue = Queue()
    max_tokens = task_params[task]['max_tokens'] - chat_len(chat_history)
    # create a queue to store the responses
    url = task_params[task]['url']
    model = task_params[task]['model']
    data = {
        'messages': chat_history,
        'stream': STREAMING,
        'temperature': TEMPERATURE,
        'url': url,
        'model': model,
        'max_tokens': max_tokens
    }
    
    header = {
        'Authorization': f'Bearer {auth.get_openai_key(task)}'
    }
    if DEBUG:
        queue.put('⏳chat streaming thread starting \n\n')
    thread = threading.Thread(target=send_chat, args=(data, header, queue))
    thread.start()
    return queue
    

# get streaming response
@retry(tries=3, delay=2, backoff=2)
def send_chat(data, header, queue=None):
    url = data.pop('url', None)
    if not url:
        for k,m in task_params.items():
            if m['model'] == data['model']:
                url = m['url']
                break
    assert url, 'url is not specified'
    stream = data['stream']
    assert (stream and queue) or (not stream and queue is None), 'stream and queue must be both True or False'
    message_tool_calls = []
    message_content = ''
    message = {
        'content': message_content,
        'tool_calls': message_tool_calls,
        'role': 'assistant'
    }
    try:
        response = requests.post(url, headers=header, json=data, stream=stream, timeout=model.TIMEOUT/2)
    except Exception as e:
        utils.logger.error(e)
        if queue:
            queue.put({model.SERVER_ERROR: '服务器超时'})
        return message
    
    if not response.ok:
        estring = f'出错啦，请重试: {response.status_code}, {response.json()}'
        logging.error(estring)
        logging.error(json.dumps(data, indent=2, ensure_ascii=False))
        if queue:
            queue.put({model.SERVER_ERROR: estring})
        return message
    elif stream:
        for line in response.iter_lines():
            if not line:
                continue
            try:
                key, value = line.decode().split(':', 1)
                # finish
                if model.FINISH_TOKEN in value:
                    if 'tools' not in data:
                        queue.put('\n\n')
                        queue.put(model.FINISH_TOKEN)
                        print('\n'+'-'*60)
                    # append response to messages, so the next tool calls can be memorized
                    data['messages'].append(message)
                    return message
                # parse response for `content` and `tool_calls`
                value = json.loads(value.strip())
                if key == 'data':
                    content = value['choices'][0]['delta'].get('content')
                    tool_calls = value['choices'][0]['delta'].get('tool_calls')
                    if content:
                        message_content += content
                        queue.put(content)
                        print(content, end='')
                    if tool_calls:
                        for call in tool_calls:
                            index = call['index']
                            function = call['function']
                            if call.get('id'): # new function
                                message_tool_calls.append(call)
                            else: # update function params
                                for k, v in function.items():
                                    partial_function = message_tool_calls[index]['function']
                                    partial_function[k] += v
                else:
                    raise Exception(line.decode())
            except Exception as e:
                print(e, line)
        # if no FINISH_TOKEN received, then finish the request
        queue.put(model.FINISH_TOKEN)
        return message
    elif not stream:
        message = response.json()['choices'][0]['message']
        data['messages'].append(message)
        return message
    else:
        raise Exception(f'Unknown response: {response}')
        

@retry(tries=3, delay=2, backoff=2)
def simple_chat(user_input, instruction=''):
    messages = [
        {'role': model.Role.system.name, 'content': instruction},
        {'role': model.Role.user.name, 'content': user_input},
    ]
    data = {
        'messages': messages,
        'model': task_params[model.Task.ChatGPT.value]['model'],
        'stream': False,
        'temperature': TEMPERATURE,
    }
    response = client.chat.completions.create(**data)
    output = response.choices[0].message.content
    return output


# --------------------信息检索------------------
'''
1. 将TOOLS和聊天历史发送给openai
2. 得到openai的回复，如果有tool_calls，则执行tool_calls
3. 对于每个tool_call，如果是google_search，则执行搜索，得到搜索结果
4. 对于每个tool_call，如果是parse_web，则执行网页解析，得到网页内容
5. 将搜索结果和网页内容加入到memory中，数据结构为：[{'title': 'xxx', 'url': 'xxx', 'content': 'xxx'}, ...]
6. 调用`explore_exploit`函数，将搜索结果和网页内容传入，如果memory有变化，则传入TOOLS
7. 得到的结果，如果是有文本生成，则展示在网页端
8. 如果有tool_calls，则回到2，否则结束
'''

TOOLS = [
    {'type': 'function', 'function': apify.function_google_search},
    {'type': 'function', 'function': apify.function_parse_web_content}
]

def chat_with_search(conversation:list, task:str):
    chat_history = conversation2history(conversation, guest=False, task=task)
    data = {
        'messages': chat_history,
        'stream': True,
        'temperature': TEMPERATURE,
        'url': task_params[task]['url'],
        'model': task_params[task]['model'],
        'tools': TOOLS
    }
    header = {
        'Authorization': f'Bearer {auth.get_openai_key(task)}'
    }
    queue = Queue()
    thread = threading.Thread(target=chat_with_search_actor, args=(task, data, header, queue))
    # thread.daemon = True
    thread.start()
    return queue
    
def chat_with_search_actor(task, data, header, queue):
    '''the thread runner for chat_with_search
    1. send assistant chat with tools enabled
    2. get response that may contain tool commands, finish if no commands
        a. if tool is google, do a google search and add search result to memory
        b. if tool is parse_web, do a web parsing and add content to memory
    3. ask assistant if it is enough to fulfill the request, 
        a. if more tool command is issued, then the loop back → 2 
        b. if assistant can answer the question directly, then output the content, finish chat
    '''
    message = send_chat(data, header, queue)
    function_calls = message['tool_calls']
    if not function_calls:
        queue.put(model.FINISH_TOKEN)
        return
    # memory
    messages = data['messages']
    new_info = True
    while function_calls and new_info:
        new_info = False
        for fid, name, func, kwargs in parse_function_calls(function_calls):
            if name == apify.function_google_search['name']:
                message = f'🔍Searching: {kwargs["query"]}'
                queue.put({model.STATUS: message})
                search_result, also_ask = func(**kwargs)
                queue.put({model.STATUS: f'🔍Found {len(search_result)} search results', model.HELP: list_dict2string(search_result)})
                function_result = search_result + also_ask
                new_info = True
            elif name == apify.function_parse_web_content['name']:
                url = kwargs["url"]
                title = kwargs.get('title') or urlparse(url).hostname
                # crawl the website
                web_content = func(**kwargs)
                if not web_content:
                    queue.put({model.STATUS: f'❌Cannot access: [{title}]({url})'})
                    web_content = '无法访问该网页'
                else:
                    new_info = True
                    size = utils.token_size(web_content)
                    queue.put({model.STATUS: f'⏳Reading: [{title}]({url}), 共{size}tokens', model.HELP: web_content})
                function_result = web_content
            else:
                raise NotImplementedError(f'Unknown function: {name}')
            # add to memory
            messages.append(
                {
                    "tool_call_id": fid,
                    "role": "tool",
                    "name": name,
                    "content": str(function_result),
                }
            )
        # check all functions are executed, otherwise remove the record
        all_tool_call_ids = [m['tool_call_id'] for m in messages if m.get('tool_call_id')]
        for m in messages:
            for f in m.get('tool_calls', []):
                if f['id'] not in all_tool_call_ids:
                    m['tool_calls'].remove(f)

        # parse the web content or answer the question
        function_calls = explore_exploit(task, messages, tools=TOOLS if new_info else None, queue=queue)
        # if tool_results returned, then continue the searching/extraction
    queue.put(model.FINISH_TOKEN)


prompt = f'''
You are a knowledgeable assistant capable of answering any questions. Here's how to proceed:

1. **Understand the User Question**: Review the user's question carefully.

2. **Examine Provided Information**: 
   - **Search Results**: Check the 'content' field of each provided search result for relevant information. There's no need to re-parse these contents.
   - **Similar questions**: Review the provided questions and answers similar to the user's question.

3. **Formulate Your Answer**: 
   - If the provided information suffices, answer the question in the user question's language.
   - If additional information is needed, you may request to parse up to three websites.

4. **Citing Sources**: 
   - If citing from search results, use the format [[NUMBER](URL)] at the end of the corresponding line, where NUMBER is the entry index and URL is the provided link.

**Remember**:
   - Avoid requesting to parse web entries (in search results) with 'content' field already existed.
   - No need to request tool usage unless necessary.
   - Today is {datetime.now()}
'''
RAG_PROMPT = {'role': model.Role.system.name, 'content': prompt}

def explore_exploit(task, messages, tools, queue):
    question = get_question(messages)
    # shorten the chat history if too long
    while (ratio := utils.token_size(str(messages)) / task_params[task]['max_tokens']) > 1:
        # shorten the memory if too long, works recursively and always shortens the longest content
        longest_message = sorted(messages, key=lambda x: utils.token_size(x.get('content')), reverse=True)[0]
        content = longest_message['content']
        title = longest_message.get('title')
        target_length = int(utils.token_size(content)/ratio/2)
        # content2 = utils.truncate_text(content, target_length)
        content2 = summarize_content(question, content, target_length, queue)
        print(f'🔍Truncated content of {title}: {utils.token_size(content)} -> {utils.token_size(content2)}')
        for m in messages:
            if m.get('content') == content:
                m['content'] = content2
        return explore_exploit(task, messages, tools, queue)
    
    # size reduced, continue to send request
    if RAG_PROMPT not in messages:
        messages.append(RAG_PROMPT)
    data = {
        'messages': messages,
        'url': task_params[task]['url'],
        'model': task_params[task]['model'],
        'temperature': TEMPERATURE,
        'stream': True,
    }
    if tools:
        data['tools'] = tools
    header = {
        'Authorization': f'Bearer {auth.get_openai_key(task)}'
    }
    queue.put({model.STATUS: '⏳Thinking...'})
    message = send_chat(data, header, queue)
    function_calls = message.get('tool_calls')
    #TODO: save results to media
    return function_calls
    

def summarize_content(question, content, max_words, queue):
    prompt = '''The following is a user question and a web content. \
        The content is too long for GPT to process.\
        Please make summarization of the web content so that the new content \
        only contains relavent information to the user's quetion. \
        Please note: \
        1. summarization should be no than {max_words} words. \
        2. reply with the same language as the user question. \
        3. the summarization should be in markdown format. \
        4. reply with the summarization directly'''
    max_tokens = task_params[model.Task.ChatGPT.value]['max_tokens']
    queue.put({model.STATUS: f'🔍Ingest web content with {utils.token_size(content)} tokens'})
    if (ratio:=utils.token_size(content) / max_tokens) > 1:
        chunks, summarizes = [], []
        n = int(ratio) + 1
        max_words_t = int(max_words/n)
        while utils.token_size(content) > 0:
            content_t = utils.truncate_text(content, max_tokens)
            chunks.append(content_t)
            content = content[len(content_t):]
            content_t = summarize_content(question, content_t, max_words_t, queue)
            summarizes.append(content_t)
        content2 = '\n\n'.join(summarizes)
        return content2
    query = f'''[User Question] {question}
    [Web content] {content}
    '''
    chat_history = [
        {'role': model.Role.system.name, 'content': prompt},
        {'role': model.Role.user.name, 'content': query}
    ]
    data = {
        'messages': chat_history,
        'url': task_params[model.Task.ChatGPT.value]['url'],
        'model': task_params[model.Task.ChatGPT.value]['model'],
        'stream': False,
    }
    header = {
        'Authorization': f'Bearer {auth.get_openai_key(model.Task.ChatGPT.value)}'
    }
    response = send_chat(data, header)
    content2 = response['content']
    print(f'🔍Summarized content: {utils.token_size(content)} -> {utils.token_size(content2)}\n{content2}')
    content2 = utils.truncate_text(content2, max_words)
    return content2
         
         
#------------------UTILITIES-----------------
# message modifier
get_question = lambda messages: [chat['content'] for chat in messages if chat['role'] == model.Role.user.name][-1]

# adapter for gradio
def history2chat(history:list[dict]) -> list[list]:
    chatbot = []
    roles = ['user', 'assistant']
    history_ = [c for c in history if c['role'] in roles]
    for i, chat in enumerate(history_):
        if i % 2 == 0:
            chatbot.append([None, None])
        if chat['role'] == roles[0]:
            chatbot[i//2][0] = chat['content']
        elif chat['role'] == roles[1]:
            chatbot[i//2][1] = chat['content']
    return chatbot


# convert AppMessage to OpenAI chat format
def conversation2history(conversation:list[model.Message], guest, task) -> list[dict]:
    max_char = task_params[task]['max_tokens']
    chat_history = []
    # add prompt
    chat_history.append(dialog.suggestion_prompt)
    if task == model.Task.ChatSearch.value:
        chat_history.append(dialog.search_prompt)
    # keep history with only roles2keep and key2keep
    chat_history += [{k: getattr(c, k) for k in KEYS2KEEP}
                    for c in conversation if c.role in ROLES2KEEP and c.content]
    
    # remove excessive history
    while (l:=chat_len(chat_history)) > max_char and len(chat_history) > 1:
        if chat_history[0]['role'] in ['assistant', 'user']:
            # st.toast(f"历史数据过长，舍弃: {chat_history[0]['content'][:10]}")
            chat_history.pop(0)
    # process media
    '''payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What’s in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
    }'''
    for chat in chat_history:
        if task==model.Task.GPT4V.value:
            if medias:=chat.pop('medias', None):
                content = [{
                    'type': 'text',
                    'text': chat['content']
                }]
                for media in medias:
                    if media.type.split('/')[1] in IMAGE_TYPES:
                        content.append({
                            'type': 'image_url',
                            'image_url': {'url': media._file_urls}
                        })
                    else:
                        logging.warning(f'Unsupported media type: {media.type}')
                chat['content'] = content
        else:
            chat.pop('medias', None)
        
    return chat_history

# convert openai function_call result to (name, function, query)
def parse_function_calls(function_calls, max_calls=20):
    i = 0
    for call in function_calls:
        # {
        #     'id': 'call_ZRg5LUmA7zhRTaMXc2ug9SsJ', 
        #     'type': 'function', 
        #     'function': {
        #         'name': 'google_search', 
        #         'arguments': '{"query": "\\u5317\\u4...29\\u6c14"}'
        #     }
        # }
        function = call['function']
        name = function['name']
        tool_info = apify.tool_list[name]
        func = tool_info['call']
        menifest = tool_info['function']
        keys = [str(k) for k in menifest['parameters']['properties'].keys()]
        arguments = json.loads(function['arguments'])
        query = {k:arguments[k] for k in keys if k in arguments}
        yield call['id'], name, func, query
        if (i := i+1) == max_calls:
            return
        

def chat_len(conversation):
    chat_string = ' '.join(c['content'] for c in conversation if c['content'])
    # count tokens
    count = utils.token_size(chat_string)
    return count

def list_dict2string(list_dictionary):
    dict2str = lambda d: '\n'.join([f'{k}: {v}' for k, v in d.items()])
    content = '\n\n---\n\n'.join([dict2str(d) for d in list_dictionary])
    return content



if __name__ == '__main__':
    # WIP: test gpt4v
    messages = '请识别图中所有物体，并理解它们的关系。'
    # with open('temp/CF49A632-6E10-4AA3-944F-F4FDA54AF003.png', 'rb') as f:
    #     attachment = f.read()
    # chat_stream(messages, task='GPT4V', attachment=attachment)
    
    ## test search
    st.session_state.name = 'Derek'
    chat_history = [
        model.Message(
            role= model.Role.user.name, 
            name = 'Derek',
            content= messages,
            time = None
        )
    ]
    queue = Queue()
    chat_with_search(chat_history, task=model.Task.ChatSearch.value, queue=queue)