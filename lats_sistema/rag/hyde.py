from langchain_core.prompts import ChatPromptTemplate
from lats_sistema.models.llm import llm_text


def hyde_generate(evento: str) -> str:
    prompt = ChatPromptTemplate.from_template("""
Gere um trecho técnico hipotético relacionado ao evento:

EVENTO:
{evento}
""")
    return (prompt | llm_text).invoke({"evento": evento}).content
