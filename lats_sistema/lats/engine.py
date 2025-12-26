# ================================================================
# lats/engine.py — LATS-P com HITL simples (checkpoint no próprio state)
# + Memória de decisões humanas (SQLite + FAISS) integrada ao contexto
# ================================================================

import math
import logging
from typing import Dict, Any, List

from lats_sistema.lats.utils import (
    eh_terminal,
    softmax,
    temperatura_por_profundidade,
    shannon_entropy,
)
from lats_sistema.lats.evaluator import avaliar_filhos_llm
from lats_sistema.lats.tree_loader import NODE_INDEX, ROOT_ID
from lats_sistema.lats.hitl_gating import precisa_hitl, gerar_hitl_metadata

# ⚡ FAST_MODE support (NÃO afeta HITL)
from lats_sistema.config.fast_mode import LATS_MAX_STEPS, LATS_TOP_FINAIS, SERVERLESS_FAST_MODE

logger = logging.getLogger(__name__)

# 🔁 Memória de decisões humanas (SQLite + FAISS)
# ⚠️ SERVERLESS: Memória depende de FAISS, desabilitada em modo serverless
if not SERVERLESS_FAST_MODE:
    from lats_sistema.memory.memory_retriever import buscar_justificativas_semelhantes
    from lats_sistema.memory.memory_saver import salvar_memoria_if_applicable
else:
    # Placeholders para modo serverless
    def buscar_justificativas_semelhantes(*args, **kwargs):
        """Placeholder - memória episódica desabilitada em serverless"""
        return []

    def salvar_memoria_if_applicable(*args, **kwargs):
        """Placeholder - memória episódica desabilitada em serverless"""
        pass

    logger.info("[SERVERLESS MODE] Memória episódica (FAISS) desabilitada")

MAX_STEPS = LATS_MAX_STEPS
TOP_FINAIS = LATS_TOP_FINAIS
MIN_SCORE = 0.05

# 🔒 COLAPSO ONTOLÓGICO: Threshold para decisão determinística
# Se um filho tem score >= DETERMINISTIC_THRESHOLD, considera-se evidência excludente
DETERMINISTIC_THRESHOLD = 0.95  # Score >= 0.95 → colapso automático


