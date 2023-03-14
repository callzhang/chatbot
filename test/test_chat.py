
import streamlit as st
from streamlit_chat import message
import time, threading, random


def show_message(queue):
    threading.Thread(target=gen_response, args=(queue,)).start()


def gen_response(queue):
    text = """ 你可以使用Python中的库，例如`markdown2`，将Markdown格式的文本转换成HTML格式，并保留代码块的格式标记。以下是一个例子：
```python
import markdown2
markdown_text = '''
# Heading H1
## Heading H2
This is a paragraph.
```python
def my_function():
    print("Hello, world!")
```
This is another paragraph.
'''
html_text = markdown2.markdown(markdown_text)
print(html_text)
```
输出：
```html
<h1>Heading H1</h1>
<h2>Heading H2</h2>
<p>This is a paragraph.</p>
<pre><code class="language-python">def my_function():
    print("Hello, world!")
</code></pre>
<p>This is another paragraph.</p>
```
你需要安装`markdown2`库，你可以使用以下命令进行安装：
```python
!pip install markdown2
```
"""
    for t in text.split(' '):
        # print(t, end='')
        queue.put(t+' ')
        time.sleep(random.random()*0.1)
    queue.put('[DONE]')
