import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import networkx as nx


def _cores_por_setor(nos, setor_do_ativo):
    setores = sorted(set(setor_do_ativo.get(no, "Outros") for no in nos))
    paleta = plt.cm.tab10
    cor_do_setor = {setor: paleta(i % 10) for i, setor in enumerate(setores)}
    return [cor_do_setor[setor_do_ativo.get(no, "Outros")] for no in nos], cor_do_setor


def desenhar_mst(arvore, setor_do_ativo, caminho="fig_mst.png"):
    graus = dict(arvore.degree())
    posicoes = nx.spring_layout(arvore, seed=42, k=0.6)
    cores, cor_do_setor = _cores_por_setor(arvore.nodes(), setor_do_ativo)
    tamanhos = [300 + graus[no] * 250 for no in arvore.nodes()]

    plt.figure(figsize=(13, 10))
    nx.draw_networkx_edges(arvore, posicoes, edge_color="#888", width=1.5, alpha=0.7)
    nx.draw_networkx_nodes(arvore, posicoes, node_color=cores, node_size=tamanhos,
                           edgecolors="white", linewidths=1.5)
    nx.draw_networkx_labels(arvore, posicoes, font_size=8, font_weight="bold")
    legenda = [Patch(color=cor, label=setor) for setor, cor in cor_do_setor.items()]
    plt.legend(handles=legenda, loc="upper left", fontsize=8)
    plt.title("Arvore Geradora Minima do mercado", fontweight="bold")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(caminho, dpi=180, bbox_inches="tight")
    plt.close()
    return caminho


def desenhar_comunidades(grafo, particao, caminho="fig_louvain.png"):
    posicoes = nx.spring_layout(grafo, seed=42, weight="weight", k=0.5)
    comunidades = sorted(set(particao.values()))
    paleta = plt.cm.Set2
    cor_da_comunidade = {comunidade: paleta(i % 8) for i, comunidade in enumerate(comunidades)}
    cores = [cor_da_comunidade[particao[no]] for no in grafo.nodes()]

    plt.figure(figsize=(13, 10))
    nx.draw_networkx_edges(grafo, posicoes, edge_color="#ccc", width=0.6, alpha=0.5)
    nx.draw_networkx_nodes(grafo, posicoes, node_color=cores, node_size=600,
                           edgecolors="white", linewidths=1.5)
    nx.draw_networkx_labels(grafo, posicoes, font_size=8, font_weight="bold")
    legenda = [Patch(color=cor, label=f"Comunidade {c}") for c, cor in cor_da_comunidade.items()]
    plt.legend(handles=legenda, loc="upper left", fontsize=8)
    plt.title("Comunidades de ativos (Louvain)", fontweight="bold")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(caminho, dpi=180, bbox_inches="tight")
    plt.close()
    return caminho


def desenhar_contagio(grafo, origem, caminhos, distancias, caminho="fig_dijkstra.png"):
    posicoes = nx.spring_layout(grafo, seed=42, k=0.6)

    arestas_da_arvore = set()
    for caminho_ate_no in caminhos.values():
        for inicio, fim in zip(caminho_ate_no[:-1], caminho_ate_no[1:]):
            arestas_da_arvore.add(tuple(sorted((inicio, fim))))
    todas = [tuple(sorted(aresta)) for aresta in grafo.edges()]
    da_arvore = [aresta for aresta in todas if aresta in arestas_da_arvore]
    fora = [aresta for aresta in todas if aresta not in arestas_da_arvore]

    distancia_maxima = max(distancias.values()) if distancias else 1.0
    cores = []
    for no in grafo.nodes():
        if no == origem:
            cores.append("#000000")
        else:
            proximidade = 1 - distancias.get(no, distancia_maxima) / distancia_maxima
            cores.append(plt.cm.YlOrRd(proximidade))

    plt.figure(figsize=(13, 10))
    nx.draw_networkx_edges(grafo, posicoes, edgelist=fora, edge_color="#eee",
                           width=0.5, alpha=0.4)
    nx.draw_networkx_edges(grafo, posicoes, edgelist=da_arvore, edge_color="#e74c3c",
                           width=2.0, alpha=0.8)
    nx.draw_networkx_nodes(grafo, posicoes, node_color=cores, node_size=500,
                           edgecolors="white", linewidths=1.5)
    nx.draw_networkx_labels(grafo, posicoes, font_size=8, font_weight="bold")
    plt.title(f"Caminhos de contagio a partir de {origem}", fontweight="bold")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(caminho, dpi=180, bbox_inches="tight")
    plt.close()
    return caminho


