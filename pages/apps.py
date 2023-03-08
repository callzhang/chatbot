import streamlit as st
from streamlit_card import card


st.set_page_config(page_title="精选AI应用", page_icon="⭐️", 
                   initial_sidebar_state="collapsed", 
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
with c2:
    card(
        title="DALL-E",
        text="图像生成，OpenAI官方应用",
        image="https://www.saashub.com/images/app/service_logos/166/9vp68kt2omnf/large.png?1609976439",
        url="https://labs.openai.com/",
    )