# ================================================================
# ENGINE LATS-P COM HITL
# ================================================================
def executar_lats(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Engine LATS-P com suporte a HITL.

    - Se houver 'hitl_selected_child' em state → retoma via _continuar_pos_hitl.
    - Caso contrário, segue o fluxo normal do LATS-P.
    - Se precisa_hitl(...) retornar True, salva o checkpoint em campos
      'ultimo_*' no próprio state e seta 'hitl_required' = True.
    """

    print("\n==============================")
    print(" 🚀 EXECUTAR LATS-P")
    print("==============================\n")

    # 1) Se estamos voltando do HITL → continuar a partir do checkpoint
    if state.get("hitl_selected_child") is not None:
        print("🔄 Retomando após HITL (hitl_selected_child preenchido)...\n")
        return _continuar_pos_hitl(state)

    descricao = state.get("descricao_evento")
    contexto_base = state.get("contexto_normativo", "") or ""

    print(f"📄 Evento: {descricao}\n")

    # logs e flags padrões
    state.setdefault("logs", [])
    state.setdefault("hitl_required", False)
    state.setdefault("hitl_metadata", None)
    state.setdefault("hitl_final_required", False)

    # Fila de candidatos
    candidatos = state.get("candidatos") or []
    if not candidatos:
        print(f"📍 Iniciando do ROOT: {ROOT_ID}")
        candidatos = [{
            "node_id": ROOT_ID,
            "log_prob": 0.0,
            "historico": [],
        }]
        state["candidatos"] = candidatos

    finais: List[Dict[str, Any]] = []

    # =============================================================
    # LOOP LATS-P
    # =============================================================
    for step in range(MAX_STEPS):

        print("\n------------------------------")
        print(f" 🔁 PASSO {step + 1}")
        print("------------------------------")

        if not candidatos:
            print("❗ Sem candidatos restantes. Encerrando loop.")
            break

        # Ordena por log_prob (maior primeiro) e pega o melhor caminho
        candidatos.sort(key=lambda c: c["log_prob"], reverse=True)
        atual = candidatos.pop(0)

        node_id_atual = atual["node_id"]
        node = NODE_INDEX[node_id_atual]

        print(f"📌 Nó atual: {node_id_atual}")
        print(f"📚 Pergunta: {node.get('pergunta')}")

        # Nó terminal
        if eh_terminal(node):
            print("🏁 Nó terminal alcançado.")
            finais.append(atual)
            if len(finais) >= TOP_FINAIS:
                print("🎯 TOP_FINAIS atingido.")
                break
            continue

        # ==========================================================
        # 🔍 1) Recuperar memórias de decisões humanas semelhantes
        # ==========================================================
        try:
            memorias = buscar_justificativas_semelhantes(
                descricao_evento=descricao or "",
                node_id=node_id_atual,
                k=3,
                state=state,  # ⚡ OTIMIZAÇÃO: Passa state para reutilizar embedding cached
            )
        except Exception as e:
            print(f"⚠️ Erro ao buscar memórias HITL: {e}")
            memorias = []

        trecho_memoria = ""
        if memorias:
            trecho_memoria = "\n\n[HISTÓRICO DE DECISÕES HUMANAS RELEVANTES]\n"
            for m in memorias:
                # Espera-se que cada memória tenha estas chaves:
                # event_text, chosen_child, justification_human
                event_resumo = (m.get("event_text") or "")[:160].replace("\n", " ")
                trecho_memoria += (
                    f"- Evento similar: \"{event_resumo}...\"\n"
                    f"  → Humano escolheu o filho: `{m.get('chosen_child')}`\n"
                    f"    Justificativa humana: {m.get('justification_human')}\n"
                )
        else:
            trecho_memoria = (
                "\n\n[HISTÓRICO DE DECISÕES HUMANAS RELEVANTES]\n"
                "Nenhuma memória relevante encontrada para este nó.\n"
            )

        # Guarda para debug / logging se quiser inspecionar depois
        state["memoria_hitl_contexto"] = trecho_memoria

        # Contexto passado para o LLM = contexto_normativo + memórias humanas
        contexto = contexto_base + trecho_memoria

        # ---------------------------------------------------------
        # 2) Avaliação dos filhos via LLM
        # ---------------------------------------------------------
        print("🤖 Avaliando filhos via LLM...")
        avaliacoes = avaliar_filhos_llm(node, descricao, contexto)

        if not avaliacoes:
            print("⚠️ Sem avaliações — usando fallback uniforme.")
            filhos = node.get("subnodos", [])
            if not filhos:
                print("⚠️ Nó sem filhos. Tratando como terminal.")
                finais.append(atual)
                continue

            avaliacoes = [
                {"id": f["id"], "score": 0.5, "justificativa": "fallback uniforme"}
                for f in filhos
            ]

        # =========================================================
        # 🔥 PODA CRÍTICA: Remover filhos com score == 0
        # =========================================================
        avaliacoes_original = avaliacoes
        avaliacoes = [a for a in avaliacoes if a.get("score", 0) > 0]

        num_podados = len(avaliacoes_original) - len(avaliacoes)
        if num_podados > 0:
            print(f"✂️ {num_podados} filho(s) podado(s) por score == 0")

        # Se TODOS os filhos foram podados → erro de modelagem
        if not avaliacoes:
            print("⚠️ AVISO: Todos os filhos têm score == 0")
            print(f"⚠️ Erro de modelagem no nó {node_id_atual}")
            print("⚠️ Tratando como nó terminal por impossibilidade de expansão")
            finais.append(atual)
            continue

        # =========================================================
        # 🔒 COLAPSO ONTOLÓGICO: Apenas 1 filho válido
        # =========================================================
        # Se restar apenas 1 filho após poda → decisão determinística
        # NÃO calcular entropia, NÃO acionar HITL, expandir automaticamente
        if len(avaliacoes) == 1:
            filho_unico = avaliacoes[0]
            print("\n🔒 COLAPSO ONTOLÓGICO DETECTADO")
            print(f"  ➤ Após poda, resta apenas 1 filho válido: {filho_unico['id']}")
            print(f"  ➤ Score: {filho_unico['score']:.3f}")
            print(f"  ➤ Decisão determinística - sem HITL, sem entropia")
            print(f"  ➤ Expandindo automaticamente...\n")

            # Expansão direta (prob = 1.0, entropia = 0)
            novo_hist = atual["historico"] + [{
                "node_id": node_id_atual,
                "pergunta": node.get("pergunta", ""),
                "depth": len(atual["historico"]) + 1,
                "children": [{
                    "id": filho_unico["id"],
                    "score": float(filho_unico["score"]),
                    "prob": 1.0,  # Probabilidade determinística
                    "justificativa": filho_unico.get("justificativa", ""),
                }],
                "chosen_child": filho_unico["id"],
                "chosen_score": float(filho_unico["score"]),
                "chosen_prob": 1.0,
                "colapso_ontologico": True,  # Flag para auditoria
            }]

            # Adicionar ao beam com log_prob inalterado (prob=1.0 → log=0)
            candidatos.append({
                "node_id": filho_unico["id"],
                "log_prob": atual["log_prob"] + math.log(1.0),  # +0
                "historico": novo_hist,
            })

            # ⚠️ CRÍTICO: LIMPAR BEAM de outros caminhos paralelos
            # Após colapso ontológico, outros ramos incompatíveis devem ser descartados
            # Isso garante que o sistema siga apenas o caminho determinístico
            candidatos = [candidatos[-1]]  # Manter apenas o caminho colapsado

            print("🔥 Beam limpo: apenas caminho ontológico será explorado")
            continue  # Pular cálculo de entropia, HITL, expansão paralela

        # =========================================================
        # 🔒 COLAPSO ONTOLÓGICO: Score determinístico (>= 0.95)
        # =========================================================
        # Se um filho tem score >= DETERMINISTIC_THRESHOLD, há evidência excludente
        # Os demais são ontologicamente impossíveis, não devem ser explorados
        max_score = max(a["score"] for a in avaliacoes)

        if max_score >= DETERMINISTIC_THRESHOLD:
            # Encontrar filho com score máximo
            filho_deterministico = max(avaliacoes, key=lambda a: a["score"])

            print("\n🔒 COLAPSO ONTOLÓGICO DETECTADO (SCORE ALTO)")
            print(f"  ➤ Filho '{filho_deterministico['id']}' tem score {filho_deterministico['score']:.3f} >= {DETERMINISTIC_THRESHOLD}")
            print(f"  ➤ Evidência excludente detectada - outros ramos são impossíveis")
            print(f"  ➤ Decisão determinística - sem HITL, sem entropia")
            print(f"  ➤ Expandindo automaticamente...\n")

            # Expansão direta (prob ≈ 1.0, entropia ≈ 0)
            novo_hist = atual["historico"] + [{
                "node_id": node_id_atual,
                "pergunta": node.get("pergunta", ""),
                "depth": len(atual["historico"]) + 1,
                "children": [{
                    "id": filho_deterministico["id"],
                    "score": float(filho_deterministico["score"]),
                    "prob": 1.0,  # Simplificado como determinístico
                    "justificativa": filho_deterministico.get("justificativa", ""),
                }],
                "chosen_child": filho_deterministico["id"],
                "chosen_score": float(filho_deterministico["score"]),
                "chosen_prob": 1.0,
                "colapso_ontologico": True,  # Flag para auditoria
                "colapso_razao": "score_deterministic",
            }]

            # Adicionar ao beam
            candidatos.append({
                "node_id": filho_deterministico["id"],
                "log_prob": atual["log_prob"] + math.log(1.0),  # +0
                "historico": novo_hist,
            })

            # ⚠️ CRÍTICO: LIMPAR BEAM de outros caminhos paralelos
            candidatos = [candidatos[-1]]  # Manter apenas o caminho determinístico

            print("🔥 Beam limpo: apenas caminho determinístico será explorado")
            continue  # Pular cálculo de entropia, HITL, expansão paralela

        # Score mais alto muito baixo?
        if max_score < MIN_SCORE:
            print(f"⚠️ Scores muito baixos (máx={max_score:.3f}) → fallback baixa confiança.")
            filhos = node.get("subnodos", [])
            if not filhos:
                print("⚠️ Nó sem filhos no fallback. Tratando como terminal.")
                finais.append(atual)
                continue

            avaliacoes = [
                {
                    "id": f["id"],
                    "score": 0.7 if i == 0 else 0.3,
                    "justificativa": "fallback baixa confiança",
                }
                for i, f in enumerate(filhos)
            ]

        depth = len(atual["historico"]) + 1
        temp = temperatura_por_profundidade(depth)
        probs = softmax([a["score"] for a in avaliacoes], temp)

        tracking_children = []
        print("\n🔍 Filhos avaliados:")
        for aval, p in zip(avaliacoes, probs):
            tracking_children.append({
                "id": aval["id"],
                "score": float(aval["score"]),
                "prob": float(p),
                "justificativa": aval.get("justificativa", ""),
            })
            print(f"  ➤ {aval['id']} | score={aval['score']:.3f} | prob={float(p):.3f}")

        entropia_local = shannon_entropy(probs)
        print(f"\n📊 Entropia local: {entropia_local:.3f}")

        # ---------------------------------------------------------
        # 3) HITL GATING
        # ---------------------------------------------------------
        etapa_info = {
            "node_id": node_id_atual,
            "children": tracking_children,
            "depth": depth,
            "entropia_local": entropia_local,
        }

        if precisa_hitl(etapa_info):
            print("\n" + "="*70)
            print(" 🔥 HITL ACIONADO - ENTROPIA ALTA DETECTADA")
            print("="*70)
            print(f"\n📍 Nó atual: {node_id_atual}")
            print(f"📊 Entropia: {entropia_local:.3f} (threshold: 1.3)")
            print(f"📉 Depth: {depth}")
            print(f"\n🔒 Salvando checkpoint do LATS-P...")

            state["ultimo_node"] = atual
            state["ultimo_avaliacoes"] = avaliacoes
            state["ultimo_probs"] = probs
            state["ultimo_tracking_children"] = tracking_children
            state["ultimo_depth"] = depth
            state["ultimo_entropia_local"] = entropia_local  # ← importante p/ memória

            state["hitl_required"] = True
            state["hitl_metadata"] = gerar_hitl_metadata(node, etapa_info)

            state["logs"].append(
                f"HITL acionado no nó {node_id_atual} "
                f"(depth={depth}, entropia={entropia_local:.3f})"
            )

            print("\n✅ Checkpoint salvo com sucesso!")
            print("⏸️  EXECUÇÃO DO LATS-P PAUSADA")
            print("➡️  Retornando state com hitl_required=True")
            print("➡️  Grafo será finalizado (hitl → END)")
            print("➡️  Frontend deve exibir modal de decisão")
            print("➡️  Use POST /hitl/continue para retomar\n")
            print("="*70 + "\n")

            return state

        print("\n➡️ Expansão normal...")

        # Expansão normal (sem HITL)
        for aval, p in zip(avaliacoes, probs):
            filho_id = aval["id"]

            new_log = atual["log_prob"] + math.log(max(p, 1e-12))
            print(f"  ➤ Expandindo com filho {filho_id}  (log_prob={new_log:.3f})")

            novo_hist = atual["historico"] + [{
                "node_id": node_id_atual,
                "pergunta": node.get("pergunta", ""),
                "depth": depth,
                "children": tracking_children,
                "chosen_child": filho_id,
                "chosen_score": float(aval["score"]),
                "chosen_prob": float(p),
            }]

            candidatos.append({
                "node_id": filho_id,
                "log_prob": new_log,
                "historico": novo_hist,
            })

    # =============================================================
    # FINALIZAÇÃO (TOP 1)
    # =============================================================
    if finais:
        finais.sort(key=lambda c: c["log_prob"], reverse=True)
        principal = finais[0]

        state["final"] = principal

        # 🔥 Sempre que finalizamos, pedimos HITL FINAL
        state["hitl_final_required"] = True

        print("\n==============================")
        print(" 🎯 RESULTADO FINAL LATS-P")
        print("==============================")
        print(f"📌 Nó final: {principal['node_id']}")
        print(f"📈 log_prob: {principal['log_prob']:.3f}\n")

    return state


# ================================================================
# CONTINUAÇÃO APÓS HITL (com gravação automática da memória)
# ================================================================
def _continuar_pos_hitl(state: Dict[str, Any]) -> Dict[str, Any]:

    print("\n" + "="*70)
    print(" 🔄 RETOMANDO EXECUÇÃO APÓS HITL")
    print("="*70 + "\n")

    obrigatorios = [
        "ultimo_node",
        "ultimo_avaliacoes",
        "ultimo_probs",
        "ultimo_tracking_children",
        "ultimo_depth",
        "hitl_selected_child",
        "hitl_justification",
        "ultimo_entropia_local",  # usamos na memória
    ]

    for campo in obrigatorios:
        if campo not in state:
            raise RuntimeError(f"ERRO: _continuar_pos_hitl chamado sem state['{campo}']")

    atual = state["ultimo_node"]
    avaliacoes = state["ultimo_avaliacoes"]
    probs = state["ultimo_probs"]
    tracking_children = state["ultimo_tracking_children"]
    depth = state["ultimo_depth"]

    escolhido = state["hitl_selected_child"]
    justificativa_humana = state["hitl_justification"]
    entropia_local = state["ultimo_entropia_local"]

    print(f"✅ Filho escolhido pelo humano: {escolhido}")
    print(f"📝 Justificativa humana: {justificativa_humana}")
    print(f"📍 Retomando do nó: {atual['node_id']}\n")

    # ---------------------------------------------------------------
    # 1) Encontrar score/prob/justificativa do filho escolhido
    # ---------------------------------------------------------------
    chosen_score = None
    chosen_prob = None
    model_just = None

    for aval, p in zip(avaliacoes, probs):
        if aval["id"] == escolhido:
            chosen_score = float(aval["score"])
            chosen_prob = float(p)
            model_just = aval.get("justificativa", "")
            break

    if chosen_prob is None:
        print("⚠️ Filho escolhido não estava na lista — fallback prob=1.0")
        chosen_score = 1.0
        chosen_prob = 1.0
        model_just = "(não encontrado)"

    # ---------------------------------------------------------------
    # 2) 🔥 Registrar memória humana (SQLite + FAISS) — se fizer sentido
    #    (regras de deduplicação e entropia alta ficam no memory_saver)
    # ---------------------------------------------------------------
    try:
        salvar_memoria_if_applicable(
            state=state,
            node_id=atual["node_id"],
            chosen_child=escolhido,
            justificativa_humana=justificativa_humana or "",
            justificativa_modelo=model_just or "",
            entropia_local=float(entropia_local),
            avaliacoes=avaliacoes,
            probs=probs,
        )
    except Exception as e:
        print(f"⚠️ ERRO ao salvar memória HITL: {e}")
        state["logs"].append(f"ERRO ao salvar memória HITL: {e}")

    # ---------------------------------------------------------------
    # 3) Construir novo histórico
    # ---------------------------------------------------------------
    novo_hist = atual["historico"] + [{
        "node_id": atual["node_id"],
        "pergunta": NODE_INDEX[atual["node_id"]].get("pergunta", ""),
        "depth": depth,
        "children": tracking_children,
        "chosen_child": escolhido,
        "chosen_score": chosen_score,
        "chosen_prob": chosen_prob,
        "justificativa_humana": justificativa_humana,
    }]

    new_log_prob = atual["log_prob"] + math.log(max(chosen_prob, 1e-12))

    print(f"➡️ Retomando com log_prob={new_log_prob:.3f}")

    # ---------------------------------------------------------------
    # 4) Limpar flags do HITL
    # ---------------------------------------------------------------
    state["hitl_required"] = False
    state["hitl_selected_child"] = None
    state["hitl_justification"] = None
    state["hitl_metadata"] = None

    # ---------------------------------------------------------------
    # 5) Continuar o LATS pelo filho selecionado
    # ---------------------------------------------------------------
    state["candidatos"] = [{
        "node_id": escolhido,
        "log_prob": new_log_prob,
        "historico": novo_hist,
    }]

    state["logs"].append(
        f"HITL resolvido: seguindo pelo filho {escolhido} "
        f"(score={chosen_score:.3f}, prob={chosen_prob:.3f})"
    )

    print("="*70)
    print(" 🔁 RETOMANDO LATS-P COM ESCOLHA HUMANA")
    print("="*70)
    print(f"➡️  Seguindo pelo filho: {escolhido}")
    print(f"➡️  Score: {chosen_score:.3f} | Prob: {chosen_prob:.3f}")
    print(f"➡️  Log-prob acumulado: {new_log_prob:.3f}\n")

    return executar_lats(state)
