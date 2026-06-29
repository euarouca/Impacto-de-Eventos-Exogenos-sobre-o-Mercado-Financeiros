import os
import fonte_gdelt
import fonte_yfinance
import experimentos
import visualizacao

CONJUNTO_SETORIAL = ["BZ=F", "LMT", "ZW=F", "CRWD", "GC=F", "RUB=X", "PETR4.SA"]

DATA_INICIO = "2021-02-01"
DATA_FIM = "2024-03-31"
JANELA_EVENTO = 3
JANELA_ESTIMACAO = 60
LIMIAR_Z = 2.0
PASTA = "resultados"


def gerar(ativos, sufixo, usar_reais=True):
    os.makedirs(PASTA, exist_ok=True)
    eventos = fonte_gdelt.listar_eventos(DATA_INICIO, DATA_FIM)

    retornos = None
    if usar_reais:
        retornos = fonte_yfinance.baixar_retornos(ativos, DATA_INICIO, DATA_FIM)
    origem = "reais"
    if retornos is None or getattr(retornos, "empty", True):
        # O modelo de mercado precisa do indice. Em dados reais o baixar_retornos
        # ja inclui ^GSPC; no sintetico precisamos adiciona-lo explicitamente.
        ativos_sint = list(ativos)
        if fonte_yfinance.INDICE_MERCADO not in ativos_sint:
            ativos_sint.append(fonte_yfinance.INDICE_MERCADO)
        retornos = fonte_yfinance.gerar_retornos_sinteticos(ativos_sint, DATA_INICIO, DATA_FIM, eventos)
        origem = "sinteticos"

    tickers = [t for t in ativos if t in retornos.columns]
    setor = fonte_yfinance.setor_de_cada_ativo(tickers)
    grafo, arestas = experimentos.grafo_evento_ativo(
        retornos, tickers, eventos, JANELA_EVENTO, JANELA_ESTIMACAO, LIMIAR_Z)

    print(f"[{sufixo}] dados={origem} | ativos={len(tickers)} | "
          f"arestas de choque evento->ativo: {len(arestas)}")

    if origem == "sinteticos":
        sufixo = f"{sufixo}_sintetico"
    csv = os.path.join(PASTA, f"tab_evento_ativo_{sufixo}.csv")
    fig = os.path.join(PASTA, f"fig_evento_ativo_{sufixo}.png")
    experimentos.tabela_evento_ativo(arestas).to_csv(csv, index=False)
    subtitulo = "DADOS SINTETICOS (previa estrutural)" if origem == "sinteticos" else None
    visualizacao.desenhar_evento_ativo(grafo, setor, fig, subtitulo=subtitulo)
    print(f"[{sufixo}] figura: {fig}")
    return fig, arestas, origem


if __name__ == "__main__":
    gerar(CONJUNTO_SETORIAL, "setorial")
