import markdown

with open('test/test.md', 'r') as f:
    text = f.read()

# 使用第一个markdown模块
html = markdown.markdown(text)

# 使用第二个markdown2模块
from markdown2 import markdown
html2 = markdown(text)

print(html)
print('-'*50)
print(html2)