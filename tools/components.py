

# my_component.py
import streamlit.components.v1 as components
import streamlit as st
if 'name' not in st.session_state:
    st.session_state.name = 'guest'
# Define the component.
content = f"""
<head>
<script
src="https://browser.sentry-cdn.com/7.86.0/bundle.tracing.replay.feedback.min.js"
integrity="sha384-3fKC3KsdiRT07aZV/LVMHsU+/udUHP5F6rc26UkHNwWVOa5locnNhI6uFb+N/FYK"
crossorigin="anonymous"
></script>
</head>
<body>
<script>
    Sentry.init({{
    dsn: "https://0e9ffdaf583b7b632cb67ade01839227@o200299.ingest.sentry.io/4506365834035200",

    integrations: [
        new Sentry.Feedback({{
        // Additional SDK configuration goes in here, for example:
        // colorScheme: "light",
        showName: false,
        showEmail: false,
        buttonLabel: "提交反馈",
        // useSentryUser" {{ username: {st.session_state.name} }}
        }}),
    ],
    }});
    Sentry.setUser({{ 
        username: "{st.session_state.name}",
        ip_address: "{{{{auto}}}}",
    }});
</script>
</body>
"""
def display_sentry_feedback():
    components.html(
        content,
        height=300,
    )

if __name__ == "__main__":
    display_sentry_feedback()