def desenhar_impacto_por_evento(tabela_validacao, caminho="fig_impacto_eventos.png"):
    cores = ["#27ae60" if valor == 0 else "#c0392b"
             for valor in tabela_validacao["ativos_significativos"]]
    plt.figure(figsize=(11, 5))
    plt.bar(range(len(tabela_validacao)), tabela_validacao["ativos_significativos"], color=cores)
    plt.xticks(range(len(tabela_validacao)), tabela_validacao["data"],
               rotation=45, ha="right", fontsize=8)
    plt.ylabel("Ativos com retorno anormal significativo")
    plt.title("Impacto por evento", fontweight="bold")
    plt.tight_layout()
    plt.savefig(caminho, dpi=170, bbox_inches="tight")
    plt.close()
    return caminho


def desenhar_evento_ativo(grafo, setor_do_ativo, caminho="fig_evento_ativo.png", subtitulo=None):
    eventos = sorted([no for no, dados in grafo.nodes(data=True) if dados.get("tipo") == "evento"],
                     key=lambda no: grafo.nodes[no].get("data", ""))
    ativos = sorted([no for no, dados in grafo.nodes(data=True) if dados.get("tipo") == "ativo"])

    def coluna(itens, x):
        divisor = max(len(itens) - 1, 1)
        return {item: (x, 1.0 - i / divisor) for i, item in enumerate(itens)}

    posicoes = {}
    posicoes.update(coluna(eventos, 0.0))
    posicoes.update(coluna(ativos, 1.0))

    cores_ativos, cor_do_setor = _cores_por_setor(ativos, setor_do_ativo)

    altura = max(6.0, 0.7 * max(len(eventos), len(ativos)))
    plt.figure(figsize=(12, altura))

    # Arestas: azul = retorno anormal positivo, vermelho = negativo; largura ~ |z|.
    for origem, destino, dados in grafo.edges(data=True):
        z = dados.get("z", 0.0)
        cor = "#2471a3" if z > 0 else "#c0392b"
        largura = 1.0 + min(abs(z), 10) / 2.2
        nx.draw_networkx_edges(grafo, posicoes, edgelist=[(origem, destino)],
                               edge_color=cor, width=largura, alpha=0.85)

    nx.draw_networkx_nodes(grafo, posicoes, nodelist=eventos, node_shape="s",
                           node_color="#34495e", node_size=900, edgecolors="white",
                           linewidths=1.5)
    nx.draw_networkx_nodes(grafo, posicoes, nodelist=ativos, node_color=cores_ativos,
                           node_size=900, edgecolors="white", linewidths=1.5)

    for no in eventos:
        x, y = posicoes[no]
        plt.text(x - 0.04, y, f'{grafo.nodes[no].get("data","")}\n{no}',
                 ha="right", va="center", fontsize=7, fontweight="bold")
    for ativo in ativos:
        x, y = posicoes[ativo]
        plt.text(x + 0.04, y, ativo, ha="left", va="center", fontsize=8, fontweight="bold")

    etiquetas = {(u, v): f'{dados.get("z", 0):+.1f}' for u, v, dados in grafo.edges(data=True)}
    nx.draw_networkx_edge_labels(grafo, posicoes, edge_labels=etiquetas, font_size=6,
                                 label_pos=0.5, rotate=False,
                                 bbox=dict(boxstyle="round,pad=0.1", fc="white",
                                           ec="none", alpha=0.6))

    legenda = [Patch(color="#2471a3", label="Choque positivo (z > 0)"),
               Patch(color="#c0392b", label="Choque negativo (z < 0)")]
    legenda += [Patch(color=cor, label=setor) for setor, cor in cor_do_setor.items()]
    plt.legend(handles=legenda, loc="upper center", bbox_to_anchor=(0.5, -0.01),
               ncol=3, fontsize=8, frameon=False)
    titulo = "Grafo bipartido evento -> ativo (choques |z| >= 2)"
    if subtitulo:
        titulo += f"\n{subtitulo}"
    plt.title(titulo, fontweight="bold", fontsize=11)
    plt.xlim(-0.55, 1.45)
    plt.ylim(-0.12, 1.12)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(caminho, dpi=180, bbox_inches="tight")
    plt.close()
    return caminho
