# https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models

from retry import retry
import requests, json, re, logging
import threading, multiprocessing
# from collections import deque
from queue import Queue
import streamlit as st
from . import dialog, auth, model, apify, utils
from openai import OpenAI

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
        'model': 'gpt-3.5-turbo', #'gpt-3.5-turbo',
        'url': 'https://api.openai.com/v1/chat/completions',
        'max_tokens': 4000,
    },
    model.Task.GPT4.value: {
        'model': 'gpt-4',
        'url': 'https://yeqiu-gpt4-3.xyhelper.cn/v1/chat/completions',
        'max_tokens': 8000,
    },
    model.Task.GPT4V.value: {
        'model': 'gpt-4v',
        'url': 'http://121.127.44.50:8100/v1/chat/gpt4v',
        'max_tokens': 4000,
    }
}
temperature = 0.7
roles2keep = ['system', 'user', 'assistant']
key2keep = ['role', 'content']
accepted_attachment_types = ['png', 'jpg', 'jpeg']


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
    thread = threading.Thread(target=get_response, args=(task, data, header, queue))
    thread.start()
    return queue
    

# get streaming response
def get_response(task, data, header, queue=None):
    url = data.pop('url')
    file = data.pop('file') if 'file' in data else None
    stream = data['stream']
    if not task == model.Task.GPT4V.value: # gpt-3.5, gpt-4
        # header['Content-Type'] = 'application/json'
        response = requests.post(url, headers=header, json=data, stream=stream, timeout=60)
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
    if DEBUG and queue:
        queue.put('⏳receiving response in another thread \n\n')
    if stream and queue is not None and response.ok:
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
        queue.put({model.SERVER_ERROR: estring})
        return
    

##--------------------信息检索+聊天------------------
def chat_with_search(conversation:list, task:str):
    chat_history = conversation2history(conversation, guest=False, task=task)
    data = {
        'messages': chat_history,
        'stream': True,
        'temperature': temperature,
        'url': task_params[task]['url'],
        'model': task_params[task]['model'],
        'tools': [{'type':'function', 'function': apify.function_google_search}]
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
    '''the thread runner for chat_with_search'''
    result = get_response(task, data, header, queue)
    
    # web search
    if not result or not (tool_results := result[model.TOOL_RESULT]):
        queue.put(model.FINISH_TOKEN)
        utils.logger.info(f'No function returned for "{data["messages"][-3]["content"]}"')
        return
    search_results, also_asks = [], []
    for name, func, kargs in get_function_calls(tool_results):
        assert name == 'google_search'
        message = f'🔍正在检索: {kargs["query"]}'
        queue.put({model.STATUS: message})
        search_result, also_ask = func(**kargs)
        # print(f'🔍search result: \n\n{json.dumps(search_result, indent=2, ensure_ascii=False)}')
        search_results += search_result
        also_asks += also_ask
    search_result_content = [f"[{r['title']}]({r['url']})" for r in search_results]
    search_result_content = '\n'.join(search_result_content)
    logging.info(search_result_content)
    # queue_UI.put(search_result_content)
    
    # let the GPT do the decision, then parse the web content
    for chat in data['messages']:
        if chat['role'] == model.Role.user.name:
            question = chat['content']
    web_content = get_search_content(task, question, search_results, queue)
    # streaming the result using regular chat_stream
    answer_question_with_search_result(task, question, also_asks, web_content, queue)
    # finish
    queue.put(model.FINISH_TOKEN)

        
def get_search_content(task, question, search_result, queue_UI):
    prompt = '请根据检索问题和网络搜索结果，决定是否要访问搜索结果中的网站。请注意：最多访问3个网站。'
    query = f'''【检索问题】{question}
    【网络搜索结果】{search_result}'''
    chat_history = [
        {'role': model.Role.system.name, 'content': prompt},
        {'role': model.Role.user.name, 'content': query}
    ]
    data = {
        'messages': chat_history,
        'url': task_params[task]['url'],
        'model': task_params[task]['model'],
        'temperature': temperature,
        'stream': False,
        'tools': [{'type':'function', 'function': apify.function_parse_web_content}]
    }
    header = {
        'Authorization': f'Bearer {auth.get_openai_key(task)}'
    }
    queue_UI.put({model.STATUS: '⏳正在思考'})
    result = get_response(task, data, header)
    tool_results = result[model.TOOL_RESULT]
    web_contents = []
    for name, func, kargs in get_function_calls(tool_results):
        assert name == 'parse_web_content'
        URL = kargs["url"]
        title = [r['title'] for r in search_result if r['url']==URL][0]
        queue_UI.put({model.STATUS: f'⏳正在阅读: [{title}]({URL})'})
        # 浏览信息
        web_content = func(**kargs)
        if not web_content:
            queue_UI.put({model.STATUS: f'❌无法访问: [{title}]({URL})'})
        else:
            print(f'🔍Ingested web content: {title} with {utils.token_size(web_content)} tokens')
            web_content = utils.truncate_text(web_content, task_params[task]['max_web_content'])
            web_contents.append(web_content)
    return web_contents
    

def answer_question_with_search_result(task, question, also_asks, web_content, queue_UI):
    prompt = '请根据用户问题和网页内容，总结网页信息，请尽量整理得详细一些，不要遗漏。并且总结一些观点并进行详细解答。内容长度至少500字。如果网页内容没有实质性信息，请回答信息量不够。'
    query = f'''【用户问题】{question}
    【相关问题】{';'.join(also_asks)}
    【网页内容】{web_content}
    '''
    chat_history = [
        {'role': model.Role.system.name, 'content': prompt},
        dialog.suggestion_prompt,
        {'role': model.Role.user.name, 'content': query}
    ]
    data = {
        'messages': chat_history,
        'url': task_params[task]['url'],
        'model': task_params[task]['model'],
        'stream': True,
    }
    header = {
        'Authorization': f'Bearer {auth.get_openai_key(task)}'
    }
    get_response(task, data, header, queue_UI)
         
         
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
def conversation2history(conversation:list[model.AppMessage], guest, task) -> list[dict]:
    max_length = 500 if guest else task_params[task]['max_tokens']
    chat_history = [{k: c.dict()[k] for k in key2keep}
                    for c in conversation if c.role in roles2keep and c.content]
    while (l:=chat_len(chat_history)) > max_length and len(chat_history) > 1:
        if chat_history[0]['role'] in ['assistant', 'user']:
            st.toast(f"历史数据过长，舍弃: {chat_history[0]['content'][:10]}")
        chat_history.pop(0)
    chat_history.append(dialog.suggestion_prompt)
    print(f"sending conversation rounds: {len(chat_history)}, length:{l}")
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



if __name__ == '__main__':
    # WIP: test gpt4v
    messages = '请识别图中所有物体，并理解它们的关系。'
    # with open('temp/CF49A632-6E10-4AA3-944F-F4FDA54AF003.png', 'rb') as f:
    #     attachment = f.read()
    # chat_stream(messages, task='GPT4V', attachment=attachment)
    
    ## test search
    st.session_state.name = 'Derek'
    chat_history = [
        model.AppMessage(
            role= model.Role.user.name, 
            name = 'Derek',
            content= messages,
            time = None
        )
    ]
    queue = Queue()
    chat_with_search(chat_history, task=model.Task.ChatSearch.value, queue_UI=queue)