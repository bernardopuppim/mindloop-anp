# ================================================================
# lats/state.py — versão revisada e completa para HITL + LATS-P
# ================================================================
from typing import TypedDict, List, Dict, Any, Optional


class Caminho(TypedDict):
    node_id: str
    log_prob: float
    historico: List[Dict[str, Any]]


class Checkpoint(TypedDict, total=False):
    """
    Estrutura usada para retomar a execução após HITL.
    (names NOW aligned: ultimo_* )
    """
    ultimo_node: Dict[str, Any]
    ultimo_avaliacoes: List[Dict[str, Any]]
    ultimo_probs: List[float]
    ultimo_tracking_children: List[Dict[str, Any]]
    ultimo_depth: int


class RawCheckpoint(TypedDict, total=False):
    """
    Versão temporária criada pelo engine antes de ir para o no_classificar.
    """
    ultimo_node: Dict[str, Any]
    ultimo_avaliacoes: List[Dict[str, Any]]
    ultimo_probs: List[float]
    ultimo_tracking_children: List[Dict[str, Any]]
    ultimo_depth: int


class LATSState(TypedDict, total=False):
    # --- Dados básicos ---
    descricao_evento: str
    contexto_normativo: Optional[str]

    # --- Execução LATS ---
    candidatos: List[Caminho]
    final: Optional[Dict[str, Any]]

    # --- HITL control ---
    hitl_required: bool
    hitl_selected_child: Optional[str]
    hitl_justification: Optional[str]
    hitl_metadata: Optional[Dict[str, Any]]

    # --- Checkpoints (novos) ---
    checkpoint_raw: Optional[RawCheckpoint]
    checkpoint: Optional[Checkpoint]

    # --- Logging ---
    logs: List[str]
