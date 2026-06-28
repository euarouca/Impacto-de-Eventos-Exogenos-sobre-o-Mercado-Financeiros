import numpy as np
import pandas as pd

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
