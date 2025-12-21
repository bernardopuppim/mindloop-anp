from graph.build import build_graph
from lats.state import LATSState
import json

app = build_graph()

if __name__ == "__main__":
    evento = """Em atividade preliminar para operaçao de pull in, durante a retirada do dummy spool, o colaborador sofreu impacto do equipamento contra o pé direito enquanto realizava o apoio do equipamento no chão. Com o impacto a biqueira da bota se deformou provocando corte de aproximadamente 6cm no dorso do pé.		"Colaborador sera atendido em terra para realizaçao de exame de imagem e sutura. Não há indicativo de fratura.
OS 006000555324 - PULL-IN DE 2ª EXTREMIDADE TOPSIDE IA / BUZ-9 / SSUN / P-76.
Local: ""OUTRA"" foi selecionada pois não há a opção da Unidade P-76 na lista."
"""
    
    entrada = LATSState(
        descricao_evento=evento,
        candidatos=[],
        final=None,
        contexto_normativo=None
    )

    saida = app.invoke(entrada)
    print(json.dumps(saida["final"], indent=2, ensure_ascii=False))
