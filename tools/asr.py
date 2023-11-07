import openai
from . import utils, model
from retry import retry
import streamlit as st

accepted_types = ['wav', 'mp3', 'mp4', 'm4a', 'webm']
task_params = {
    model.Task.ASR.value: {
        'model': 'whisper-1',
        'url': 'https://api.openai.com/v1/engines/whisper-1/completions',
        'max_tokens': 244,
    },
}

@retry(tries=3, delay=1)
def transcript(audio_file, prompt=None):
    """Transcript audio file to text"""
    username = st.session_state.name
    openai.api_key = utils.get_openai_key(username)
    try:
        transcript = openai.Audio.transcribe("whisper-1", audio_file, prompt=prompt)
    except openai.error.InvalidRequestError as e:
        print(e)
        st.error(e)
    return transcript['text']