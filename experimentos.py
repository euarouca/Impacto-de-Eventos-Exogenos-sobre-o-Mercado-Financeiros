import numpy as np
import pandas as pd
import networkx as nx

import fonte_yfinance


def retorno_anormal(retornos, ativo, data_evento, janela_evento, janela_estimacao, janela_gap=10):

    datas = retornos.index
    posicoes = np.where(datas >= pd.to_datetime(data_evento))[0]
    if len(posicoes) == 0:
        return None
    inicio = posicoes[0]
    fim = min(inicio + janela_evento, len(datas) - 1)
    # Janela de estimacao termina 'janela_gap' pregoes antes do evento (carencia)
    fim_estimacao = inicio - janela_gap
    inicio_estimacao = fim_estimacao - janela_estimacao
    if inicio_estimacao < 0:
        return None

    estimacao = retornos[ativo].iloc[inicio_estimacao:fim_estimacao].values
    if len(estimacao) < 5:
        return None
    mu = float(np.mean(estimacao))
    sigma = float(np.std(estimacao, ddof=1))
    if sigma == 0:
        return None

    ativo_evento = retornos[ativo].iloc[inicio:fim + 1].values
    car = float((ativo_evento - mu).sum())
    n = fim - inicio + 1
    z = car / (sigma * np.sqrt(n))
    return car, float(z)


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


def tabela_validacao(retornos, tickers, eventos, janela_evento, janela_estimacao, limiar_z,
                     janela_gap=10):
    linhas = []
    for evento in eventos:
        significativos = 0
        car_total = 0.0
        for ativo in tickers:
            resultado = retorno_anormal(retornos, ativo, evento["data"],
                                        janela_evento, janela_estimacao, janela_gap)
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


def arestas_evento_ativo(retornos, tickers, eventos, janela_evento, janela_estimacao, limiar_z, janela_gap=10):
    arestas = []
    for evento in eventos:
        goldstein = float(evento.get("goldstein", 0.0))
        for ativo in tickers:
            resultado = retorno_anormal(retornos, ativo, evento["data"],
                                        janela_evento, janela_estimacao, janela_gap)
            if resultado is None:
                continue
            car, z = resultado
            if abs(z) >= limiar_z:
                peso = abs(goldstein) * abs(car)
                arestas.append({
                    "evento": evento["rotulo"],
                    "data": evento["data"],
                    "ativo": ativo,
                    "car": round(float(car), 4),
                    "z": round(float(z), 2),
                    "goldstein": goldstein,
                    "peso": round(peso, 4),
                })
    return arestas


def grafo_evento_ativo(retornos, tickers, eventos, janela_evento, janela_estimacao,
                       limiar_z, janela_gap=10):
    # Camada exogena: grafo DIRECIONADO (evento -> ativo).
    grafo = nx.DiGraph()
    for evento in eventos:
        grafo.add_node(evento["rotulo"], bipartite=0, tipo="evento", data=evento["data"])
    for ativo in tickers:
        grafo.add_node(ativo, bipartite=1, tipo="ativo")
    arestas = arestas_evento_ativo(retornos, tickers, eventos,
                                   janela_evento, janela_estimacao, limiar_z, janela_gap)
    for aresta in arestas:
        grafo.add_edge(aresta["evento"], aresta["ativo"], z=aresta["z"], car=aresta["car"],
                       goldstein=aresta["goldstein"], peso=aresta["peso"],
                       sinal=1 if aresta["z"] > 0 else -1, weight=aresta["peso"])
    return grafo, arestas


def tabela_evento_ativo(arestas):
    colunas = ["evento", "data", "ativo", "car", "z", "goldstein", "peso"]
    if not arestas:
        return pd.DataFrame(columns=colunas)
    return pd.DataFrame(arestas)[colunas]
