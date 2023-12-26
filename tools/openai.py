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
        'model': 'gpt-4v',
        # 'url': 'http://121.127.44.50:8100/v1/chat/gpt4v',
        'url': 'https://api.openai.com/v1/chat/completions',
        'max_tokens': 4000,
    }
}
temperature = 0.7
roles2keep = ['system', 'user', 'assistant']
key2keep = ['role', 'content']
accepted_image_types = ['png', 'jpg', 'jpeg']


## ------------receiving streaming server-sent events（异步）------------
def chat_stream(conversation:list, task:str, attachment=None, guest=True, tools=None):
    chat_history = conversation2history(conversation, guest, task)
    queue = Queue()
    # create a queue to store the responses
    url = task_params[task]['url']
    model = task_params[task]['model']
    data = {
        'messages': chat_history,
        'stream': STREAMING,
        'temperature': temperature,
        'url': url,
        'model': model,
        'file': attachment,
    }
    
    header = {
        'Authorization': f'Bearer {auth.get_openai_key(task)}'
    }
    if DEBUG:
        queue.put('⏳chat streaming thread starting \n\n')
    thread = threading.Thread(target=request_chat, args=(task, data, header, queue))
    thread.start()
    return queue
    

# get streaming response
def request_chat(task, data, header, queue=None):
    url = data.pop('url')
    file = data.pop('file') if 'file' in data else None
    stream = data['stream']
    assert (stream and queue) or (not stream and queue is None), 'stream and queue must be both True or False'
    try:
        if not task == model.Task.GPT4V.value: # gpt-3.5, gpt-4
            # header['Content-Type'] = 'application/json'
            response = requests.post(url, headers=header, json=data, stream=stream, timeout=model.TIMEOUT/2)
        else: # gpt4v
            data2 = {k:v for k, v in data.items() if k in ['messages', 'stream']}
            message = ''
            for k in range(len(data['messages'])-1, 0, -1):
                if data['messages'][k]['role'] == model.Role.user.name:
                    message = data['messages'][k]['content']
                    break
            data2['message'] = message
            fobject = {'file': (file.name, file)}
            # header['Content-Type'] = 'multipart/form-data' # The issue is that the Content-Type header in your request is missing the boundary parameter, which is crucial for the server to parse the multipart form data correctly. The requests library in Python should add this parameter automatically when you pass data through the files parameter. It seems like the Content-Type header is being set manually somewhere which is overriding the automatically set header by requests. Make sure that you are not setting the Content-Type header manually anywhere in your code or in any middleware that might be modifying the request.
            response = requests.post(url, headers=header, data=data2, files=fobject, stream=stream, timeout=300)
    except Exception as e:
        utils.logger.error(e)
        if queue:
            queue.put({model.SERVER_ERROR: '服务器超时'})
        return
    if stream and response.ok:
        tool_results = []
        for line in response.iter_lines():
            if not line:
                continue
            try:
                key, value = line.decode().split(':', 1)
                # finish
                if model.FINISH_TOKEN in value:
                    if 'tools' in data:
                        # if this is a function call, then return the tool result and do the next
                        print('tool_results: ', tool_results)
                        return {model.TOOL_RESULT: tool_results}
                    else:
                        queue.put('\n\n')
                        queue.put(model.FINISH_TOKEN)
                        print('\n'+'-'*60)
                        return
                # unpack
                value = json.loads(value.strip())
                if key == 'data':
                    content = value['choices'][0]['delta'].get('content')
                    tool_calls = value['choices'][0]['delta'].get('tool_calls')
                    if content:
                        queue.put(content)
                        print(content, end='')
                    if tool_calls:
                        for call in tool_calls:
                            index = call['index']
                            if 'id' in call: # new function
                                assert index == len(tool_results)
                                tool_results.append(call['function'])
                            else: # update function params
                                for k, v in call['function'].items():
                                    tool_results[index][k] += v
                else:
                    raise Exception(line.decode())
            except Exception as e:
                print(e, line)
    elif not stream and response.ok:
        message = response.json()['choices'][0]['message']
        chat_content = message.get('content')
        function_calls = message.get('tool_calls')
        tool_calls = [call['function'] for call in function_calls] if function_calls else None
        not chat_content or print('message:', chat_content)
        not tool_calls or print('tool_calls:', tool_calls)
        if queue:
            queue.put(chat_content)
            queue.put(model.FINISH_TOKEN)
        return {
            'content': chat_content,
            model.TOOL_RESULT: tool_calls,
        }
    else:
        estring = f'出错啦，请重试: {response.status_code}, {response.text}'
        logging.error(estring)
        logging.error(json.dumps(data, indent=2, ensure_ascii=False))
        if queue:
            queue.put({model.SERVER_ERROR: estring})
        return
    

