from langchain_core.prompts import ChatPromptTemplate
from lats_sistema.models.llm import llm_text

prompt_synth = ChatPromptTemplate.from_template("""
Crie um resumo técnico relacionando o evento aos trechos normativos:

EVENTO:
{evento}

TRECHOS:
{trechos}

RESUMO:
""")

def sintetizar(evento, ranking):
    melhores = "\n\n".join(x["trecho"] for x in ranking[:5])
    return (prompt_synth | llm_text).invoke({
        "evento": evento,
        "trechos": melhores
    }).content
