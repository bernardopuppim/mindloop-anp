from lats_sistema.graph.build import build_graph

def simular_humano(state):
    print("\n🔔 HITL acionado!")
    print("Node:", state["hitl_metadata"]["node_id"])
    print("Pergunta:", state["hitl_metadata"]["pergunta"])
    print("Entropia local:", state["hitl_metadata"]["entropia_local"])

    print("\nOpções avaliadas:")
    for i, c in enumerate(state["hitl_metadata"]["children"]):
        print(f"  [{i}] id={c['id']} score={c['score']} prob={c['prob']}")

    escolha = int(input("\n👉 Escolha o filho correto (índice): "))
    escolhido = state["hitl_metadata"]["children"][escolha]["id"]

    state["hitl_selected_child"] = escolhido
    state["hitl_justification"] = "Escolhido no teste interativo"
    state["hitl_required"] = False

    return state


def main():
    graph = build_graph()

    state = {
        "descricao_evento": "Durante atividade ocorreu queda da mangueira no convés causando batida no dedo.",
        "candidatos": [],
        "contexto_normativo": "",
        "final": None,
        "hitl_required": False,
        "hitl_selected_child": None,
        "hitl_justification": None,
        "logs": []
    }

    print("\n🚀 Executando pipeline...\n")
    
    # executa grafo, passando a função simulada de humano
    result = graph.invoke(
            state,
            config={"configurable": {}}
        )


    print("\n📌 Resultado final:")
    print(result)
    print("\n📌 Logs:")
    for l in result["logs"]:
        print(" -", l)


if __name__ == "__main__":
    main()