##--------------------信息检索------------------
def chat_with_search(conversation:list, task:str):
    chat_history = conversation2history(conversation, guest=False, task=task)
    data = {
        'messages': chat_history,
        'stream': True,
        'temperature': temperature,
        'url': task_params[task]['url'],
        'model': task_params[task]['model'],
        'tools': [
            {'type': 'function', 'function': apify.function_google_search},
            {'type': 'function', 'function': apify.function_parse_web_content}
        ]
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
    result = request_chat(task, data, header, queue)
    if not result or not (tool_results := result[model.TOOL_RESULT]):
        queue.put(model.FINISH_TOKEN)
        return
    
    # memory
    question = [chat['content'] for chat in data['messages'] if chat['role'] == model.Role.user.name][-1]
    search_results, also_asks = [], []
    new_info = True
    while tool_results and new_info:
        new_info = False
        for name, func, kwargs in get_function_calls(tool_results):
            if name == 'google_search':
                message = f'🔍Searching: {kwargs["query"]}'
                search_result, also_ask = func(**kwargs)
                queue.put({model.STATUS: message, model.HELP: list_dict2string(search_result)})
                search_results += search_result
                also_asks += also_ask
                new_info = True
            elif name == 'parse_web_content':
                url = kwargs["url"]
                title = kwargs.get('title') or urlparse(url).hostname
                target_search = [s for s in search_results if s['url'] == url or s['title'] == title]
                if not target_search:
                    target_search = {
                        'title': title,
                        'url': url
                    }
                    search_results.append(target_search)
                else:
                    target_search = target_search[0]
                if target_search.get('content'):
                    continue
                web_content = func(**kwargs)
                if not web_content:
                    queue.put({model.STATUS: f'❌Cannot access: [{title}]({url})'})
                    web_content = '无法访问该网页'
                else:
                    new_info = True
                    size = utils.token_size(web_content)
                    if size > (max_len:=task_params[task]['max_web_content']):
                        web_content = summarize_content(question, web_content, int(max_len/2), queue)
                        size2 = utils.token_size(web_content)
                        print(f'🔍Ingested web content: {title} with {size2} tokens (shortened from {size} tokens)')
                    queue.put({model.STATUS: f'⏳Reading: [{title}]({url}), 共{size}tokens', model.HELP: web_content})
                # write the result
                target_search['content'] = web_content
        info = '\n'.join([f"[{r['title']}]({r['content']})" for r in search_results if r.get('content')])
        logging.info(info)

        # parse the web content or answer the question
        tool_results = explore_exploit(task, question, search_results, also_asks, tools=new_info, queue=queue)

    queue.put(model.FINISH_TOKEN)



def explore_exploit(task, question, search_results, also_asks, tools, queue):
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
   - Avoid requesting to parse web entries with a 'content' field already existed.
   - No need to request tool usage unless necessary.
   - Today is {datetime.now()}
'''
    new_search_result = [s.copy() for s in search_results]
    for s in new_search_result:
        if s.get('content') and s.get('url'):
            s.pop('url')
            print(f'pop url: {s["title"]}')
    query = f'''[User Question]: {question}
    [Similar questions]：{also_asks}
    [Search results]：{new_search_result}'''
    chat_history = [
        {'role': model.Role.system.name, 'content': prompt},
        {'role': model.Role.user.name, 'content': query}
    ]
    data = {
        'messages': chat_history,
        'url': task_params[task]['url'],
        'model': task_params[task]['model'],
        'temperature': temperature,
        'stream': True,
    }
    # shorten the chat history if too long
    while (ratio:=utils.token_size(str(chat_history)) / task_params[task]['max_tokens']) > 1:
        new_search_result.sort(key=lambda x: utils.token_size(x.get('content')), reverse=True)
        content = new_search_result[0]['content']
        target_length = int(utils.token_size(content)/ratio/2)
        # content2 = utils.truncate_text(content, target_length)
        content2 = summarize_content(question, content, target_length, queue)
        print(f'🔍Truncated chat history: {utils.token_size(content)} -> {utils.token_size(content2)}')
        new_search_result[0]['content'] = content2
        return explore_exploit(task, question, new_search_result, also_asks, tools, queue)
    
    if tools:
        data['tools'] = [{'type':'function', 'function': apify.function_parse_web_content}]
    header = {
        'Authorization': f'Bearer {auth.get_openai_key(task)}'
    }
    queue.put({model.STATUS: '⏳thinking...'})
    result = request_chat(task, data, header, queue)
    if not result:
        return None
    tool_results = result.get(model.TOOL_RESULT)
    return tool_results
    

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
    response = request_chat(model.Task.ChatGPT.value, data, header)
    content2 = response['content']
    print(f'🔍Summarized content: {utils.token_size(content)} -> {utils.token_size(content2)}')
    content2 = utils.truncate_text(content2, max_words)
    return content2
         
         
#------------------UTILITIES-----------------
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
    max_length = 500 if guest else task_params[task]['max_tokens']
    chat_history = [{k: c.model_dump()[k] for k in key2keep}
                    for c in conversation if c.role in roles2keep and c.content]
    while (l:=chat_len(chat_history)) > max_length and len(chat_history) > 1:
        if chat_history[0]['role'] in ['assistant', 'user']:
            st.toast(f"历史数据过长，舍弃: {chat_history[0]['content'][:10]}")
        chat_history.pop(0)
    chat_history.append(dialog.suggestion_prompt)
    if task == model.Task.ChatSearch.value:
        chat_history.append(dialog.search_prompt)
    utils.logger.info(f"sending conversation rounds: {len(chat_history)}, length:{l}")
    return chat_history

# convert openai function_call result to (name, function, query)
def get_function_calls(function_calls, max_calls=3):
    i = 0
    for call in function_calls:
        if (i:=i+1) == max_calls:
            return
        # {'id': 'call_ZRg5LUmA7zhRTaMXc2ug9SsJ', 'type': 'function', 'function': {'name': 'google_search', 'arguments': '{"query": "\\u5317\\u4...29\\u6c14"}'}}
        name = call['name']
        tool_info = apify.tool_list[name]
        func = tool_info['call']
        menifest = tool_info['function']
        keys = [str(k) for k in menifest['parameters']['properties'].keys()]
        arguments = json.loads(call['arguments'])
        query = {k:arguments[k] for k in keys if k in arguments}
        yield name, func, query
        

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