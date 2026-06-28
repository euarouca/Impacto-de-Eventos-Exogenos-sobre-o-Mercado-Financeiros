import numpy as np
import networkx as nx


def matriz_correlacao(retornos, tickers=None):
    if tickers is not None:
        colunas = [ticker for ticker in tickers if ticker in retornos.columns]
        retornos = retornos[colunas]
    return retornos.corr()


def grafo_correlacao(retornos, tickers=None, limiar=0.0):
    correlacao = matriz_correlacao(retornos, tickers)
    nomes = list(correlacao.columns)
    grafo = nx.Graph()
    grafo.add_nodes_from(nomes)
    for i in range(len(nomes)):
        for j in range(i + 1, len(nomes)):
            valor = correlacao.iloc[i, j]
            if np.isnan(valor) or abs(valor) < limiar:
                continue
            grafo.add_edge(nomes[i], nomes[j], weight=abs(float(valor)),
                           correlacao=float(valor))
    return grafo


def grafo_distancia(retornos, tickers=None):
    correlacao = matriz_correlacao(retornos, tickers)
    nomes = list(correlacao.columns)
    grafo = nx.Graph()
    grafo.add_nodes_from(nomes)
    for i in range(len(nomes)):
        for j in range(i + 1, len(nomes)):
            valor = correlacao.iloc[i, j]
            if np.isnan(valor):
                continue
            distancia = np.sqrt(2 * (1 - valor))
            grafo.add_edge(nomes[i], nomes[j], weight=float(distancia),
                           correlacao=float(valor))
    return grafo


if __name__ == "__main__":
    import fonte_yfinance
    tickers = fonte_yfinance.tickers_dos_setores(["Energia", "Defesa", "Metais"])
    retornos = fonte_yfinance.gerar_retornos_sinteticos(tickers, "2022-01-01", "2022-12-31")
    grafo = grafo_distancia(retornos, tickers)
    print("Nos:", grafo.number_of_nodes(), "Arestas:", grafo.number_of_edges())
