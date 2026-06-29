from collections import Counter, defaultdict

import networkx as nx

try:
    import community as louvain
    USA_LOUVAIN = True
except ImportError:
    USA_LOUVAIN = False


def detectar_comunidades(grafo_similaridade, semente=42):
    # Grafo sem arestas: a modularidade e indefinida (divisao por zero no networkx).
    # Retorna particao trivial -- cada no em sua propria comunidade -- com Q = 0.
    if grafo_similaridade.number_of_edges() == 0:
        return {no: i for i, no in enumerate(grafo_similaridade.nodes())}, 0.0

    if USA_LOUVAIN:
        particao = louvain.best_partition(grafo_similaridade, weight="weight",
                                          random_state=semente)
        modularidade = louvain.modularity(particao, grafo_similaridade, weight="weight")
        return particao, modularidade

    grupos = nx.community.greedy_modularity_communities(grafo_similaridade, weight="weight")
    particao = {}
    for numero, grupo in enumerate(grupos):
        for ativo in grupo:
            particao[ativo] = numero
    modularidade = nx.community.modularity(grafo_similaridade,
                                           [set(g) for g in grupos], weight="weight")
    return particao, modularidade


def comparar_com_setores(particao, setor_do_ativo):
    ativos_por_comunidade = defaultdict(list)
    for ativo, comunidade in particao.items():
        ativos_por_comunidade[comunidade].append(ativo)

    total = len(particao)
    acertos = 0
    detalhe = {}
    for comunidade, ativos in ativos_por_comunidade.items():
        setores = [setor_do_ativo.get(ativo, "Outros") for ativo in ativos]
        setor_dominante, frequencia = Counter(setores).most_common(1)[0]
        acertos += frequencia
        detalhe[comunidade] = {
            "setor_dominante": setor_dominante,
            "tamanho": len(ativos),
            "pureza": round(frequencia / len(ativos), 2),
        }
    pureza_media = acertos / total if total else 0.0
    return pureza_media, detalhe


if __name__ == "__main__":
    import fonte_yfinance, grafo_base
    tickers = fonte_yfinance.tickers_dos_setores(["Energia", "Defesa", "Metais", "Agricultura"])
    retornos = fonte_yfinance.gerar_retornos_sinteticos(tickers, "2022-01-01", "2022-12-31")
    grafo = grafo_base.grafo_correlacao(retornos, tickers, limiar=0.2)
    particao, modularidade = detectar_comunidades(grafo)
    pureza, _ = comparar_com_setores(particao, fonte_yfinance.setor_de_cada_ativo(tickers))
    print("Modularidade:", round(modularidade, 3), "Pureza:", pureza)
