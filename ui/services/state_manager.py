import streamlit as st


def init_session_state():
    defaults = {
        "descricao_evento": "",
        "state": {},
        "hitl_required": False,
        "hitl_metadata": None,
        "final": None,
        "logs": [],
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def clear_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
