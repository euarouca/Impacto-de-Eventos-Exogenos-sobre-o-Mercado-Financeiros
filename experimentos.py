import numpy as np
import pandas as pd
import networkx as nx

import fonte_yfinance


def retorno_anormal(retornos, ativo, data_evento, janela_evento, janela_estimacao,
                    indice=fonte_yfinance.INDICE_MERCADO):
    datas = retornos.index
    posicoes = np.where(datas >= pd.to_datetime(data_evento))[0]
    if len(posicoes) == 0:
        return None
    inicio = posicoes[0]
    fim = min(inicio + janela_evento, len(datas) - 1)
    if inicio - janela_estimacao < 0 or indice not in retornos.columns or ativo == indice:
        return None

    ativo_estimacao = retornos[ativo].iloc[inicio - janela_estimacao:inicio].values
    indice_estimacao = retornos[indice].iloc[inicio - janela_estimacao:inicio].values
    if len(ativo_estimacao) < 5 or np.std(indice_estimacao) == 0:
        return None

    beta, alfa = np.polyfit(indice_estimacao, ativo_estimacao, 1)
    residuos = ativo_estimacao - (alfa + beta * indice_estimacao)
    desvio_residuos = residuos.std()
    if desvio_residuos == 0:
        return None

    ativo_evento = retornos[ativo].iloc[inicio:fim + 1].values
    indice_evento = retornos[indice].iloc[inicio:fim + 1].values
    car = (ativo_evento - (alfa + beta * indice_evento)).sum()
    n = fim - inicio + 1
    z = car / (desvio_residuos * np.sqrt(n))
    return float(car), float(z)


def tabela_dataset(tickers, eventos, retornos, periodo):
    return pd.DataFrame([
        {"caracteristica": "Ativos", "valor": len(tickers)},
        {"caracteristica": "Eventos", "valor": len(eventos)},
        {"caracteristica": "Pregoes", "valor": retornos.shape[0]},
        {"caracteristica": "Periodo", "valor": periodo},
    ])


def tabela_mst(metricas):
    return pd.DataFrame([
        {"metrica": "Hub central", "valor": metricas["hub"]},
        {"metrica": "Grau do hub", "valor": metricas["grau_hub"]},
        {"metrica": "Comprimento total", "valor": metricas["comprimento_total"]},
        {"metrica": "Ativos perifericos", "valor": metricas["quantidade_folhas"]},
    ])


def tabela_louvain(detalhe):
    return pd.DataFrame([
        {"comunidade": comunidade, "setor_dominante": dados["setor_dominante"],
         "tamanho": dados["tamanho"], "pureza": dados["pureza"]}
        for comunidade, dados in detalhe.items()
    ])


def tabela_dijkstra(resultado):
    return pd.DataFrame([
        {"posicao": i + 1, "ativo": ativo, "distancia": round(distancia, 3)}
        for i, (ativo, distancia) in enumerate(resultado["primeiros_atingidos"])
    ])


def tabela_validacao(retornos, tickers, eventos, janela_evento, janela_estimacao, limiar_z):
    linhas = []
    for evento in eventos:
        significativos = 0
        car_total = 0.0
        for ativo in tickers:
            resultado = retorno_anormal(retornos, ativo, evento["data"],
                                        janela_evento, janela_estimacao)
            if resultado is None:
                continue
            car, z = resultado
            if abs(z) >= limiar_z:
                significativos += 1
                car_total += abs(car)
        linhas.append({
            "evento": evento["rotulo"],
            "data": evento["data"],
            "ativos_significativos": significativos,
            "car_acumulado": round(car_total, 3),
        })
    return pd.DataFrame(linhas)


def arestas_evento_ativo(retornos, tickers, eventos, janela_evento, janela_estimacao, limiar_z):
    """Lista as arestas de choque evento->ativo: o ativo teve retorno anormal
    significativo (|z| >= limiar_z) na janela do evento, pelo modelo de mercado."""
    arestas = []
    for evento in eventos:
        for ativo in tickers:
            resultado = retorno_anormal(retornos, ativo, evento["data"],
                                        janela_evento, janela_estimacao)
            if resultado is None:
                continue
            car, z = resultado
            if abs(z) >= limiar_z:
                arestas.append({
                    "evento": evento["rotulo"],
                    "data": evento["data"],
                    "ativo": ativo,
                    "car": round(float(car), 4),
                    "z": round(float(z), 2),
                })
    return arestas


def grafo_evento_ativo(retornos, tickers, eventos, janela_evento, janela_estimacao, limiar_z):
    """Monta o grafo bipartido evento->ativo. Vertices de evento tem bipartite=0
    e vertices de ativo bipartite=1; cada aresta de choque guarda z, car e o sinal."""
    grafo = nx.Graph()
    for evento in eventos:
        grafo.add_node(evento["rotulo"], bipartite=0, tipo="evento", data=evento["data"])
    for ativo in tickers:
        grafo.add_node(ativo, bipartite=1, tipo="ativo")
    arestas = arestas_evento_ativo(retornos, tickers, eventos,
                                   janela_evento, janela_estimacao, limiar_z)
    for aresta in arestas:
        grafo.add_edge(aresta["evento"], aresta["ativo"], z=aresta["z"], car=aresta["car"],
                       sinal=1 if aresta["z"] > 0 else -1, weight=abs(aresta["z"]))
    return grafo, arestas


def tabela_evento_ativo(arestas):
    if not arestas:
        return pd.DataFrame(columns=["evento", "data", "ativo", "car", "z"])
    return pd.DataFrame(arestas)
