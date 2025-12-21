import streamlit as st

def render_logs_block(container, logs):
    container.write("### Logs")
    if not logs:
        container.write("Nenhum log ainda.")
    else:
        for log in logs:
            container.write(f"- {log}")
