import re, requests
import streamlit as st
from retry import retry
from . import utils, model

url = 'https://api.openai.com/v1/images/generations'
lab_url = 'https://labs.openai.com/'

# below are regex patterns to detect user intension to generate an image
keywords = [
    r'[作|张|副|生成](.*)的?图'
]

# image generation function
'''curl https://api.openai.com/v1/images/generations \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -d '{
  "prompt": "A cute baby sea otter",
  "n": 2,
  "size": "1024x1024"
}'
'''
@retry(tries=3, delay=1)
def gen_image(prompt):
    print(f'prompt: {prompt}')
    header = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {utils.get_openai_key(st.session_state.name, model.Task.text2img.name)}'
    }
    data = {
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024" #1024x1024
    }
    res = requests.post(url, headers=header, json=data).json()
    if 'error' in res:
        return res['error']['message']
    urls = [r['url'] for r in res['data']]
    # return markdown
    # return url2markdown(urls)
    return urls
    



