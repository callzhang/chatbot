import streamlit as st
import json, os, time
import extra_streamlit_components as stx
from tools import utils, model, auth
from datetime import datetime, timedelta

st.title('秘钥输入')
st.write('请在下方输入秘钥，我们不会泄露你的秘钥，但是请注意不要泄露给他人')

if not st.session_state.get('name'):
    st.warning('请先登录再输入秘钥')
    cm = stx.CookieManager()
    st.json(cm.get_all(), expanded=False)
    st.stop()
    
    
openai_key_file = f'secrets/{st.session_state.name}/openai_key.json'
bing_key_file = f'secrets/{st.session_state.name}/bing_key.json'

openai_tab, bing_tab = st.tabs(['OpenAI', 'BingAI'])
with openai_tab:
    st.info('可以使用自己的OpenAI的秘钥，调用方法为官方，不会封号，请放心使用😊')
    st.checkbox('OpenAI秘钥已保存', value=os.path.exists(openai_key_file), disabled=True)
    openai_key = ''
    if os.path.exists(openai_key_file):
        openai_key = auth.get_openai_key(st.session_state.name)
    openai_key = st.text_input('请输入OpenAI的秘钥', type='password', 
                               placeholder='sk-*******', value=openai_key, 
                               help='从[这个](https://beta.openai.com/account/api-keys)页面获取秘钥')
    if st.button('保存', key='save_openai_key'):
        auth.get_openai_key.clear_cache()
        if not openai_key and os.path.exists(openai_key_file):
            # 清除秘钥
            os.remove(openai_key_file)
            st.success('秘钥已清除')
        else:
            os.makedirs(f'secrets/{st.session_state.name}', exist_ok=True)
            st.session_state.openai_key = openai_key
            key_json = {
                'openai_key': openai_key
            }
            json.dump(key_json, open(openai_key_file, 'w'))
            st.success('秘钥已保存')
            time.sleep(1)
        st.rerun()
    
        
with bing_tab:
    st.warning('BingAI调用方法非官方，可能会导致问题，请酌情使用。申请BingAI，请先将小猫咪设置为全局模式，并选择“英国”等非亚洲国家，进入bing.com时需要清空cookies。')
    st.checkbox('BingAI秘钥已保存', value=os.path.exists(bing_key_file), disabled=True)
    bing_instruction = '''### Checking access (Required)
- Install the latest version of Microsoft Edge
- Open http://bing.com/chat
- If you see a chat feature, you are good to go
### Getting authentication (Required)
- Install the cookie editor extension for [Chrome](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) or [Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/)
- Go to `bing.com`
- Open the extension
- Click "Export" on the bottom right (This saves your cookies to clipboard)
- Paste your cookies below
    '''
    # st.markdown(bing_instruction)
    cookie_template = '''[
    {
        "domain": ".bing.com",
        "expirationDate": 1710652153.409955,
        "hostOnly": false,
        "httpOnly": false,
        "name": "SnrOvr",
        "path": "/",
        "sameSite": "no_restriction",
        "secure": true,
        "session": false,
        "storeId": null,
        "value": "X=rebateson"
    },...
    '''
    bingai_cookies = auth.get_bingai_key(st.session_state.name)
    bingai_cookies = st.text_area('请输入BingAI的cookies', placeholder=cookie_template,
                                  height=200, value=bingai_cookies, 
                                  help=bing_instruction)
    if bingai_cookies and st.button('保存', key='save_bingai_key'):
        os.makedirs(f'secrets/{st.session_state.name}', exist_ok=True)
        # print(bingai_cookies)
        # json.dump(bingai_cookies, open(bing_key_file, 'w'), indent=4)
        try:
            json.loads(bingai_cookies)
        except:
            st.error('cookies格式错误，请检查是否为json格式')
            st.stop()
        with open(bing_key_file, 'w') as f:
            f.write(bingai_cookies)
        utils.get_bingai_key.clear_cache()
        st.success('BingAI cookies已保存')
        time.sleep(1)
        st.rerun()

# log out
cm = stx.CookieManager()
if st.button('退出登录'):
    cm.delete(model.LOGIN_CODE)
    del st.session_state.name
    del st.session_state.conversation
    st.rerun()


# admin panel
admins = auth.get_admin_db().index
if st.session_state.name in admins:
    st.subheader('Admin panel')
    st.checkbox(st.session_state.name, True, disabled=True)
    add_user_tab, edit_user_tab, all_users_tab = st.tabs(['添加用户', '编辑用户', '用户列表'])
    with add_user_tab:
        username = st.text_input('用户名')
        code = st.text_input('访问码')
        expiration = st.date_input('截止日期', value=datetime.now()+timedelta(days=360))
        if st.button('添加用户'):
            if auth.add_user(username, code, expiration):
                st.success('用户添加成功')
            else:
                st.error('用户添加失败')
            
    with edit_user_tab:
        db = auth.get_user_db()
        # task
        tasks = model.Task.values()
        columns = db.columns[2:].to_list()
        assert all([t in columns for t in tasks])
        c1, c2, c3 = st.columns(3)
        with c1:
            username_pl = st.empty()
            username = username_pl.selectbox('用户名', db.index)
            info = db.loc[username]
        with c2:
            code = st.text_input('新访问码, 留空不更新', key=f'{username}_code')
        with c3:
            exp_date = st.date_input(
                '新截止日期', value=info['截止日期'], key=f'{username}_exp_date')
        
        task_val = []
        for col, task in zip(st.columns(len(columns)), columns):
            with col:
                val = info[task] == 'TRUE' or info[task] is True
                checked = st.checkbox(task, value=val, key=f'{username}_{task}_checkbox')
                task_val.append(checked)
            
        if st.button('更新用户'):
            rows = [code, exp_date] + task_val
            if not code:
                code = info['访问码']
            if code in db.index:
                st.error('访问码不安全，请重新输入')
            elif auth.update_user(username, rows):
                st.success('用户更新成功')
            else:
                st.error('用户更新失败')
        
        if st.button('删除用户'):
            if auth.delete_user(username):
                st.success('用户删除成功')
                username_pl.selectbox('用户名', db.index)
            else:
                st.error('用户删除失败')
        
        
                
                                
    with all_users_tab:
        db = auth.get_user_db()
        st.dataframe(db.drop(columns=['访问码']), use_container_width=True)
