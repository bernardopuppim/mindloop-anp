# backend/models.py

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional


class PredictRequest(BaseModel):
    # Campo principal esperado pelo frontend
    texto_evento: str = Field(..., alias="descricao_evento")

    # Campos opcionais já existentes
    contexto_normativo: Optional[str] = None
    state: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True


class HitlContinueRequest(BaseModel):
    state: Dict[str, Any]
    selected_child: str
    justification: Optional[str] = None


class PredictResponse(BaseModel):
    hitl_required: bool
    state: Dict[str, Any]
    hitl_metadata: Optional[Dict[str, Any]] = None
    final: Optional[Dict[str, Any]] = None
    confianca: Optional[Dict[str, Any]] = None  # Tradução de log_prob (deprecated - usar resultado_formatado)
    resultado_formatado: Optional[Dict[str, Any]] = None  # ✨ Saída formatada para UI
