import asyncio, pprint, logging
from EdgeGPT import Chatbot, ConversationStyle
from collections import deque
import threading, json
try:
    from . import openai
except:
    import chat
    
from . import utils

class BingAI:
    def __init__(self, name, style: ConversationStyle = ConversationStyle.balanced):
        self.bot = None
        self.style = style
        self.name = name
        self.renew()
        
    def __del__(self):
        asyncio.run(self.close())
        
        
    def renew(self):
        try:
            self.bot = Chatbot(cookiePath=utils.get_bingai_key(self.name))
        except Exception as e:
            logging.error(f'创建bing实例出错：\n{e}')
            
        
    async def chat(self):
        if not self.is_alive:
            self.renew()
        response = await self.bot.ask(prompt="Hello world", conversation_style=self.style)
        print(response)
        

    async def chat_async(self, queue: deque, prompt: str):
        tried = 0
        while not self.bot:
            self.renew()
            tried += 1
            if tried > 2:
                # 如果仍然不行，则认为账户失效
                queue.append('BingAI账户失效，请检查！')
                queue.append(utils.FINISH_TOKEN)
                return
        message = ''
        async for finished, response in self.bot.ask_stream(prompt):
            if not finished:
                new_msg = response.replace(message, '')
                print(new_msg, end='')
                queue.append(new_msg)
                message = response
            else:
                print('')
                # pprint.pprint(response)
                suggestions = [r['text'] for r in response['item']
                               ['messages'][1]['suggestedResponses']]
                print(f'{utils.SUGGESTION_TOKEN}:  {suggestions}')
                queue.append(f'{utils.SUGGESTION_TOKEN}: {json.dumps(suggestions)}')
                queue.append(utils.FINISH_TOKEN)
                print('-'*60)
                break
        self.close()
                
    def chat_run(self, queue, prompt):
        asyncio.run(self.chat_async(queue, prompt))
    
    
    def chat_stream(self, prompt):
        '''主函数
        返回一个队列，用于接收对话内容
        返回一个线程，用于运行对话'''
        queue = deque()
        thread = threading.Thread(target=self.chat_run, args=(queue, prompt))
        thread.daemon = True
        thread.start()
        return queue, thread

    async def close(self):
        await self.bot.close()
        self.bot = None
        self.open = False
        
    async def reset(self):
        self.bot.reset()

if __name__ == "__main__":
    queue = deque()
    bing = BingAI()
    conversation = [{'content': 'Bing GPT的优点是什么？'}]
    queue, thread = bing.chat_stream(conversation)
