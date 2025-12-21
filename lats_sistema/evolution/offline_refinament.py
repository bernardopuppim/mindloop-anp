"""
Offline refinement do LATS-P:
- Carrega eventos históricos de dados_historicos.jsonl
- Executa o classificador LATS-P para cada evento
- Coleta entropia, incerteza e métricas por nó e profundidade
- Gera relatório global com diagnósticos evolutivos
"""

import os
import json
from pathlib import Path
from datetime import datetime

# ================================
# IMPORTS DO SISTEMA LATS
# ================================
from lats_sistema.lats.engine import executar_lats
from lats_sistema.lats.tree_loader import ARVORE, NODE_INDEX, ROOT_ID

# ================================
# MÉTRICAS
# ================================
from lats_sistema.evolution.metrics.entropy_tracker import EntropyTracker


# ==============================================================================
# 1. Carregar Base Histórica
# ==============================================================================
def carregar_eventos(nome_arquivo="dados_historicos.jsonl"):
    """
    Carrega eventos históricos da pasta lats_sistema/evolution/data/.
    Cada linha deve ser um JSON válido contendo o campo 'descricao_evento'.
    """

    # Diretório deste arquivo → evolution/
    base_dir = Path(__file__).resolve().parent
    data_path = base_dir / "data" / nome_arquivo

    if not data_path.exists():
        raise FileNotFoundError(
            f"[ERRO] Arquivo não encontrado: {data_path}\n"
            f"Certifique-se de que está em: lats_sistema/evolution/data/"
        )

    eventos = []
    with open(data_path, "r", encoding="utf-8") as f:
        for linha in f:
            try:
                eventos.append(json.loads(linha))
            except Exception:
                continue

    return eventos


# ==============================================================================
# 2. Processar Eventos usando o LATS-P
# ==============================================================================
def processar_eventos(eventos):
    resultados = []
    entropy_tracker = EntropyTracker()

    for idx, evento in enumerate(eventos, start=1):
        print(f"[{idx}/{len(eventos)}] Classificando evento…")

        # ==========================================================
        # Extrai o campo correto do JSONL
        # ==========================================================
        texto_evento = (
            evento.get("descricao_evento")
            or evento.get("texto")
            or evento.get("descricao")
            or evento.get("evento")
        )

        if not texto_evento:
            raise KeyError(
                f"[ERRO] Evento não contém campo textual válido.\nEvento: {evento}"
            )

        # ==========================================================
        # Executar o LATS-P
        # ==========================================================
        state = {
            "descricao_evento": texto_evento,
            "contexto_normativo": "",
            "candidatos": [],
            "final": None,
        }

        saida = executar_lats(state)
        final = saida["final"]

        # ==========================================================
        # PROCESSAR ENTROPIA — percurso principal + top3
        # ==========================================================
        percurso_principal = final["principal"]["percurso_completo"]
        entropy_tracker.processar_percurso(percurso_principal)

        for alt in final["top3"]:
            entropy_tracker.processar_percurso(alt["percurso_completo"])

        # Guarda resultado bruto
        resultados.append({
            "id_evento": evento.get("id"),
            "descricao_evento": texto_evento,
            "classificacao": final,
        })

    return resultados, entropy_tracker


# ==============================================================================
# 3. Gerar Relatórios
# ==============================================================================
def salvar_relatorios(resultados, entropy_tracker, pasta_out="lats_sistema/evolution/out"):
    Path(pasta_out).mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------
    # JSON completo
    # -------------------------------------------------------
    json_path = os.path.join(pasta_out, "resultado_refinamento.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    # -------------------------------------------------------
    # Markdown com análises
    # -------------------------------------------------------
    md_path = os.path.join(pasta_out, "relatorio_refinamento.md")

    rel_global = entropy_tracker.relatorio_global()
    resumo_por_no = entropy_tracker.resumo_por_no()
    resumo_por_depth = entropy_tracker.resumo_por_profundidade()

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 📊 Relatório de Refinamento — Entropia da Árvore LATS-P\n\n")
        f.write(f"Gerado em: **{datetime.now()}**\n\n")

        f.write("## 🔥 Estatísticas Gerais\n")
        f.write(f"- Total de registros analisados: **{rel_global['total_registros']}**\n")
        f.write(f"- Nós avaliados: **{rel_global['nos_avaliados']}**\n\n")

        # -------------------------------------------------------
        # Ranking por entropia
        # -------------------------------------------------------
        f.write("## 🌳 Nós mais ambíguos (maior entropia média)\n\n")

        ranking = sorted(
            resumo_por_no.items(),
            key=lambda x: x[1]["media_entropia"],
            reverse=True
        )

        for node_id, stats in ranking[:20]:
            f.write(
                f"- `{node_id}` → entropia média: **{stats['media_entropia']:.3f}**, "
                f"desvio: {stats['desvio']:.3f}, visitas: {stats['visitas']}\n"
            )

        # -------------------------------------------------------
        # Entropia por profundidade
        # -------------------------------------------------------
        f.write("\n## 📏 Entropia por profundidade\n\n")
        for depth, stats in resumo_por_depth.items():
            f.write(
                f"- Depth {depth}: média = **{stats['media_entropia']:.3f}**, "
                f"desvio = {stats['desvio']:.3f}, "
                f"samples = {stats['samples']}\n"
            )

    print("\n🎉 Refinamento concluído!")
    print(f"→ JSON: {json_path}")
    print(f"→ Relatório: {md_path}")

    # -------------------------------------------------------
    # GERAR A ÁRVORE v2 (ANOTADA PARA REFINAMENTO)
    # -------------------------------------------------------
    from lats_sistema.evolution.generators.restructure_tree import (
        gerar_arvore_v2,
        salvar_arvore_v2
    )
    from lats_sistema.lats.tree_loader import ARVORE

    arvore_v2 = gerar_arvore_v2(
        ARVORE,
        entropy_tracker.resumo_por_no(),
        threshold=0.90,   # Ajuste fino depois
    )

    arvore_v2_path = "lats_sistema/evolution/out/arvore_v2_draft.json"
    salvar_arvore_v2(arvore_v2, arvore_v2_path)

    print("\n🌱 Árvore v2 gerada com sucesso!")
    print(f"→ {arvore_v2_path}")


# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    print("📘 Iniciando refinamento offline da árvore LATS-P\n")

    eventos = carregar_eventos()
    resultados, entropy_tracker = processar_eventos(eventos)

    salvar_relatorios(resultados, entropy_tracker)

    print("\n🚀 Processo finalizado!")

