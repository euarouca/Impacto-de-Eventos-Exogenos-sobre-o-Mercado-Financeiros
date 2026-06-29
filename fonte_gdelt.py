CATALOGO_EVENTOS = [
    {"id": "crimeia_2014",      "data": "2014-03-18", "rotulo": "Anexacao da Crimeia",            "goldstein": -9.0},
    {"id": "queda_petroleo_2014", "data": "2014-11-28", "rotulo": "OPEP nao corta producao",      "goldstein": -4.0},
    {"id": "brexit_2016",       "data": "2016-06-24", "rotulo": "Resultado do Brexit",            "goldstein": -5.0},
    {"id": "guerra_comercial_2018", "data": "2018-07-06", "rotulo": "Guerra comercial EUA-China", "goldstein": -6.0},
    {"id": "soleimani_2020",    "data": "2020-01-03", "rotulo": "Morte de Soleimani",             "goldstein": -9.0},
    {"id": "covid_2020",        "data": "2020-03-11", "rotulo": "Pandemia de COVID-19",           "goldstein": -8.0},
    {"id": "petroleo_negativo_2020", "data": "2020-04-20", "rotulo": "Petroleo WTI negativo",     "goldstein": -7.0},
    {"id": "ucrania_2022",      "data": "2022-02-24", "rotulo": "Invasao da Ucrania",             "goldstein": -10.0},
    {"id": "sancoes_2022",      "data": "2022-02-28", "rotulo": "Sancoes a Russia",               "goldstein": -9.0},
    {"id": "embargo_2022",      "data": "2022-03-08", "rotulo": "Embargo ao petroleo russo",      "goldstein": -9.0},
    {"id": "svb_2023",          "data": "2023-03-10", "rotulo": "Colapso do Silicon Valley Bank", "goldstein": -7.0},
    {"id": "israel_2023",       "data": "2023-10-07", "rotulo": "Ataque Hamas-Israel",            "goldstein": -10.0},
]


def listar_eventos(data_inicio=None, data_fim=None):
    eventos = CATALOGO_EVENTOS
    if data_inicio is not None:
        eventos = [evento for evento in eventos if evento["data"] >= data_inicio]
    if data_fim is not None:
        eventos = [evento for evento in eventos if evento["data"] <= data_fim]
    return sorted(eventos, key=lambda evento: evento["data"])


def carregar_eventos_gdelt(data_inicio, data_fim, project_id, minimo_artigos=200, goldstein_maximo=-7.0, limite=50):
    import pandas_gbq  # importado aqui para o projeto rodar sem a dependencia do BigQuery
    consulta = f'''
      SELECT CAST(SQLDATE AS STRING) AS data, EventCode, GoldsteinScale,
             Actor1Name, Actor2Name, NumArticles
      FROM `gdelt-bq.gdeltv2.events`
      WHERE SQLDATE BETWEEN {int(data_inicio.replace("-", ""))}
                        AND {int(data_fim.replace("-", ""))}
        AND NumArticles >= {minimo_artigos}
        AND GoldsteinScale <= {goldstein_maximo}
      ORDER BY NumArticles DESC
      LIMIT {limite}
    '''
    dados = pandas_gbq.read_gbq(consulta, project_id=project_id)
    return [{"id": f"gdelt_{linha.EventCode}_{linha.data}",
             "data": linha.data,
             "rotulo": f"{linha.Actor1Name}-{linha.Actor2Name}",
             "goldstein": float(linha.GoldsteinScale)}
            for linha in dados.itertuples()]


if __name__ == "__main__":
    for evento in listar_eventos("2022-01-01", "2022-12-31"):
        print(evento["data"], evento["rotulo"], evento["goldstein"])
