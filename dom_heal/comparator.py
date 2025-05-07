"""
Módulo comparator: funções para ler snapshots de DOM e gerar diferenças entre eles.
"""

import json
from pathlib import Path
from rapidfuzz import fuzz

# Atributos padrão para comparação
ATRIBUTOS_PADRAO = ['id', 'class', 'text', 'name', 'type', 'aria_label']
# Limiar padrão para comparação fuzzy
LIMIAR_PADRAO = 0.7


def ler_snapshot(caminho: Path) -> list:
    """
    Lê um arquivo JSON contendo um snapshot do DOM e retorna uma lista de elementos.

    Args:
        caminho (Path): Caminho para o arquivo JSON do snapshot.

    Returns:
        list: Lista de dicionários representando elementos; vazia se falhar ao ler/parsing.
    """
    try:
        return json.loads(caminho.read_text(encoding='utf-8'))
    except Exception:
        return []


def gerar_diferencas(
    antes: list,
    depois: list,
    atributos: list = None,
    limiar: float = None
) -> dict:
    """
    Compara dois snapshots (listas de dicionários) e retorna as diferenças estruturais:

      - movidos: elementos que mudaram de XPath por ID ou similaridade fuzzy
      - removidos: XPaths que existiam em 'antes' e sumiram em 'depois'
      - adicionados: XPaths novos em 'depois'
      - alterados: mesmos XPaths com mudanças em atributos

    Args:
        antes (list): Snapshot inicial (t0) como lista de dicionários.
        depois (list): Snapshot posterior (t1) como lista de dicionários.
        atributos (list, optional): Lista de atributos a considerar; usa ATRIBUTOS_PADRAO se None.
        limiar (float, optional): Limiar para comparação fuzzy (0.0 a 1.0); usa LIMIAR_PADRAO se None.

    Returns:
        dict: Estrutura com chaves 'movidos', 'removidos', 'adicionados', 'alterados'.
    """

    # 1) Defaults
    atributos = list(atributos or ATRIBUTOS_PADRAO)
    limiar = limiar if limiar is not None else LIMIAR_PADRAO

    # 2) Atributos data-*
    data_attrs = {
        k for el in antes + depois for k in el.keys()
        if k.startswith('data_') and k not in atributos
    }
    atributos.extend(sorted(data_attrs))

    # 3) Mapa por XPath
    mapa_antes  = {e['xpath']: e for e in antes}
    mapa_depois = {e['xpath']: e for e in depois}

    # 4) Conjuntos iniciais
    removidos   = set(mapa_antes) - set(mapa_depois)
    adicionados = set(mapa_depois) - set(mapa_antes)
    movidos     = []

    # 5) Detecta movimento por ID
    ids_antes  = {el['id']: xp for xp, el in mapa_antes.items()  if el.get('id')}
    ids_depois = {el['id']: xp for xp, el in mapa_depois.items() if el.get('id')}
    for id_valor, xp_antes in ids_antes.items():
        xp_depois = ids_depois.get(id_valor)
        if xp_depois and xp_depois != xp_antes:
            movidos.append({'id': id_valor, 'de': xp_antes, 'para': xp_depois})
            removidos.discard(xp_antes)
            adicionados.discard(xp_depois)

    # 6) Detecta movimento FUZZY
    for xp_antes in list(removidos):
        el_a = mapa_antes[xp_antes]
        for xp_depois in list(adicionados):
            el_d = mapa_depois[xp_depois]
            s_a = ' '.join([el_a.get('tag','')] + [str(el_a.get(a,'')) for a in atributos])
            s_d = ' '.join([el_d.get('tag','')] + [str(el_d.get(a,'')) for a in atributos])

            score = fuzz.ratio(s_a, s_d) / 100.0
            if score >= limiar:
                movidos.append({'similaridade': score*100, 'de': xp_antes, 'para': xp_depois})
                removidos.discard(xp_antes)
                adicionados.discard(xp_depois)
                break

    # 7) Detecta alterações de atributos
    alterados = []
    for xp in set(mapa_antes) & set(mapa_depois):
        diffs = {}
        for a in atributos:
            b = mapa_antes[xp].get(a); d = mapa_depois[xp].get(a)
            if b != d:
                diffs[a] = {'antes': b, 'depois': d}
        if diffs:
            alterados.append({'xpath': xp, 'diferencas': diffs})

    # 8) Ordena preservando hierarquia
    ordenado_removidos   = [e['xpath'] for e in antes  if e['xpath'] in removidos]
    ordenado_adicionados = [e['xpath'] for e in depois if e['xpath'] in adicionados]

    return {
        'movidos': movidos,
        'removidos': ordenado_removidos,
        'adicionados': ordenado_adicionados,
        'alterados': alterados
    }
