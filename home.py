from st_pages import Page, show_pages, add_page_title
import streamlit as st
import sys, subprocess, datetime
import sentry_sdk

# error handling
runner = sys.modules["streamlit.runtime.scriptrunner.script_runner"]
original_handler = runner.handle_uncaught_app_exception
try:
    release = subprocess.check_output(["git", "describe", "--always"]).strip().decode()
except:
    release = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

sentry_sdk.init(
    dsn="https://0e9ffdaf583b7b632cb67ade01839227@o200299.ingest.sentry.io/4506365834035200",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,  
    # Enable performance monitoring
    enable_tracing=True,
    # get git commit hash
    release=release
)


def sentry_handler(exception: Exception) -> None:
    """Pass the provided exception through to sentry."""
    sentry_sdk.capture_exception(exception)
    return original_handler(exception)


if original_handler != sentry_handler:
    print('---> add exception handler with sentry_handler')
    runner.handle_uncaught_app_exception = sentry_handler

add_page_title()
pages = [
        Page("chatbot.py", "星尘小助手", "💬"),
        Page("pages/⭐️精选应用.py", "精选应用", ":star:"),
        # Section("My section", icon="🎈️"),
        Page("pages/📒聊天历史.py", icon="📒"),
        Page("pages/㊙️秘钥管理.py", icon="㊙️"),
    ]

if st.secrets.debug:
    pages.append(Page("pages/🤗助理.py", icon="🤗"))
show_pages(pages)