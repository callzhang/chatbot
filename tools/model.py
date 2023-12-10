
from enum import Enum, unique
# from collections import deque
from queue import Queue
from datetime import datetime, timedelta
from streamlit.runtime.uploaded_file_manager import UploadedFile, UploadedFileRec
import requests, os, logging, mimetypes, re
from pydantic.dataclasses import dataclass # not useful as it cannot check arbitrary types
from pydantic import BaseModel, validator
from .utils import parse_file_info, excel_num_to_datetime, endpoint, save_uri_to_oss
from dateutil.parser import parse

global username

FINISH_TOKEN = '[DONE]'
RETRY_ACTION = '[RETRY]'
MODIFY_ACTION = '[MODIFY]'
TTS = '[TTS]'
ACTIONS = [RETRY_ACTION, TTS]
TIMEOUT = 60
LOGIN_CODE = 'login_code'
SERVER_ERROR = '[SERVER_ERROR]'
TOOL_RESULT = '[TOOL_RESULT]'
STATUS = '[STATUS]'
HELP = '[HELP]'

@unique
class Task(Enum):
    # internal name : display name
    ChatSearch = '信息检索'
    ChatGPT = '对话'
    GPT4 = 'GPT4'
    GPT4V = 'GPT4V'
    BingAI = 'BingAI'
    text2img = '文字做图'
    ASR = '语音识别'
    TTS = '文本朗读'
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
    content: str | None # text message displayed in the chat, None when using text2img
    status: list[dict] = [] # status updates for searching or other actions
    time: datetime # time created
    task: str | None # task type using Task, None for system message
    name: str # user name or model name
    queue: Queue | None = None # used to get streaming message from another thread
    suggestions: list[str] | None = None # suggestions for user to choose
    actions: dict[str, str] | None = None # actions for user to choose
    medias: list[UploadedFile] | None = None # media files kept in bytes, e.g. images, audio, video
    functions: list[dict] = [] # functions to be executed, e.g. google search
    
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
    
    @validator('time', pre=True, always=True)
    def set_time(time):
        if not time:
            time = datetime.now()
        elif isinstance(time, str):
            time = parse(time)
        elif isinstance(time, float):
            time = excel_num_to_datetime(time)
        assert isinstance(time, datetime)
        return time
           
    @validator('medias', pre=True)
    def set_medias(media_object:list):
        if not media_object:
            return None
        medias = []
        if isinstance(media_object, str):
            if '=IMAGE(' in media_object:
                media_list = re.findall(r'=IMAGE\("(.*)"\)', media_object)
            else:
                try:
                    media_list = eval(media_object)
                    assert isinstance(media_list, list)
                except Exception as e:
                    print(f'failed to eval media string: {media_object}')
                    media_list = []
        elif isinstance(media_object, list):
            media_list = media_object
        elif isinstance(media_object, UploadedFile):
            assert media_object.type, 'file_type not set'
            media_list = [media_object]
        else:
            raise Exception(f'Unknown media type: {type(m)}')
        
        # upload media to OSS
        for m in media_list:
            if isinstance(m, str):
                # url, download to local file
                url = m
                if url.startswith('http'):
                    if endpoint in url:  # already on OSS
                        res = requests.get(url)
                        if res.ok:
                            data = res.content
                            url = url
                        else:
                            print(f'Unable to download url: {m}')
                            continue
                    else: # upload to oss
                        url, data = save_uri_to_oss(url)
                else:
                    raise Exception(f'Unknown media url or file not found: {m}')
                filename, filetype = parse_file_info(m)
                rec = UploadedFileRec(
                    file_id=m,
                    name=filename,
                    type=filetype,
                    data=data,
                )
                medias.append(UploadedFile(rec, url))
            elif isinstance(m, UploadedFile):
                if not m._file_urls:
                    url, data = save_uri_to_oss(m)
                    m._file_urls = url
                medias.append(m)
            else:
                raise Exception(f'Unknown media: {m}')
        return medias or None
    
    @validator('suggestions', pre=True)
    def set_suggestions(suggestions:list[str]|str):
        if isinstance(suggestions, str) and suggestions:
            suggestions = eval(suggestions)
            assert isinstance(suggestions, list)
        return suggestions or None
    
    @validator('actions', pre=True)
    def set_actions(actions:list[str]|str):
        if isinstance(actions, str) and actions:
            actions = eval(actions)
            assert isinstance(actions, dict)
            for k, v in actions.items():
                assert k in ACTIONS
        return actions or None
    
    @validator('status', pre=True)
    def set_status(status_list: list):
        if not status_list:
            return []
        if isinstance(status_list, str):
            _status_list = eval(status_list)
            assert isinstance(_status_list, list)
            status_list = []
            for s in _status_list:
                if isinstance(s, str):
                    status_list.append({STATUS: s})
                elif isinstance(s, dict):
                    status_list.append(s)
                else:
                    raise NotImplementedError
        if isinstance(status_list, list):
            assert all(isinstance(s, dict) for s in status_list)
            return status_list
        else:
            raise ValueError(status_list)


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
    