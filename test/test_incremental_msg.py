
import streamlit as st
from streamlit_chat import message
from test_chat import show_message
import multiprocessing as mp
import time
    
message('你好啊', is_user=True, key='1')
message('你好，很高兴认识你', is_user=False, key='2')
message('你是谁？', is_user=True, key='3')

if 'streaming' not in st.session_state:
    st.session_state.streaming = False
if 'q' not in st.session_state:
    st.session_state.q = mp.Queue()
if 'text' not in st.session_state:
    st.session_state.text = ''

if st.button('显示文本'):
    st.session_state.streaming = True
    show_message(st.session_state.q)

while st.session_state.streaming:
    time.sleep(0.1)
    data = st.session_state.q.get()
    print(data, end='')
    if '[DONE]' in data:
        st.session_state.streaming = False
        message(st.session_state.text, key='active')
        st.session_state.text = ''
    else:
        st.session_state.text += data
        message(st.session_state.text, key='active')
        st.experimental_rerun()




# import numpy as np
# progress_bar = st.progress(0)
# status_text = st.empty()
# chart = st.line_chart(np.random.randn(10, 2))

# for i in range(100):
#     # Update progress bar.
#     progress_bar.progress(i + 1)

#     new_rows = np.random.randn(10, 2)

#     # Update status text.
#     status_text.text(
#         'The latest random number is: %s' % new_rows[-1, 1])

#     # Append data to the chart.
#     chart.add_rows(new_rows)

#     # Pretend we're doing some computation that takes time.
#     time.sleep(0.1)

# status_text.text('Done!')
# st.balloons()
