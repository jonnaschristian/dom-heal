# comparator_simplificado.py
# Biblioteca de comparação de snapshots do DOM com pontuação fuzzy real

import json
from pathlib import Path
from rapidfuzz import fuzz

# Atributos padrão para comparação
ATRIBUTOS_PADRAO = ['id', 'class', 'text', 'name', 'type', 'aria_label']
# Limiar padrão para comparação fuzzy (0.0 a 1.0)
LIMIAR_PADRAO = 0.7


def ler_snapshot(caminho: Path) -> list:
    """
    Lê um arquivo JSON com snapshot de DOM e retorna lista de elementos
    """
    try:
        conteudo = caminho.read_text(encoding='utf-8')
        return json.loads(conteudo)
    except Exception:
        return []


def gerar_diferencas(
    antes: list,
    depois: list,
    atributos: list = None,
    limiar: float = None
) -> dict:
    """
    Compara dois snapshots e retorna dict com movidos, removidos, adicionados e alterados,
    usando pontuação fuzzy real entre 0 e 1.
    """
    if atributos is None:
        atributos = ATRIBUTOS_PADRAO.copy()
    if limiar is None:
        limiar = LIMIAR_PADRAO

    # Inclui dinamicamente atributos data-*
    data_attrs = set()
    for el in antes + depois:
        for k in el.keys():
            if k.startswith('data_') and k not in atributos:
                data_attrs.add(k)
    atributos.extend(sorted(data_attrs))

    # Mapeia cada elemento pelo seu XPath
    mapa_antes = {e['xpath']: e for e in antes}
    mapa_depois = {e['xpath']: e for e in depois}

    removidos = set(mapa_antes) - set(mapa_depois)
    adicionados = set(mapa_depois) - set(mapa_antes)
    movidos = []

    # Detecta movimentos por id
    ids_antes = {el['id']: xp for xp, el in mapa_antes.items() if el.get('id')}
    ids_depois = {el['id']: xp for xp, el in mapa_depois.items() if el.get('id')}
    for id_valor, xp_antes in ids_antes.items():
        xp_depois = ids_depois.get(id_valor)
        if xp_depois and xp_depois != xp_antes:
            movidos.append({'id': id_valor, 'de': xp_antes, 'para': xp_depois})

    # Detecta movimentos fuzzy
    for xp_antes in list(removidos):
        el_antes = mapa_antes[xp_antes]
        for xp_depois in list(adicionados):
            el_depois = mapa_depois[xp_depois]
            # concatena atributos e tag como string para fuzzy
            fp_antes = ' '.join([el_antes['tag']] + [str(el_antes.get(a, '')) for a in atributos])
            fp_depois = ' '.join([el_depois['tag']] + [str(el_depois.get(a, '')) for a in atributos])

            # fuzz.ratio retorna 0-100, normalizamos para 0-1
            score_percent = fuzz.ratio(fp_antes, fp_depois)
            similaridade = score_percent / 100.0

            if similaridade >= limiar:
                movidos.append({
                    'similaridade': similaridade * 100,  # armazena porcentagem real
                    'de': xp_antes,
                    'para': xp_depois
                })
                removidos.discard(xp_antes)
                adicionados.discard(xp_depois)
                break

    alterados = []
    # Mesmos XPaths mas atributos mudaram
    for xp in set(mapa_antes) & set(mapa_depois):
        diff = {}
        for attr in atributos:
            before_val = mapa_antes[xp].get(attr)
            after_val = mapa_depois[xp].get(attr)
            if before_val != after_val:
                diff[attr] = {'antes': before_val, 'depois': after_val}
        if diff:
            alterados.append({'xpath': xp, 'diferencas': diff})

    return {
        'movidos': movidos,
        'removidos': list(removidos),
        'adicionados': list(adicionados),
        'alterados': alterados
    }
