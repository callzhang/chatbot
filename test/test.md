星尘小助手: 可以使用Python中的`markdown`和`markdown2`模块，它们都支持将Markdown格式转换为HTML格式。

``` python
import markdown
from markdown2 import markdown

text = '''
# This is a header
This is some **bold** text.
'''

# 使用第一个markdown模块
html = markdown.markdown(text)

# 使用第二个markdown2模块
html2 = markdown(text)

print(html)
print(html2)
```

代码中，我们分别使用`markdown.markdown(text)`和`markdown(text)`将Markdown格式的文本`text`转换为HTML格式的文本。注意，`markdown`模块转换的文本中，双下划线`__`和单下划线`_`被认为是下标和上标的标志，而不是加粗和斜体的标志，需要使用`<strong>`和`<em>`标签进行加粗和斜体的显示。

`markdown2`模块在此方面则更加灵活，会根据句子中的内容自动转换为对应的HTML标签。