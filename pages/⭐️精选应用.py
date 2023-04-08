import streamlit as st
from streamlit_card import card


st.set_page_config(page_title="精选AI应用", page_icon="⭐️", 
                   initial_sidebar_state="expanded",
                   menu_items={
                    'Get Help': 'https://stardust.ai',
                    'About': "# 精选AI应用. \n *欢迎体验*"
                })


st.header('⭐️精选AI应用')

c1, c2 = st.columns(2)
with c1:
    card(
        title="ChatPDF",
        text="用GPT来阅读PDF，交互式提问，生成答案",
        image="https://saifhassan.info/wp-content/uploads/2016/04/WhatsappPDF.png",
        url="https://www.chatpdf.com/",
    )
    card(
        title='文心一言',
        text='百度打造的AI对话语言大模型，支持中英文',
        url='https://yiyan.baidu.com/',
        image='https://pic2.zhimg.com/v2-20257813e0f5669f28aba3a588bf2e0d_r.jpg'
    )
    card(
        title='AssemblyAI',
        text='Conformer-1是一种最先进的语音识别模型，实现了接近人类水平的性能和鲁棒性。',
        url='https://www.assemblyai.com/playground/source',
        image='https://lh4.googleusercontent.com/pw6VHzWKgDZHeSMY2GKceYs3-xPyF4K4LVjgCSpm9wR2WOaki08jSGJtxdjr5Uh4UvwcuePl65_LXYDgSleBnVCojkGmApwZJCv7dW2Lj7gIbKza71jhlQdJgVDL2SJZ4nTaGZcfNsPISG8'
    )
with c2:
    card(
        title="DALL-E",
        text="图像生成，OpenAI官方应用",
        image="https://www.saashub.com/images/app/service_logos/166/9vp68kt2omnf/large.png?1609976439",
        url="https://labs.openai.com/",
    )
    card(
        title='CivitAI',
        text='Civitai is a platform for Stable Diffusion AI Art models.',
        url='https://civitai.com/',
        image='https://tengyart.ru/wp-content/uploads/2023/03/chto-takoe-civitai.jpg'
    )
    card(
        title='poe.com',
        text='Poe 是一个让你与各种人工智能机器人进行对话的应用，其中包括付费订阅机器人和免费机器人。',
        url='https://poe.com',
        image='https://www.ermalalibali.com/wp-content/uploads/2023/04/poe.com-logo.png'
    )