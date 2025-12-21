# ================================================================
# graph/build.py — Monta o grafo LangGraph (RAG + LATS-P + HITL)
# ================================================================

from langgraph.graph import StateGraph, END

from lats_sistema.graph.nodes import no_rag, no_classificar, no_hitl, no_hitl_final

def build_graph():
    graph = StateGraph(dict)

    # Nós
    graph.add_node("rag", no_rag)
    graph.add_node("classificar", no_classificar)
    graph.add_node("hitl", no_hitl)
    graph.add_node("hitl_final", no_hitl_final)

    graph.set_entry_point("rag")

    # RAG → classificar
    graph.add_edge("rag", "classificar")

    # classificar → hitl ou hitl_final
    def decisor(state: dict) -> str:
        if state.get("hitl_required"):
            return "hitl"
        if state.get("final"):
            return "hitl_final"
        return "__end__"

    graph.add_conditional_edges(
        "classificar",
        decisor,
        {
            "hitl": "hitl",
            "hitl_final": "hitl_final",
            "__end__": END,
        }
    )

    # ✅ CORREÇÃO CRÍTICA: hitl → END (não volta para classificar)
    # O frontend deve chamar /hitl/continue explicitamente para retomar
    graph.add_edge("hitl", END)

    # hitl_final → END
    graph.add_edge("hitl_final", END)

    return graph.compile()
