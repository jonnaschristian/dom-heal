"""
Módulo de comparação: funções para ler seletores do JSON antigo e gerar diferenças em relação ao DOM atual da página.
"""

import json
from pathlib import Path
from rapidfuzz import fuzz

# Atributos padrão para comparação
ATRIBUTOS_PADRAO = ['id', 'class', 'text', 'name', 'type', 'aria_label']
# Limiar padrão para comparação fuzzy
LIMIAR_PADRAO = 0.7

def ler_json_elementos(caminho: Path) -> list:
    """
    Lê um arquivo JSON contendo os seletores antigos e retorna uma lista de elementos.
    """
    try:
        return json.loads(Path(caminho).read_text(encoding='utf-8'))
    except Exception:
        return []

def gerar_diferencas(
    antes: list,
    depois: list,
    atributos: list = None,
    limiar: float = None
) -> dict:
    """
    Compara o JSON de seletores antigos (antes) com o DOM atual (depois) e retorna as diferenças estruturais:
      - movidos: elementos que mudaram de XPath por ID ou similaridade fuzzy
      - removidos: XPaths que existiam em 'antes' e sumiram em 'depois'
      - adicionados: XPaths novos em 'depois'
      - alterados: mesmos XPaths com mudanças em atributos

    Retorno:
        dict: Estrutura com chaves 'movidos', 'removidos', 'adicionados', 'alterados'.
    """
    atributos = list(atributos or ATRIBUTOS_PADRAO)
    limiar = limiar if limiar is not None else LIMIAR_PADRAO

    # Atributos data-*
    atributos_data = {
        chave for elemento in antes + depois for chave in elemento.keys()
        if chave.startswith('data_') and chave not in atributos
    }
    atributos.extend(sorted(atributos_data))

    # Mapa por XPath
    mapa_antes  = {elemento['xpath']: elemento for elemento in antes}
    mapa_depois = {elemento['xpath']: elemento for elemento in depois}

    removidos   = set(mapa_antes) - set(mapa_depois)
    adicionados = set(mapa_depois) - set(mapa_antes)
    movidos     = []

    # Detecta movimento por ID
    ids_antes  = {elemento.get('id'): xp for xp, elemento in mapa_antes.items() if elemento.get('id')}
    ids_depois = {elemento.get('id'): xp for xp, elemento in mapa_depois.items() if elemento.get('id')}
    for valor_id, xp_antes in ids_antes.items():
        xp_depois = ids_depois.get(valor_id)
        if xp_depois and xp_depois != xp_antes:
            movidos.append({'id': valor_id, 'de': xp_antes, 'para': xp_depois})
            removidos.discard(xp_antes)
            adicionados.discard(xp_depois)

    # Detecta movimento por similaridade (fuzzy)
    for xp_antes in list(removidos):
        elemento_antes = mapa_antes[xp_antes]
        for xp_depois in list(adicionados):
            elemento_depois = mapa_depois[xp_depois]
            str_antes = ' '.join([elemento_antes.get('tag', '')] + [str(elemento_antes.get(a, '')) for a in atributos])
            str_depois = ' '.join([elemento_depois.get('tag', '')] + [str(elemento_depois.get(a, '')) for a in atributos])

            score = fuzz.ratio(str_antes, str_depois) / 100.0
            if score >= limiar:
                movidos.append({'similaridade': score*100, 'de': xp_antes, 'para': xp_depois})
                removidos.discard(xp_antes)
                adicionados.discard(xp_depois)
                break

    # Alterações de atributos
    alterados = []
    for xp in set(mapa_antes) & set(mapa_depois):
        diferencas = {}
        for atributo in atributos:
            valor_antes = mapa_antes[xp].get(atributo)
            valor_depois = mapa_depois[xp].get(atributo)
            if valor_antes != valor_depois:
                diferencas[atributo] = {'antes': valor_antes, 'depois': valor_depois}
        if diferencas:
            alterados.append({'xpath': xp, 'diferencas': diferencas})

    ordenado_removidos   = [elemento['xpath'] for elemento in antes  if elemento['xpath'] in removidos]
    ordenado_adicionados = [elemento['xpath'] for elemento in depois if elemento['xpath'] in adicionados]

    diferencas = {
        'movidos': movidos,
        'removidos': ordenado_removidos,
        'adicionados': ordenado_adicionados,
        'alterados': alterados
    }

    # (Opcional) Remover entradas vazias:
    diferencas = {k: v for k, v in diferencas.items() if v}

    return diferencas
