import asyncio, pprint
from EdgeGPT import Chatbot, ConversationStyle
from collections import deque
import threading
from . import chat
finish_token = chat.finish_token


class BingGPT:
    def __init__(self, style: ConversationStyle = ConversationStyle.balanced):
        self.bot = None
        self.style = style
        self.renew()
        
        
    def __del__(self):
        asyncio.run(self.close())
        
        
    def renew(self):
        self.bot = Chatbot(cookiePath='.streamlit/bing.cookies')
        
    def is_open(self):
        return not (self.bot and self.bot.chat_hub.wss and self.bot.chat_hub.wss.closed)
    
    is_alive = property(is_open)
        
    async def chat(self):
        if not self.is_alive:
            self.renew()
        response = await self.bot.ask(prompt="Hello world", conversation_style=self.style)
        print(response)
        

    async def chat_async(self, queue: deque, prompt: str):
        if not self.is_alive:
            self.renew()
        message = ''
        async for finished, response in self.bot.ask_stream(prompt):
            if not finished:
                new_msg = response.replace(message, '')
                print(new_msg, end='')
                queue.append(new_msg)
                message = response
            else:
                print('')
                queue.append(finish_token)
                print('-'*60)
                # pprint.pprint(response)
                
    def chat_run(self, queue, prompt):
        asyncio.run(self.chat_async(queue, prompt))
    
    
    def chat_stream(self, prompt):
        '''主函数
        返回一个队列，用于接收对话内容
        返回一个线程，用于运行对话'''
        queue = deque()
        thread = threading.Thread(target=self.chat_run, args=(queue, prompt))
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
    bing = BingGPT()
    conversation = [{'content': 'Bing GPT的优点是什么？'}]
    queue, thread = bing.chat_stream(conversation)
