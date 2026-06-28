# Impacto de Eventos Exógenos sobre o Mercado Financeiro

Projeto da disciplina **CMAC03 – Algoritmos em Grafos** (UNIFEI). Modela como choques exógenos (conflitos geopolíticos, sanções, desastres) se propagam pelo mercado financeiro, integrando eventos do **GDELT** com cotações reais do **yfinance** em um grafo.

São aplicados três algoritmos de grafos, cada um respondendo a uma pergunta diferente:

| Algoritmo | Pergunta que responde |
|---|---|
| **MST** (Árvore Geradora Mínima) | Qual é o esqueleto do mercado? |
| **Louvain** (Comunidades) | Quais ativos formam grupos que se movem juntos? |
| **Dijkstra** (Caminhos mínimos) | Por onde o choque de um evento se propaga? |

---

## Como funciona

O grafo tem dois tipos de vértice — **eventos** (do GDELT) e **ativos** (do yfinance) — e duas camadas de aresta:

- **Evento → Ativo:** criada quando o ativo apresenta retorno anormal significativo na janela do evento (estudo de eventos, com teste `|z| ≥ 2`).
- **Ativo ↔ Ativo:** correlação de Pearson dos retornos, convertida na distância de Mantegna `d = √(2(1−ρ))` para a MST e o Dijkstra.

Os preços viram **retornos logarítmicos** `R = ln(Pₜ / Pₜ₋₁)`.

---

## Instalação

Requer Python 3.9+.

```bash
pip install yfinance pandas numpy networkx matplotlib pyarrow python-louvain
```

---

## Como usar

Rodar tudo (calcula as tabelas e gera as figuras):

```bash
python main.py
```

Cada módulo também roda sozinho, com um exemplo embutido:

```bash
python algo_mst.py
python algo_louvain.py
python algo_dijkstra.py
```

### Sem internet

Se o yfinance estiver bloqueado, defina no topo de `main.py`:

```python
USAR_DADOS_REAIS = False
```

Isso usa um gerador de dados sintéticos com correlação por setor, permitindo testar toda a lógica offline. Em uso normal, o download real fica em cache na pasta `cache_yf/`, então cada combinação de ativos e período é baixada apenas uma vez.

---

## Resultados gerados

Após `python main.py`, a pasta `resultados/` contém:

| Arquivo | Conteúdo |
|---|---|
| `tab_dataset.csv` | Nº de ativos, eventos, pregões e período |
| `tab_mst.csv` | Hub central, comprimento total e ativos periféricos da árvore |
| `tab_louvain.csv` | Comunidades detectadas × setor real, com tamanho e pureza |
| `tab_dijkstra.csv` | Ordem de propagação do contágio a partir da origem |
| `tab_validacao.csv` | Ativos com retorno anormal significativo por evento |
| `fig_mst.png` | Árvore do mercado; nó maior = hub, cor = setor |
| `fig_louvain.png` | Comunidades coloridas |
| `fig_dijkstra.png` | Árvore de contágio a partir da origem |
| `fig_impacto_eventos.png` | Nº de ativos impactados por evento |

Como ler as métricas: o **hub** da MST é o principal eixo de transmissão de risco; a **modularidade Q** acima de 0,3 indica comunidades reais; a **pureza** perto de 1,0 mostra que as comunidades recuperaram os setores; no **Dijkstra**, os ativos mais próximos da origem são os primeiros alcançados pela cascata.

---

## Estrutura do projeto

```
fonte_gdelt.py       Eventos exógenos
fonte_yfinance.py    Preços e retornos (com cache e nova tentativa)
grafo_base.py        Grafos de correlação e de distância
algo_mst.py          Árvore Geradora Mínima
algo_louvain.py      Detecção de comunidades
algo_dijkstra.py     Caminhos de contágio
experimentos.py      Cálculo das tabelas e validação por estudo de eventos
visualizacao.py      Geração de todas as figuras
main.py              Roda tudo e salva os resultados
```

Cada módulo tem uma responsabilidade única. O cálculo dos algoritmos está separado da geração de figuras (`visualizacao.py`).

---

## Parâmetros

No topo de `main.py`:

| Parâmetro | Significado |
|---|---|
| `SETORES` | Quais grupos de ativos usar |
| `DATA_INICIO` / `DATA_FIM` | Janela de análise |
| `EVENTO_FOCO` | Evento usado no Dijkstra |
| `LIMIAR_CORRELACAO` | Correlação mínima para criar aresta no Louvain |
| `LIMIAR_Z` | Desvios-padrão para considerar um retorno anormal |
| `JANELA_EVENTO` | Dias da janela do evento |
| `JANELA_ESTIMACAO` | Dias da janela de estimação |
| `USAR_DADOS_REAIS` | `True` = yfinance; `False` = sintético |

Para usar a base completa do GDELT, preencha `carregar_eventos_gdelt()` em `fonte_gdelt.py` com a consulta ao BigQuery.

---

## Limitações

- A correlação de Pearson captura apenas relações lineares.
- Os caminhos do Dijkstra indicam associação e proximidade estrutural, não causalidade.
- O critério `|z| ≥ 2` assume normalidade aproximada dos retornos.
