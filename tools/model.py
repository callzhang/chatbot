
from enum import Enum, unique
from collections import deque
from datetime import datetime
from streamlit.runtime.uploaded_file_manager import UploadedFile, UploadedFileRec
from io import BytesIO
import requests, os, logging
from pydantic.dataclasses import dataclass # not useful as it cannot check arbitrary types
from pydantic import BaseModel, validator
from threading import Thread


SUGGESTION_TOKEN = '[SUGGESTION]'
FINISH_TOKEN = 'data: [DONE]'
RETRY_TOKEN = '[RETRY]'
ACTIONS = [RETRY_TOKEN]
TIMEOUT = 30
LOGIN_CODE = 'login_code'



@unique
class Task(Enum):
    # internal name : display name
    ChatGPT = '对话'
    GPT4 = 'GPT4'
    GPT4V = 'GPT4V'
    BingAI = 'BingAI'
    text2img = '文字做图'
    ASR = '语音识别'
    @classmethod
    def names(cls):
        return [c.name for c in cls]
    @classmethod
    def values(cls):
        return [c.value for c in cls]
    @classmethod
    def get_value(cls, name):
        return cls[name].value
    @classmethod
    def get_name(cls, value):
        return cls(value).name
    
@unique
class Role(Enum):
    server = '服务器'
    user = '用户'
    assistant = '星尘小助手'
    system = '系统'
    @classmethod
    def names(cls):
        return [c.name for c in cls]
    @classmethod
    def values(cls):
        return [c.value for c in cls]
    
@unique
class MediaType(Enum):
    image = 'image'
    audio = 'audio'
    video = 'video'
    
    
# @dataclass
class AppMessage(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        # allow_mutation = False
        extra = 'forbid'
        
    role: str # system/user/assistant
    content: str | None # text message displayed in the chat
    queue: deque | None # used to get streaming message from another thread
    thread: Thread | None # thread used to close when streaming is finished
    time: datetime # time created
    task: str | None # task type using Task, None for system message
    name: str # user name or model name
    suggestions: list[str] | None # suggestions for user to choose
    actions: dict[str, str] | None # actions for user to choose
    medias: list[UploadedFile] | None = None # media files kept in bytes, e.g. images, audio, video

    @validator('role', pre=True, always=True)
    def set_role(role:str):
        assert role in Role.names(), f'role {role} not in {Role.names()}'
        return role
    
    @validator('task', pre=True, always=True)
    def set_task(task:str):
        if task and task not in Task.names():
            logging.warning(f'task {task} not in {Task.names()}')
            task = Task.get_name(task)
        return task or None
           
    @validator('medias', pre=True, always=True)
    def set_medias(media_bytes_or_urls:list):
        if not media_bytes_or_urls:
            return None
        medias = []
        for m in media_bytes_or_urls:
            if isinstance(m, str):
                # url, download to local file
                if m.startswith('http'):
                    data = requests.get(m).content
                elif os.path.exists(m):
                    data = open(m, 'rb').read()
                else:
                    raise Exception(f'Unknown media url: {m}')
                filename = m.split('/')[-1]
                # filepath = chat_model.allocate_file_path(filename)
                rec = UploadedFileRec(
                    file_id=filename,
                    name=filename,
                    type=filename.split('.')[-1],
                    data=data,
                )
                medias.append(UploadedFile(rec, m))
            elif isinstance(m, UploadedFile):
                medias.append(m)
            elif isinstance(m, BytesIO):
                raise NotImplementedError('BytesIO not implemented yet')
            else:
                raise Exception(f'Unknown media type: {type(m)}')
        return medias or None
    
    @validator('suggestions', pre=True, always=True)
    def set_suggestions(suggestions:list[str]|str):
        if isinstance(suggestions, str) and suggestions:
            suggestions = eval(suggestions)
            assert isinstance(suggestions, list)
        return suggestions or None
    
    @validator('actions', pre=True, always=True)
    def set_actions(actions:list[str]|str):
        if isinstance(actions, str) and actions:
            actions = eval(actions)
            assert isinstance(actions, dict)
            for k, v in actions.items():
                assert v in ACTIONS
        return actions or None
    

if __name__ == '__main__':
    msg = AppMessage(
        role = 'user',
        content = 'hello',
        queue = None,
        time = datetime.now(),
        task = 'ChatGPT',
        name = 'user',
        suggestions = None,
        actions = None,
        medias = ['https://www.baidu.com/img/flexible/logo/pc/result.png'],
    )
    print(msg.medias)
    print(msg.dict())
    # print(msg.asdict()) # used for dataclass, not working for BaseModel
    