import networkx as nx


def calcular_mst(grafo_distancia):
    return nx.minimum_spanning_tree(grafo_distancia, weight="weight")


def metricas_mst(arvore):
    graus = dict(arvore.degree())
    hub = max(graus, key=graus.get) if graus else None
    comprimento_total = sum(dados["weight"] for _, _, dados in arvore.edges(data=True))
    folhas = [no for no, grau in graus.items() if grau == 1]
    return {
        "hub": hub,
        "grau_hub": graus.get(hub, 0),
        "comprimento_total": round(comprimento_total, 3),
        "quantidade_folhas": len(folhas),
        "folhas": folhas,
    }


if __name__ == "__main__":
    import fonte_yfinance, grafo_base
    tickers = fonte_yfinance.tickers_dos_setores(["Energia", "Defesa", "Metais", "Agricultura"])
    retornos = fonte_yfinance.gerar_retornos_sinteticos(tickers, "2022-01-01", "2022-12-31")
    arvore = calcular_mst(grafo_base.grafo_distancia(retornos, tickers))
    print(metricas_mst(arvore))
