import streamlit as st
# from streamlit_chat import message
from tools import dialog, utils, controller, model, auth, speech
from streamlit_extras.buy_me_a_coffee import button
import extra_streamlit_components as stx
import sys
runner = sys.modules["streamlit.runtime.scriptrunner.script_runner"]

# 初始化
Task = model.Task
Role = model.Role
Message = model.Message
WIDE_LAYOUT_THRESHOLD = 1000
try:
    if 'desired_layout' not in st.session_state:
        st.session_state.desired_layout = 'centered'
    st.set_page_config(page_title="💬星尘小助手", page_icon="💬",
                    layout=st.session_state.desired_layout,
                    initial_sidebar_state="auto", menu_items={
                'Get Help': 'https://stardust.ai',
                #  'Report a bug': "https://www.extremelycoolapp.com/bug",
                'About': "# 星尘小助手. \n *仅限员工使用，请勿外传!*"
        })
except:
    pass
st.title("💬星尘小助手") 
    
# user auth
if 'name' not in st.session_state:
    st.session_state.guest = True
    cm = stx.CookieManager()
    code = cm.get(model.LOGIN_CODE)
    
    # 通知
    with open('README.md', 'r') as f:
        readme = f.read()
        st.toast(readme, icon='😍')
        
    # 登录
    if not code:
        st.info('我是一个集成多个聊天机器人能力的小助手，希望能帮助你提高工作效率😊')
        code = st.text_input('请输入你的访问码', help='仅限员工使用，请勿外传！')
    if code:
        username, exp_date, authenticated = auth.validate_code(code)
        st.session_state.guest = not authenticated
        st.session_state.name = username
        cm.set(model.LOGIN_CODE, code, expires_at=exp_date)
        st.rerun()
    st.stop()
    
## dialog history management
dialog.init_dialog_history(st.session_state.name)

##---- UI -----
task = st.selectbox('选择功能', Task.values(), key='task', label_visibility='collapsed')
# 聊天历史列表
def on_conversation_change():
    del st.session_state.conversation
dialog_index = st.session_state.dialog_history.index(st.session_state.selected_title)
st.session_state.selected_title = st.sidebar.radio('聊天历史', 
                                  st.session_state.dialog_history, 
                                  index=dialog_index,
                                  key='chat_title_selection', 
                                  on_change=on_conversation_change)

if st.session_state.guest:
    st.info('访客模式：支持最大10轮对话和20轮聊天历史')

# 添加文本输入框
task_info = auth.user_task_list(st.session_state.name)
enabled = task_info[task]
label = None
max_chars = controller.task_params[task][task]['max_tokens']
if st.session_state.guest and len(st.session_state.conversation) > 10:
    enabled, help = False, '访客不支持长对话，请联系管理员'
elif task == Task.ChatGPT.value:
    help = '输入你的问题，然后按回车提交。'
elif task == Task.ChatSearch.value:
    help = '输入你的问题，按需调用搜索引擎。'
elif task == Task.GPT4.value:
    help = '输入你的问题，然后按回车提交。'
elif task == Task.GPT4V.value:
    help = '输入你的问题，并上传图片，然后按回车提交。'
    label = '🎨上传图片'
    filetypes = controller.openai_image_types
elif task == Task.text2img.value:
    help = '访客不支持文字做图' if st.session_state.guest else '输入你的prompt'
elif task == Task.ASR.value:
    label = '🎤上传语音文件'
    filetypes = controller.speech_media_types
    help = '访客不支持语音识别' if st.session_state.guest else '上传语音文件'
elif task == Task.TTS.value:
    help = '访客不支持文本朗读' if st.session_state.guest else '输入需要朗读的文本'
else:
    raise NotImplementedError(task)

# 文件上传
if label:
    attachment = st.file_uploader(
        label, type=filetypes, key='attachment', disabled=not enabled)
# chat input
user_input = st.chat_input(placeholder=help,
                           key='input_text',
                           disabled=not enabled,
                           max_chars=max_chars,
                           )
if user_input:
    user_message, bot_response = controller.gen_response(user_input)
    
# 显示对话内容
for i, message in enumerate(st.session_state.conversation):
    role, content, medias =  message.role, message.content, message.medias
    message_placeholder = None
    if role == Role.system.name:
        pass
    elif role == Role.server.name:# not implemented
        message_placeholder = st.chat_message(role)
        message_placeholder.markdown(content)
    elif role == Role.user.name:
        message_placeholder = st.chat_message(role)
        if medias:
            for media in medias:
                controller.display_media(media, container=message_placeholder)
        if content:
            message_placeholder.markdown(content)
    elif role == Role.assistant.name:
        message_placeholder =  st.chat_message(role)
        controller.show_streaming_message(message, message_placeholder)
    else:
        raise Exception(f'Unknown role: {role}')
    
    # action
    if message_placeholder:
        controller.show_actions(message, message_placeholder)

    # page layout
    if st.session_state.desired_layout != 'wide' and message.role=='assistant' and utils.token_size(message.content) > WIDE_LAYOUT_THRESHOLD:
        st.session_state.desired_layout = 'wide'
        st.rerun()


## 聊天历史功能区
c1, c2, c3, c4 = st.sidebar.columns(4)
with c1: # 新对话
    if st.session_state.guest and len(st.session_state.dialog_history) >= 5:
        disabled, help = True, '访客不支持超过10轮对话，请联系管理员'
    else:
        disabled, help = False, '新对话'
    if st.button('➕', help=help, disabled=disabled):
        del st.session_state.conversation
        title = dialog.new_dialog(st.session_state.name)
        st.session_state.new_title = title
        st.session_state.audio = None
        st.rerun()
with c2: # 删除
    if st.button('⛔', help='删除当前聊天记录', disabled=st.session_state.guest):
        del st.session_state.conversation
        dialog.delete_dialog(st.session_state.name, st.session_state.selected_title)
        st.rerun()
with c3: # 导出
    if st.download_button(label='📤', help='导出对话',
                        data=dialog.conversation2markdown(st.session_state.conversation, st.session_state.name), 
                        file_name=f'history.md',
                        mime='text/markdown'):
        st.success('导出成功！')
with c4: # 修改
    def update_title():
        new_title = st.session_state.new_title_text
        if new_title in st.session_state.dialog_history:
            new_title += '(1)'
        dialog.edit_dialog_name(st.session_state.name, st.session_state.selected_title, new_title)
        st.session_state.new_title = new_title
    if st.button('✏️', help='修改对话名称'):
        new_title = st.sidebar.text_input('修改名称', st.session_state.selected_title, help='修改当前对话标题', key='new_title_text', on_change=update_title)
        
        
from streamlit_extras.add_vertical_space import add_vertical_space
from tools import components
# buy me a coffee
with st.sidebar:
    components.display_sentry_feedback()
    # button(username="derekz", floating=False, width=221)

