import numpy as np
import networkx as nx


def escolher_origem(retornos, tickers, data_evento, janela_dias=3):
    datas = retornos.index
    posicoes = np.where(datas >= np.datetime64(data_evento))[0]
    if len(posicoes) == 0:
        return None
    inicio = posicoes[0]
    fim = min(inicio + janela_dias, len(datas) - 1)
    janela = retornos.iloc[inicio:fim + 1]

    candidatos = [ticker for ticker in tickers if ticker in janela.columns]
    if not candidatos:
        return None
    variacoes = {ticker: abs(janela[ticker].sum()) for ticker in candidatos}
    return max(variacoes, key=variacoes.get)


def caminhos_de_contagio(grafo_distancia, origem):
    distancias, caminhos = nx.single_source_dijkstra(grafo_distancia, origem, weight="weight")
    return distancias, caminhos


def ordem_de_propagacao(distancias, origem):
    pares = [(ativo, distancia) for ativo, distancia in distancias.items() if ativo != origem]
    return sorted(pares, key=lambda par: par[1])


def metricas_dijkstra(retornos, tickers, grafo_distancia, data_evento, janela_dias=3):
    origem = escolher_origem(retornos, tickers, data_evento, janela_dias)
    if origem is None or origem not in grafo_distancia:
        return None
    distancias, caminhos = caminhos_de_contagio(grafo_distancia, origem)
    ordem = ordem_de_propagacao(distancias, origem)
    return {
        "origem": origem,
        "distancias": distancias,
        "caminhos": caminhos,
        "primeiros_atingidos": ordem[:5],
        "distancia_media": round(float(np.mean(list(distancias.values()))), 3),
    }


if __name__ == "__main__":
    import fonte_yfinance, grafo_base
    tickers = fonte_yfinance.tickers_dos_setores(["Energia", "Defesa", "Metais", "Agricultura"])
    retornos = fonte_yfinance.gerar_retornos_sinteticos(tickers, "2022-01-01", "2022-12-31")
    grafo = grafo_base.grafo_distancia(retornos, tickers)
    resultado = metricas_dijkstra(retornos, tickers, grafo, "2022-02-24")
    print("Origem:", resultado["origem"])
    print("Primeiros:", [ativo for ativo, _ in resultado["primeiros_atingidos"]])
