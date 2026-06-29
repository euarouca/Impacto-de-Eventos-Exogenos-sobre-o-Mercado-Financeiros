import os
import fonte_gdelt
import fonte_yfinance
import grafo_base
import algo_mst
import algo_louvain
import algo_dijkstra
import experimentos
import visualizacao


ATIVOS = ["GC=F", "SI=F", "DX-Y.NYB", "BZ=F", "CL=F", "HG=F",
          "^GSPC", "^VIX", "EURUSD=X", "USDBRL=X", "BTC-USD", "ZW=F"]

DATA_INICIO = "2021-02-01"
DATA_FIM = "2024-03-31"
EVENTO_FOCO = "2022-02-24"
LIMIAR_CORRELACAO = 0.25
LIMIAR_Z = 2.0
JANELA_EVENTO = 3
JANELA_ESTIMACAO = 60
USAR_DADOS_REAIS = True
PASTA_SAIDA = "resultados"


def carregar_dados():
    tickers = ATIVOS
    eventos = fonte_gdelt.listar_eventos(DATA_INICIO, DATA_FIM)
    if USAR_DADOS_REAIS:
        retornos = fonte_yfinance.baixar_retornos(tickers, DATA_INICIO, DATA_FIM)
        if retornos is None or retornos.empty:
            print("Download indisponivel. Usando dados sinteticos.")
            retornos = fonte_yfinance.gerar_retornos_sinteticos(tickers, DATA_INICIO,
                                                                DATA_FIM, eventos)
    else:
        retornos = fonte_yfinance.gerar_retornos_sinteticos(tickers, DATA_INICIO,
                                                            DATA_FIM, eventos)
    tickers = [ticker for ticker in tickers if ticker in retornos.columns]
    return retornos, tickers, eventos


def main():
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    retornos, tickers, eventos = carregar_dados()
    setor_do_ativo = fonte_yfinance.setor_de_cada_ativo(tickers)

    grafo_similaridade = grafo_base.grafo_correlacao(retornos, tickers, LIMIAR_CORRELACAO)
    grafo_distancia = grafo_base.grafo_distancia(retornos, tickers)

    arvore = algo_mst.calcular_mst(grafo_distancia)
    metricas_arvore = algo_mst.metricas_mst(arvore)
    print("MST -> hub:", metricas_arvore["hub"],
          "| comprimento:", metricas_arvore["comprimento_total"])

    particao, modularidade = algo_louvain.detectar_comunidades(grafo_similaridade)
    pureza, detalhe_comunidades = algo_louvain.comparar_com_setores(particao, setor_do_ativo)
    print("Louvain -> modularidade:", round(modularidade, 3), "| pureza:", pureza)

    resultado_dijkstra = algo_dijkstra.metricas_dijkstra(retornos, tickers, grafo_distancia,
                                                         EVENTO_FOCO, JANELA_EVENTO)
    print("Dijkstra -> origem:", resultado_dijkstra["origem"],
          "| primeiros:", [a for a, _ in resultado_dijkstra["primeiros_atingidos"]])

    validacao = experimentos.tabela_validacao(retornos, tickers, eventos,
                                              JANELA_EVENTO, JANELA_ESTIMACAO, LIMIAR_Z)

    tabelas = {
        "tab_dataset": experimentos.tabela_dataset(tickers, eventos, retornos, f"{DATA_INICIO} a {DATA_FIM}"),
        "tab_mst": experimentos.tabela_mst(metricas_arvore),
        "tab_louvain": experimentos.tabela_louvain(detalhe_comunidades),
        "tab_dijkstra": experimentos.tabela_dijkstra(resultado_dijkstra),
        "tab_validacao": validacao,
    }
    for nome, tabela in tabelas.items():
        tabela.to_csv(os.path.join(PASTA_SAIDA, f"{nome}.csv"), index=False)

    visualizacao.desenhar_mst(arvore, setor_do_ativo, os.path.join(PASTA_SAIDA, "fig_mst.png"))
    visualizacao.desenhar_comunidades(grafo_similaridade, particao, os.path.join(PASTA_SAIDA, "fig_louvain.png"))
    visualizacao.desenhar_contagio(grafo_distancia, resultado_dijkstra["origem"],
                                   resultado_dijkstra["caminhos"],
                                   resultado_dijkstra["distancias"],
                                   os.path.join(PASTA_SAIDA, "fig_dijkstra.png"))
    visualizacao.desenhar_impacto_por_evento(validacao, os.path.join(PASTA_SAIDA, "fig_impacto_eventos.png"))


if __name__ == "__main__":
    main()