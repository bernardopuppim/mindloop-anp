# lats_sistema/memory/db.py

import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
import datetime
import numpy as np

from lats_sistema.models.embeddings import embeddings

DB_PATH = Path(__file__).resolve().parent / "decisions.db"


# ---------------------------------------------------------
# Inicialização do banco
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_text TEXT,
        node_id TEXT,
        chosen_child TEXT,
        model_suggestion TEXT,
        justification_human TEXT,
        justification_model TEXT,
        entropy REAL,
        timestamp TEXT,
        embedding BLOB
    );
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# Versão completa (API interna)
# ---------------------------------------------------------
def insert_decision(data: Dict[str, Any]) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO decisions (
            event_text, node_id, chosen_child, model_suggestion,
            justification_human, justification_model, entropy,
            timestamp, embedding
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("event_text"),
        data.get("node_id"),
        data.get("chosen_child"),
        data.get("model_suggestion"),
        data.get("justification_human"),
        data.get("justification_model"),
        data.get("entropy"),
        datetime.datetime.utcnow().isoformat(),
        data.get("embedding"),
    ))

    conn.commit()
    decision_id = cur.lastrowid
    conn.close()
    return decision_id


# ---------------------------------------------------------
# Wrapper amigável (para HITL e testes)
# ---------------------------------------------------------
def insert_memory_simple(
    event_text: str,
    node_id: str,
    chosen_child: str,
    justification_human: Optional[str] = None,
    entropy: Optional[float] = None,
):
    """
    Versão simples para registrar memórias sem exigir todos os campos.

    🔹 Gera embedding automaticamente
    🔹 Deixa todos os outros campos como None
    """
    # gerar embedding
    vec = embeddings.embed_query(event_text)
    vec = np.array(vec).astype("float32").tobytes()

    data = {
        "event_text": event_text,
        "node_id": node_id,
        "chosen_child": chosen_child,
        "model_suggestion": None,
        "justification_human": justification_human,
        "justification_model": None,
        "entropy": entropy,
        "embedding": vec,
    }

    return insert_decision(data)


# ---------------------------------------------------------
# Busca
# ---------------------------------------------------------
def get_decision_by_id(decision_id: int) -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM decisions WHERE id=?", (decision_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    cols = [
        "id", "event_text", "node_id", "chosen_child",
        "model_suggestion", "justification_human",
        "justification_model", "entropy", "timestamp", "embedding"
    ]

    return dict(zip(cols, row))


# ---------------------------------------------------------
# Busca todas decisões passadas
# ---------------------------------------------------------
def get_all_decisions():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM decisions ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()

    cols = [
        "id","event_text",
        "node_id",
        "chosen_child",
        "model_suggestion",
        "justification_human",
        "justification_model",
        "entropy",
        "timestamp",
        "embedding"
    ]

    results = []
    for r in rows:
        d = dict(zip(cols, r))
        results.append(d)

    return results
