import openai
from retry import retry
import streamlit as st

openai.api_key = st.secrets.key
accepted_types = ['wav', 'mp3', 'mp4', 'm4a', 'webm']

@retry(tries=3, delay=1)
def transcript(audio_file):
    """Transcript audio file to text"""
    try:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    except openai.error.InvalidRequestError as e:
        print(e)
        st.error(e)
    return transcript['text']