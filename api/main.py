# api/main.py
"""
Entrypoint fino para Vercel.

Este arquivo existe APENAS para compatibilidade com a estrutura de deploy do Vercel.
Toda a lógica de negócio permanece em backend/main.py.

⚠️ NÃO MODIFICAR - apenas re-exporta a aplicação FastAPI existente.
"""

from backend.main import app

# Vercel detecta automaticamente a variável "app" neste arquivo
