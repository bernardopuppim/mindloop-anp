import streamlit as st

def render_history_block(hist):
    st.subheader("🧭 Caminho percorrido (histórico)")
    if not hist:
        st.info("Nenhum histórico disponível.")
        return
    st.json(hist)
