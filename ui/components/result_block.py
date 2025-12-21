import streamlit as st

def render_result_block(final: dict):
    st.success("🎉 Classificação concluída!")
    st.json(final)
