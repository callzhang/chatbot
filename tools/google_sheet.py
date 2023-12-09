import json
import streamlit as st
from gspread_pandas import Spread, Client
from . import utils


key = json.loads(st.secrets.gsecret.replace("'", '"'))

@utils.cached(timeout=7200)
def init_client():
    msg = st.toast('正在连接数据库，请稍等...')
    client = Client(config=key)
    msg.toast('数据库连接成功！')
    return client
