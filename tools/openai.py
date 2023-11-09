# https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models

from retry import retry
import requests, json, re, logging, time
import threading
from collections import deque
import streamlit as st
from . import dialog, utils, model, apify
try:
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
except:
    pass

# 参数
task_params = {
    model.Task.ChatSearch.value: {
        'model': 'gpt-3.5-turbo-1106', #'gpt-3.5-turbo',
        'url': 'https://api.openai.com/v1/chat/completions',
        'max_tokens': 8000,
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

# function calling
function_google_search = {
    "name": "google_search",
    "description": "Search inormation on Google",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The keywords string to search for information on the internet. Returns the search results in dictionary format.",
            },
        },
        "required": ["query"],
    },
}

function_parse_web_content = {
    "name": "parse_web_content",
    "description": "Parse web content",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The url of the web page to parse. Returns the content of the website in markdown format.",
            },
        },
        "required": ["url"],
    },
}

tool_list = {
    'google_search': {
        'call': apify.search_google,
        'function': function_google_search,
    },
    'scrape_page': {
        'call': apify.parse_web_content,
        'function': function_parse_web_content
    }
}

def chat_len(conversation):
    chat_string = ' '.join(c['content'] for c in conversation if c['content'])
    # count tokens
    try:
        count = len(tokenizer.encode(chat_string))
    except:
        count = len(chat_string)
    return count


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
    while chat_len(chat_history) > max_length and len(chat_history) > 1:
        if chat_history[0]['role'] in ['assistant', 'user']:
            st.toast(f"历史数据过长，舍弃: {chat_history[0]['content'][:10]}")
        chat_history.pop(0)
    chat_history.append(dialog.suggestion_prompt)
    print(f"sending conversation rounds: {len(chat_history)}, length:{chat_len(chat_history)}")
    return chat_history


## receiving streaming server-sent events（异步）
def chat_stream(conversation:list, username:str, task:str, queue:deque, attachment=None, guest=True, tools=None):
    chat_history = conversation2history(conversation, guest, task)
    # create a queue to store the responses
    url = task_params[task]['url']
    model = task_params[task]['model']
    data = {
        'messages': chat_history,
        'stream': True,
        'temperature': temperature,
        'url': url,
        'model': model,
        'file': attachment,
        'stream': True,
    }
        
    thread = threading.Thread(target=get_response, args=(task, username, data, queue))
    # thread.daemon = True
    thread.start()
    return queue
    

# get streaming response
def get_response(task, username, data, queue=None):
    url = data.pop('url')
    file = data.pop('file') if 'file' in data else None
    stream = data['stream']
    header = {
        'Authorization': f'Bearer {utils.get_openai_key(username, task)}'
    }
    if not file: # gpt-3.5, gpt-4
        header['Content-Type'] = 'application/json'
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
    if stream and response.ok:
        tool_results = []
        for line in response.iter_lines():
            if not line:
                continue
            if line == model.FINISH_TOKEN.encode():
                if tool_results:
                    queue.append({model.TOOL_RESULT: tool_results})
                    print(tool_results)
                else:
                    queue.append(model.FINISH_TOKEN)
                    print('\n'+'-'*60)
                return
            try:
                key, value = line.decode().split(':', 1)
                value = json.loads(value.strip())
                if key == 'data':
                    content = value['choices'][0]['delta'].get('content')
                    tool_calls = value['choices'][0]['delta'].get('tool_calls')
                    if content:
                        queue.append(content)
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
        tool_calls = message.get('tool_calls')
        not chat_content or print('message:', chat_content)
        not tool_calls or print('tool_calls:', tool_calls)  
        return {
            'content': chat_content,
            model.TOOL_RESULT: tool_calls,
        }
    else:
        estring = f'出错啦，请重试: {response.status_code}, {response.text}'
        logging.error(json.dumps(data, indent=2, ensure_ascii=False))
        queue.append({model.SERVER_ERROR: estring})
        return

## 信息检索+聊天
def chat_with_search(conversation:list, username:str, task:str, queue_UI:deque):
    chat_history = conversation2history(conversation, guest=False, task=task)
    data = {
        'messages': chat_history,
        'stream': False,
        'temperature': temperature,
        'url': task_params[task]['url'],
        'model': task_params[task]['model'],
        'tools': [{'type':'function', 'function': function_google_search}]
    }
    thread = threading.Thread(target=chat_with_search_actor, args=(task, username, data, queue_UI))
    thread.start()
    
    
def chat_with_search_actor(task, username, data:dict, queue_UI:deque):

    result = get_response(task, username, data)
    assert model.TOOL_RESULT in result
    tool_results = result[model.TOOL_RESULT]
    search_results = []
    for name, func, kargs in get_function_calls(tool_results):
        assert name == 'google_search'
        message = f'⏳正在检索: {kargs["query"]}\n\n'
        queue_UI.append(message)
        search_result = func(**kargs)
        print(f'🔍search result: \n\n{json.dumps(search_result, indent=2, ensure_ascii=False)}')
        search_results += search_result
    search_result_content = [f"[{r['title']}]({r['url']})" for r in search_results]
    search_result_content = '\n\n'.join(search_result_content)
    queue_UI.append(search_result_content)
    queue_UI.append(model.FINISH_TOKEN)
    
    # TODO: let the GPT do the decision
    # url = chat(<prompt>)
    # TODO: parse the web content
    # web_content = apify.parse_web_content(url)
    # TODO: streaming the result using regular chat_stream
    # chat_stream(<prompt>)
    return

def get_function_calls(tool_results):
    for tool_result in tool_results:
        assert tool_result['type'] == 'function'
        # {'id': 'call_ZRg5LUmA7zhRTaMXc2ug9SsJ', 'type': 'function', 'function': {'name': 'google_search', 'arguments': '{"query": "\\u5317\\u4...29\\u6c14"}'}}
        function_result = tool_result['function'] # openai function result
        name = function_result['name']
        tool_info = tool_list[name]
        func = tool_info['call']
        menifest = tool_info['function']
        keys = [str(k) for k in menifest['parameters']['properties'].keys()]
        arguments = json.loads(function_result['arguments'])
        query = {k:arguments[k] for k in keys if k in arguments}
        yield name, func, query
        
         
def is_markdown(text):
    # all markdown syntax
    patterns = [
        r'\n\d\.\s',  # ordered list
        r'\*\*|__',  # bold
        r'\n-\s',  # unordered list
        r'\n>\s',  # blockquote
        r'\n#+\s',  # header
        r'`(.*?)`',  # inline code
        r'\n`{3}.*?\\n`{3}',  # code block
        r'\n---\n',  # horizontal rule
        r'\!\[(.*?)\]\((.*?)\)',  # image
    ]
    matches = [re.findall(pattern, text) for pattern in patterns]
    is_md = any(matches)
    return is_md

if __name__ == '__main__':
    # WIP: test gpt4v
    # messages = '请识别图中所有物体，并理解它们的关系。'
    # with open('temp/CF49A632-6E10-4AA3-944F-F4FDA54AF003.png', 'rb') as f:
    #     attachment = f.read()
    # chat_stream(messages, username='test', task='GPT4V', attachment=attachment)
    
    ## test search
    pass
