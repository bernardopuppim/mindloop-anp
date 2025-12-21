import streamlit as st

def render_hitl_block(meta: dict):
    st.subheader("🧑‍⚖️ Intervenção Humana (HITL) Necessária")

    st.markdown(f"**Nó atual:** `{meta['node_id']}`")
    st.markdown(f"**Pergunta:** {meta['pergunta']}")
    st.markdown(f"**Entropia local:** `{meta['entropia_local']:.3f}`")
    st.write("---")

    children = meta["children"]

    st.markdown("### Escolha um dos caminhos sugeridos:")

    cols = st.columns(len(children))

    for idx, c in enumerate(children):
        with cols[idx]:
            st.markdown(f"**Filho `{c['id']}`**")
            st.markdown(f"- Score: `{c['score']:.3f}`")
            st.markdown(f"- Prob: `{c['prob']:.3f}`")
            if st.button(f"Selecionar {c['id']}", key=f"hitl_btn_{idx}"):
                st.session_state.selected_child = c["id"]

    if "selected_child" in st.session_state:
        st.text_area("Justificativa humana (opcional):", key="hitl_justification")

        if st.button("📤 Enviar decisão"):
            from services.run_engine import continuar_pos_hitl

            result = continuar_pos_hitl(
                st.session_state.state,
                st.session_state.selected_child,
                st.session_state.get("hitl_justification"),
            )

            st.session_state.state = result["state"]
            st.session_state.hitl_required = result["hitl_required"]
            st.session_state.hitl_metadata = result["hitl_metadata"]
            st.session_state.final = result["final"]

            del st.session_state["selected_child"]
            if "hitl_justification" in st.session_state:
                del st.session_state["hitl_justification"]

            st.rerun()
