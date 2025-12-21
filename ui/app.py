# ui/app.py

import streamlit as st
from typing import Dict, Any

from services.run_engine import executar_primeira_fase, executar_pos_hitl
from lats_sistema.lats.tree_loader import NODE_INDEX


# -------------------------------------------------------
# Configuração da página
# -------------------------------------------------------
st.set_page_config(
    page_title="Classificador SMS (LATS-P + HITL)",
    layout="wide",
)

# CSS para cards e "popup" de HITL
st.markdown(
    """
    <style>
    .hitl-banner {
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
        border-radius: 12px;
        background-color: #f5f7ff;
        border: 1px solid #d0d7ff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .hitl-cards-row {
        display: flex;
        gap: 1rem;
        margin-top: 0.75rem;
        margin-bottom: 0.75rem;
    }
    .hitl-card {
        flex: 1;
        padding: 0.75rem 0.9rem;
        border-radius: 10px;
        border: 1px solid #dcdcdc;
        background-color: #ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        font-size: 0.9rem;
    }
    .hitl-card-best {
        border: 2px solid #3b82f6;  /* azul destaque para top1 */
    }
    .hitl-card-selected {
        border: 2px solid #16a34a;  /* verde quando usuário seleciona */
        background-color: #ecfdf3;
    }
    .hitl-card-title {
        font-weight: 600;
        margin-bottom: 0.35rem;
    }
    .hitl-card-just {
        font-size: 0.85rem;
        color: #374151;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛠️ Classificador de Eventos SMS — LATS-P + HITL")


# -------------------------------------------------------
# Estado global da sessão (Streamlit)
# -------------------------------------------------------
if "lats_state" not in st.session_state:
    st.session_state.lats_state = None

# usado para controlar auto-preenchimento da justificativa do HITL
if "hitl_justificativa_source" not in st.session_state:
    st.session_state.hitl_justificativa_source = None


# -------------------------------------------------------
# Entrada do usuário
# -------------------------------------------------------
st.subheader("1️⃣ Descrição do evento")

descricao = st.text_area(
    "Cole abaixo a descrição textual do evento:",
    height=180,
    placeholder="Exemplo: Durante atividade de manutenção preventiva...",
)

col1, col2 = st.columns([1, 2])

with col1:
    if st.button("🚀 Classificar evento", type="primary"):
        if not descricao.strip():
            st.warning("Por favor, preencha a descrição do evento antes de classificar.")
        else:
            # Reseta estado anterior
            st.session_state.lats_state = None

            with st.spinner("Rodando RAG + LATS-P..."):
                state = executar_primeira_fase(descricao)

            st.session_state.lats_state = state
            st.success("Primeira fase concluída.")
            st.rerun()


# -------------------------------------------------------
# Sidebar com métricas
# -------------------------------------------------------
with st.sidebar:
    st.header("📊 Métricas do processo")

    state_sidebar = st.session_state.lats_state

    if state_sidebar is not None:

        final_sb = state_sidebar.get("final")
        historico_sb = final_sb.get("historico", []) if final_sb else []

        # Passos / profundidade
        passos = len(historico_sb)
        st.metric("Passos executados", passos)
        st.metric("Profundidade final", passos if final_sb else "—")

        # Número de HITLs
        logs_sb = state_sidebar.get("logs", [])
        num_hitl = sum(1 for l in logs_sb if "HITL" in l)
        st.metric("HITLs acionados", num_hitl)

        # Entropia média
        entropias = []
        for hstep in historico_sb:
            children = hstep.get("children")
            if children:
                probs = [c.get("prob") for c in children if c.get("prob") is not None]
                if probs:
                    import math
                    ent = -sum(p * math.log2(p) for p in probs if p and p > 0)
                    entropias.append(ent)

        if entropias:
            import numpy as np
            st.metric("Entropia média", f"{np.mean(entropias):.3f}")
        else:
            st.metric("Entropia média", "—")

        # Classe final sugerida
        if final_sb:
            node_id_sb = final_sb["node_id"]
            node_sb = NODE_INDEX.get(node_id_sb, {})
            classe_sb = node_sb.get("classe", "N/D")
            st.write("### Classe sugerida")
            st.code(classe_sb)

        # Classe corrigida pelo humano
        vf = state_sidebar.get("validacao_final")
        if vf and vf.get("status") == "corrigido":
            classe_corrigida = vf.get("classe_corrigida_humano", "—")
            st.write("### Classe corrigida pelo humano")
            st.code(classe_corrigida)

    else:
        st.info("Execute uma classificação para ver métricas.")


# -------------------------------------------------------
# Função auxiliar para exibir resultado final
# -------------------------------------------------------
def mostrar_resultado_final(state: Dict[str, Any]) -> None:
    final = state.get("final")
    if not final:
        st.info("Ainda não há resultado final disponível.")
        return

    node_id = final["node_id"]
    node = NODE_INDEX.get(node_id, {})

    classe_final = node.get("classe", "Classe_indefinida")

    st.subheader("4️⃣ Resultado da classificação")

    st.markdown(f"**Classe final sugerida:** `{classe_final}`")
    st.markdown(f"**Nó final:** `{node_id}`")

    # Caminho percorrido
    historico = final.get("historico", [])
    if historico:
        with st.expander("Ver caminho percorrido (histórico LATS)", expanded=False):
            for passo in historico:
                nid = passo["node_id"]
                filho_escolhido = passo.get("chosen_child")
                score = passo.get("chosen_score")
                prob = passo.get("chosen_prob")

                nodo = NODE_INDEX.get(nid, {})
                pergunta = nodo.get("pergunta", "")

                st.markdown(
                    f"- **{nid}** — {pergunta}\n"
                    f"    → filho escolhido: `{filho_escolhido}` "
                    f"(score={score:.3f} | prob={prob:.3f})"
                )


# -------------------------------------------------------
# ESTADO ATUAL DO ENGINE
# -------------------------------------------------------
state = st.session_state.lats_state

if state is None:
    st.stop()  # não continua a renderização se ainda não rodou nada


# ======================================================
# 2️⃣ HITL INTERMEDIÁRIO — modal com UX avançado
# ======================================================
state = st.session_state.lats_state

if state and state.get("hitl_required"):

    meta = state["hitl_metadata"]
    children = meta["children"]

    # Ordenar pelos melhores candidatos
    children_sorted = sorted(children, key=lambda c: c["prob"], reverse=True)
    top_children = children_sorted[:3]

    # controle interno para atualizar preenchimento automático
    if "hitl_selected_index" not in st.session_state:
        st.session_state.hitl_selected_index = 0
    if "hitl_auto_just" not in st.session_state:
        st.session_state.hitl_auto_just = ""

    @st.dialog("🔎 Revisão humana necessária (HITL)")
    def hitl_modal():

        st.markdown(f"**Nó atual:** `{meta['node_id']}`")
        st.markdown(f"**Pergunta:** {meta.get('pergunta')}")
        st.markdown(f"**Entropia:** `{meta.get('entropia_local'):.3f}`")

        st.write("### Opções avaliadas (Top-3 mais prováveis)")

        # --- RADIO COM APENAS TOP 3 ---
        selected_idx = st.radio(
            "Selecione a opção correta:",
            options=list(range(len(top_children))),
            format_func=lambda i: f"Opção {i+1}",
            key="hitl_choice_radio",
            horizontal=True,
        )

        # Atualizar justificativa automática
        selected_child = top_children[selected_idx]
        modelo_just = selected_child.get("justificativa", "")

        if st.session_state.hitl_selected_index != selected_idx:
            st.session_state.hitl_selected_index = selected_idx
            st.session_state.hitl_auto_just = modelo_just

        # ---- CSS dos cards ----
        st.markdown("""
            <style>
            .hitl-row { display: flex; gap: 1rem; margin-top: 1rem; }
            .hitl-card {
                flex: 1;
                padding: 0.9rem;
                border-radius: 10px;
                border: 1px solid #dcdcdc;
                background: white;
                box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            }
            .hitl-best { border: 2px solid #3b82f6; }
            .hitl-selected { border: 2px solid #16a34a; background: #ecfdf3; }
            .hitl-title { font-weight: 600; margin-bottom: 0.3rem; }
            .hitl-just { font-size: 0.85rem; color: #374151; }
            </style>
        """, unsafe_allow_html=True)

        # ---- CARDS LADO A LADO ----
        st.markdown('<div class="hitl-row">', unsafe_allow_html=True)

        for i, c in enumerate(top_children):

            filho = c["id"]
            nodo = NODE_INDEX.get(filho, {})
            pergunta = nodo.get("pergunta", "(sem texto)")
            justificativa = c.get("justificativa", "")

            classes = "hitl-card"
            if i == 0:
                classes += " hitl-best"
            if i == selected_idx:
                classes += " hitl-selected"

            st.markdown(
                f"""
                <div class="{classes}">
                    <div class="hitl-title">Opção {i+1} — {filho}</div>
                    <div><strong>Pergunta do nó:</strong> {pergunta}</div>
                    <div class="hitl-just">
                        <strong>Justificativa do modelo:</strong><br>{justificativa}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # --- JUSTIFICATIVA HUMANA ----
        justificativa_humana = st.text_area(
            "Justificativa humana (opcional):",
            value=st.session_state.hitl_auto_just,
            key="hitl_user_just",
            height=120,
        )

        # --- BOTÃO CONFIRMAR ---
        if st.button("✔️ Confirmar decisão e continuar"):
            filho_escolhido = selected_child["id"]

            novo_state = executar_pos_hitl(
                state,
                child_id=filho_escolhido,
                justificativa=justificativa_humana,
            )

            st.session_state.lats_state = novo_state
            st.rerun()

    hitl_modal()



# ======================================================
# 3️⃣ HITL FINAL — modal refinado
# ======================================================
elif state and state.get("hitl_final_required"):

    final = state["final"]
    node_id = final["node_id"]
    classe_final = NODE_INDEX.get(node_id, {}).get("classe", "Classe_indefinida")

    @st.dialog("📝 Validação Final da Classificação")
    def hitl_final_modal():

        st.markdown(f"**Classe sugerida:** `{classe_final}`")

        escolha = st.radio(
            "Você concorda com a classificação?",
            ["Sim", "Não"],
            key="hitl_final_decision",
            horizontal=True,
        )

        justificativa = st.text_area(
            "Justificativa (opcional):",
            key="hitl_final_justificativa",
            height=120,
        )

        classe_corrigida = None
        if escolha == "Não":
            classe_corrigida = st.selectbox(
                "Selecione a classe correta:",
                ["Classe 1", "Classe 2", "Classe 3", "Classe 4", "Classe 5"],
                key="hitl_final_corrigida",
            )

        if st.button("📌 Registrar"):
            novo_state = executar_pos_hitl(
                state,
                child_id=None,
                justificativa=justificativa,
                final_correto=(escolha == "Sim"),
                classe_corrigida=classe_corrigida,
            )
            st.session_state.lats_state = novo_state
            st.rerun()

    hitl_final_modal()



# ======================================================
# 4️⃣ Caso nenhum HITL esteja pendente, mostrar resultado final
# ======================================================
else:
    mostrar_resultado_final(state)

    # Logs internos
    with st.expander("🧪 Logs internos do engine", expanded=False):
        for linha in state.get("logs", []):
            st.text(linha)


# ======================================================
# 6️⃣ Painel de Diagnóstico da Memória (FAISS + SQLite)
# ======================================================
with st.sidebar.expander("🧠 Diagnóstico da Memória", expanded=False):

    st.write("### Estado atual do repositório de memória")

    from lats_sistema.memory.db import get_all_decisions
    from lats_sistema.memory.faiss_store import search_vectors
    from lats_sistema.models.embeddings import embeddings
    import numpy as np

    # -----------------------------
    # Mostrar decisões armazenadas
    # -----------------------------
    st.write("**Memórias no SQLite:**")

    memories = get_all_decisions()
    if not memories:
        st.info("Nenhuma memória registrada ainda.")
    else:
        for m in memories[-10:]:   # mostrar apenas as 10 mais recentes
            st.markdown("---")
            st.markdown(f"🆔 **ID:** `{m['id']}`")
            st.markdown(f"📄 **Evento:** {m['event_text'][:160]}...")
            st.markdown(f"🌳 **Nó:** `{m['node_id']}`")
            st.markdown(f"➡️ **Filho escolhido:** `{m['chosen_child']}`")
            st.markdown(f"📝 **Justificativa humana:** {m['justification_human']}")

    # -----------------------------
    # Testar FAISS
    # -----------------------------
    st.write("### Testar recuperação FAISS")
    teste_evento = st.text_input("Descrição para teste de similaridade:")

    if st.button("🔍 Testar FAISS"):
        if not teste_evento.strip():
            st.warning("Digite uma descrição para teste.")
        else:
            vec = embeddings.embed_query(teste_evento)
            vec = np.array(vec).astype("float32")

            try:
                ids, dist = search_vectors(vec, k=3)
                st.success(f"IDs retornados: {ids}")
            except Exception as e:
                st.error(f"Erro FAISS: {e}")

# ======================================================
# Aba de Debug — Ver Memórias da Base
# ======================================================

    mems = get_all_decisions()

    st.write(f"Total memórias: {len(mems)}")

    for m in mems[-10:]:
        st.markdown("---")
        st.write(f"**ID:** {m['id']}")
        st.write(f"**Nó:** {m['node_id']}")
        st.write(f"**Filho escolhido:** {m['chosen_child']}")
        st.write(f"**Justificativa humana:** {m['justification_human']}")

