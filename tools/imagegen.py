import re, requests
import streamlit as st
from retry import retry

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
        'Authorization': f'Bearer {st.secrets.key}'
    }
    data = {
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024" #1024x1024
    }
    res = requests.post(url, headers=header, json=data)
    urls = [r['url'] for r in res.json()['data']]
    return url2markdown(urls)


# utls to markdown
def url2markdown(urls):
    md_formated = ""
    for i, url in enumerate(urls):
        md_formated += f"""![图{i+1}]({url})\n\n"""
    # print(f'md_formated: {md_formated}')
    return md_formated
