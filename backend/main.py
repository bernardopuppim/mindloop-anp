# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models import PredictRequest, HitlContinueRequest, PredictResponse
from backend.services.lats_service import executar_primeira_fase, continuar_pos_hitl

app = FastAPI(title="LATS-P Service API")

# Liberar chamadas do Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Rota principal de previsão
# -------------------------
@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    return executar_primeira_fase(req)


# -------------------------
# Continuação do HITL
# -------------------------
@app.post("/hitl/continue", response_model=PredictResponse)
def hitl_continue(req: HitlContinueRequest):
    return continuar_pos_hitl(req)
