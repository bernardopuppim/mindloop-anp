"""
Utilidades para manipular e representar métricas de nós.
"""

def ordenar_por_entropia(metricas, descending=True):
    return sorted(
        metricas.items(), 
        key=lambda x: (x[1]["entropia"] or -1), 
        reverse=descending
    )


def filtrar_por_visitas(metricas, minimo=10):
    return {
        node_id: data
        for node_id, data in metricas.items()
        if data["visitas"] >= minimo
    }
