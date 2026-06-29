import os
import time
import hashlib
import numpy as np
import pandas as pd
import yfinance as yf

try:
    from curl_cffi import requests as curl_requests
    SESSAO = curl_requests.Session(impersonate="chrome")
except ImportError:
    SESSAO = None


INDICE_MERCADO = "^GSPC"
PASTA_CACHE = "cache_yf"

# Universo do estudo: 7 ativos, um por setor. Os rotulos sao os usados nas
# figuras e no texto. O indice de mercado (^GSPC) NAO e vertice do grafo: serve
# apenas de baseline no Modelo de Mercado (calculo do retorno anormal).
CATALOGO_ATIVOS = {
    "Energia": ["BZ=F"],
    "Defesa": ["LMT"],
    "Agrobusiness": ["ZW=F"],
    "Cibersegurança": ["CRWD"],
    "Safe Havens": ["GC=F"],
    "Indices e Cambio": ["RUB=X"],
    "Mercado Brasileiro": ["PETR4.SA"],
}

# Setores cujos ativos recebem o choque sintetico nos dias de evento (usado
# apenas no gerador offline gerar_retornos_sinteticos, para testes sem rede).
SETORES_SENSIVEIS = ("Energia", "Defesa", "Mercado Brasileiro",
                     "Agrobusiness", "Safe Havens", "Indices e Cambio")


def tickers_dos_setores(setores):
    tickers = []
    for setor in setores:
        tickers.extend(CATALOGO_ATIVOS.get(setor, []))
    return tickers


def setor_de_cada_ativo(tickers):
    mapa = {}
    for setor, lista in CATALOGO_ATIVOS.items():
        for ticker in lista:
            if ticker in tickers:
                mapa[ticker] = setor
    for ticker in tickers:
        mapa.setdefault(ticker, "Outros")
    return mapa


def _caminho_cache(tickers, data_inicio, data_fim):
    chave = "|".join(sorted(tickers)) + f"|{data_inicio}|{data_fim}"
    codigo = hashlib.md5(chave.encode()).hexdigest()[:16]
    return os.path.join(PASTA_CACHE, f"precos_{data_inicio}_{data_fim}_{codigo}.parquet")


def _extrair_precos(dados_brutos, tickers):
    precos = {}
    for ticker in tickers:
        try:
            if isinstance(dados_brutos.columns, pd.MultiIndex):
                if ticker in dados_brutos.columns.get_level_values(0):
                    tabela = dados_brutos[ticker]
                elif ticker in dados_brutos.columns.get_level_values(1):
                    tabela = dados_brutos.xs(ticker, level=1, axis=1)
                else:
                    continue
                coluna = "Close" if "Close" in tabela.columns else tabela.columns[0]
                precos[ticker] = tabela[coluna]
            else:
                precos[ticker] = dados_brutos["Close"]
        except Exception:
            continue
    if not precos:
        return None
    return pd.DataFrame(precos).dropna(how="all").ffill().bfill()


def _baixar_com_tentativas(tickers, data_inicio, data_fim, tentativas=4, espera=20):
    for tentativa in range(tentativas):
        try:
            argumentos = dict(start=data_inicio, end=data_fim, progress=False,
                              auto_adjust=True, group_by="ticker")
            if SESSAO is not None:
                argumentos["session"] = SESSAO
            dados = yf.download(tickers, **argumentos)
            if dados is not None and not dados.empty:
                return dados
        except Exception:
            pass
        if tentativa < tentativas - 1:
            time.sleep(espera * (tentativa + 1))
    return None


def baixar_retornos(tickers, data_inicio, data_fim, incluir_indice=True, margem_dias=160):
    os.makedirs(PASTA_CACHE, exist_ok=True)
    tickers = sorted(set(list(tickers) + ([INDICE_MERCADO] if incluir_indice else [])))
    inicio_com_margem = (pd.to_datetime(data_inicio) - pd.Timedelta(days=margem_dias)).strftime("%Y-%m-%d")
    caminho = _caminho_cache(tickers, inicio_com_margem, data_fim)

    precos = None
    if os.path.exists(caminho):
        try:
            precos = pd.read_parquet(caminho)
        except Exception:
            precos = None

    if precos is None:
        dados_brutos = _baixar_com_tentativas(tickers, inicio_com_margem, data_fim)
        if dados_brutos is None:
            return None
        precos = _extrair_precos(dados_brutos, tickers)
        if precos is None or precos.empty:
            return None
        try:
            precos.to_parquet(caminho)
        except Exception:
            pass

    retornos = np.log(precos / precos.shift(1)).fillna(0.0)
    datas = retornos.index.strftime("%Y-%m-%d")
    return retornos.loc[(datas >= data_inicio) & (datas <= data_fim)]


def gerar_retornos_sinteticos(tickers, data_inicio, data_fim, eventos=None, semente=42):
    # Garante o indice de mercado, exigido pelo Modelo de Mercado (retorno anormal).
    tickers = list(tickers)
    if INDICE_MERCADO not in tickers:
        tickers = tickers + [INDICE_MERCADO]
    datas = pd.date_range(data_inicio, data_fim, freq="B")
    gerador = np.random.default_rng(semente)
    setor_do_ativo = setor_de_cada_ativo(tickers)

    setores = sorted(set(setor_do_ativo.values()))
    fator_por_setor = {setor: gerador.normal(0, 0.011, len(datas)) for setor in setores}
    fator_mercado = gerador.normal(0, 0.008, len(datas))

    retornos = pd.DataFrame(index=datas)
    for ticker in tickers:
        setor = setor_do_ativo[ticker]
        ruido = gerador.normal(0, 0.006, len(datas))
        retornos[ticker] = 0.6 * fator_por_setor[setor] + 0.4 * fator_mercado + ruido

    if eventos:
        for evento in eventos:
            data = pd.to_datetime(evento["data"])
            if data in retornos.index:
                intensidade = abs(evento.get("goldstein", -5)) / 10.0
                for ticker in tickers:
                    if setor_do_ativo[ticker] in SETORES_SENSIVEIS:
                        retornos.loc[data, ticker] += gerador.normal(0, 0.04) * intensidade
    return retornos

if __name__ == "__main__":
    tickers = tickers_dos_setores(["Energia", "Defesa"])
    eventos = fonte_gdelt.listar_eventos("2022-01-01", "2022-12-31") if False else None
    retornos = gerar_retornos_sinteticos(tickers, "2022-01-01", "2022-12-31")
    print("Retornos:", retornos.shape)