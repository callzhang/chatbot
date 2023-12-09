

# my_component.py
import streamlit.components.v1 as components

# Define the component.

def display_sentry():
    components.html(
        """
<head>
<script
src="https://browser.sentry-cdn.com/7.86.0/bundle.tracing.replay.feedback.min.js"
integrity="sha384-3fKC3KsdiRT07aZV/LVMHsU+/udUHP5F6rc26UkHNwWVOa5locnNhI6uFb+N/FYK"
crossorigin="anonymous"
></script>
</head>
<body>
<script>
    Sentry.init({
    dsn: "https://28eb6ea304b24c41a6ea6883121fe62f@o200299.ingest.sentry.io/1364811",

    integrations: [
        new Sentry.Feedback({
        // Additional SDK configuration goes in here, for example:
        // colorScheme: "light",
        }),
    ],
    });
</script>
</body>
        """,
        height=600,
    )

display_sentry()