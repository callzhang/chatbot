import gradio as gr
import random
import time
from tools import chat, utils

name = 'Derek'

themes = [
    # 'sudeepshouche/minimalist',
    # 'bethecloud/storj_theme',
    # 'ParityError/LimeFace',
    # 'gradio/base',
    # 'gradio/monochrome',
    'derekzen/stardust'
]

    
with gr.Blocks(theme=random.choice(themes),
               title='星尘小助手') as demo:
    history = gr.State(utils.init_prompt)

    def bot(msg, history, task):
        if not msg or msg.strip() == '':
            print('received empty string')
            print(f'history:\n{history}')
            chatbot = chat.history2chat(history)
            return '', history, chatbot
            
        # add history
        history.append({
            "role": "user", 
            "content": msg, 
            "task": task
        })
        history.append({'role': 'assistant', 'content': ''})
        chatbot = chat.history2chat(history)
        queue = chat.chat_stream(history, name)
        start = time.time()
        receiving = True
        actions = {}
        while receiving:
            while queue is not None and len(queue):
                content = queue.popleft()
                if content == utils.FINISH_TOKEN:
                    receiving = False
                else:
                    history[-1]['content'] += content
                    start = time.time()
            # yield result
            chatbot = chat.history2chat(history)
            chatbot[-1][1] = utils.filter_suggestion(history[-1]['content'])
            yield '', history, chatbot
            # timeout
            if time.time() - start > utils.TIMEOUT:
                chatbot[-1][1] += '\n抱歉出了点问题，请重试...'
                actions.update({'重试': utils.RETRY_TOKEN})
                history[-1]['actions'] = actions
                receiving = False
                yield '', history, chatbot
            time.sleep(0.1)
    
    def process_suggestions(history):
        # suggestion
        content = history[-1].get('content')
        suggestions = []
        if utils.SUGGESTION_TOKEN in content:
            content, suggestions = utils.parse_suggestions(content)
            history[-1]['suggestions'] = suggestions
            history[-1]['content'] = content
            print(f'suggestion: \n{suggestions}')
        action_btns = [gr.Button.update(value=suggestion, visible=True) for suggestion in suggestions]
        
        #actions
        actions = history[-1].get('actions')
        if actions:
            for title, action in actions.items():
                if action == utils.RETRY_TOKEN:
                    action_btns.append(gr.Button.update(value=title, visible=True))
            
        action_btns += [gr.Button.update(visible=False) for i in range(10-len(suggestions))]
        
        return action_btns
        
    def action(value):
        if value == '重试':
            bot_response = history.pop(-1)
            user_input = history.pop(-1)
            return user_input['content']
        else:
            return value
        
    def on_select(evt: gr.SelectData):  # SelectData is a subclass of EventData
        return f"You selected 【{evt.value}】 at 【{evt.index}】 from 【{evt.target}】"

    ## interface
    chatbot = gr.Chatbot(show_label=False)
    with gr.Row():
        with gr.Column(scale=0.1):
            task = gr.Dropdown(['ChatGPT', 'GPT-4'], value='ChatGPT', show_label=False)
        with gr.Column():
            msg = gr.Textbox(placeholder='输入你的问题，然后按回车提交。', show_label=False)
    with gr.Row():
        action_btns = []
        for i in range(10):
            action_btn = gr.Button('对话区域', visible=False)
            action_btn.click(action, action_btn, msg)
            action_btns.append(action_btn)
        new_chat = gr.Button("💬新对话")
        save = gr.Button('💾保存')
    statement = gr.Textbox('选中的文本')
    
    ## interactions
    chatbot.select(on_select, None, statement)
    msg.submit(bot, [msg, history, task], [msg, history, chatbot], show_progress=True)\
        .then(process_suggestions, history, action_btns)\
        .then(chat.history2chat, history, chatbot)
    new_chat.click(lambda: [], [], chatbot, queue=False)


demo.queue(concurrency_count=16).launch(
    show_api=False, 
    # share=True, 
    debug=True, 
    favicon_path='images/icon.ico')
