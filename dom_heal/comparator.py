"""
Comparator
==========

Módulo responsável por comparar seletores antigos do teste automatizado com o novo DOM,
sugerindo seletores alternativos de forma inteligente via fuzzy e boosts.

Matching por id, name, class ou xpath. Prioriza o mesmo tipo de seletor original,
aplicando boosts só quando necessário. Sem penalidades, apenas incrementos positivos.
"""

from rapidfuzz import fuzz

ATRIBUTOS = ['id', 'name', 'class', 'xpath']
LIMIARES_POR_CAMPO = {
    'id': 0.70,
    'name': 0.70,
    'class': 0.70,
    'xpath': 0.80
}

def formatar_selector(campo, valor):
    """Formata o seletor CSS/XPath conforme o atributo."""
    if campo == 'id':
        return f'#{valor}'
    elif campo == 'name':
        return f'[name="{valor}"]'
    elif campo == 'class':
        return f'.{valor.split()[0]}'  # pega apenas a primeira classe para consistência
    elif campo == 'xpath':
        return valor
    return valor

def detectar_tipo_selector(selector: str) -> str:
    """Detecta o tipo do seletor a partir da string."""
    if selector.startswith('#'):
        return 'id'
    elif selector.startswith('[name='):
        return 'name'
    elif selector.startswith('.'):
        return 'class'
    else:
        return 'xpath'

def score_fuzzy(selector_antigo, candidato):
    """Calcula o score fuzzy base entre duas strings."""
    return fuzz.ratio(selector_antigo.lower(), candidato.lower()) / 100.0

def boost_prefixo(a, b):
    """+0.05 se prefixo for igual."""
    return 0.05 if b.lower().startswith(a.lower()[:max(2, int(0.5*len(a)))]) else 0

def boost_sufixo(a, b):
    """+0.05 se sufixo for igual."""
    return 0.05 if b.lower().endswith(a.lower()[-max(2, int(0.5*len(a))):]) else 0

def boost_um_char(a, b):
    """+0.05 se diferença de um caractere (adicionado, removido ou trocado)."""
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    if abs(len(a) - len(b)) > 1:
        return 0
    # Removido ou adicionado
    for i in range(min(len(a), len(b))):
        if a[:i] + a[i+1:] == b or b[:i] + b[i+1:] == a:
            return 0.05
    # Trocado
    if len(a) == len(b):
        diff = sum(1 for x, y in zip(a, b) if x != y)
        if diff == 1:
            return 0.05
    return 0

def boost_palavras_iguais(a, b):
    """+0.05 se as palavras forem iguais em qualquer ordem."""
    import re
    palavras_a = set(re.findall(r'[a-zA-Z0-9]+', a.lower()))
    palavras_b = set(re.findall(r'[a-zA-Z0-9]+', b.lower()))
    return 0.05 if palavras_a == palavras_b and palavras_a else 0

def fuzzy_matching_selector(selector_antigo, dom_novo, nome_logico=None, elementos_ja_usados=None):
    """
    Matching fuzzy, priorizando o mesmo tipo do seletor original. 
    Boost só para scores entre 0.50 e <0.70.
    Fallback só se nenhum candidato do mesmo tipo atingir score suficiente.
    """
    tipo = detectar_tipo_selector(selector_antigo)
    if tipo == 'id':
        seletor_val = selector_antigo.lstrip('#')
    elif tipo == 'name':
        import re
        match = re.match(r'\[name\s*=\s*[\'"]?(.+?)[\'"]?\]', selector_antigo)
        seletor_val = match.group(1) if match else selector_antigo
    elif tipo == 'class':
        seletor_val = selector_antigo.lstrip('.')
    else:
        seletor_val = selector_antigo

    # Matching exato pelo tipo prioritário
    for idx, elem in enumerate(dom_novo):
        if elementos_ja_usados and idx in elementos_ja_usados:
            continue
        valor = elem.get(tipo, '')
        if valor and (valor == seletor_val or valor == nome_logico):
            return (formatar_selector(tipo, valor), elem, 1.0, tipo, idx)

    # Matching fuzzy e boosts apenas no tipo prioritário
    candidatos_validos = []
    for idx, elem in enumerate(dom_novo):
        if elementos_ja_usados and idx in elementos_ja_usados:
            continue
        valor = elem.get(tipo, '')
        if not valor:
            continue
        fuzzy = score_fuzzy(seletor_val, valor)
        score_total = fuzzy
        if 0.5 <= fuzzy < 0.7:
            score_total += (
                boost_prefixo(seletor_val, valor) +
                boost_sufixo(seletor_val, valor) +
                boost_um_char(seletor_val, valor) +
                boost_palavras_iguais(seletor_val, valor)
            )
        if score_total >= LIMIARES_POR_CAMPO[tipo]:
            candidatos_validos.append({
                'score': score_total,
                'selector': formatar_selector(tipo, valor),
                'elemento': elem,
                'campo': tipo,
                'idx': idx
            })
    if candidatos_validos:
        melhor = max(candidatos_validos, key=lambda x: x['score'])
        return (melhor['selector'], melhor['elemento'], melhor['score'], tipo, melhor['idx'])

    # Fallback: tenta nos outros atributos (id, name, class, xpath)
    for campo in ATRIBUTOS:
        if campo == tipo:
            continue
        for idx, elem in enumerate(dom_novo):
            if elementos_ja_usados and idx in elementos_ja_usados:
                continue
            valor = elem.get(campo, '')
            if valor and (valor == seletor_val or valor == nome_logico):
                return (formatar_selector(campo, valor), elem, 1.0, campo, idx)
            fuzzy = score_fuzzy(seletor_val, valor)
            score_total = fuzzy
            if 0.5 <= fuzzy < 0.7:
                score_total += (
                    boost_prefixo(seletor_val, valor) +
                    boost_sufixo(seletor_val, valor) +
                    boost_um_char(seletor_val, valor) +
                    boost_palavras_iguais(seletor_val, valor)
                )
            if score_total >= LIMIARES_POR_CAMPO.get(campo, 0.7):
                return (formatar_selector(campo, valor), elem, score_total, campo, idx)

    return None, None, 0, None, None

def gerar_diferencas(antes: list, depois: list, atributos: list = None) -> dict:
    """
    Função principal chamada pelo engine.
    Recebe dois estados de elementos (antes, depois) e retorna um dict dos seletores alterados
    conforme o matching heurístico, respeitando o controle de duplicidade.
    """
    antes = [el for el in antes if isinstance(el, dict)]
    depois = [el for el in depois if isinstance(el, dict)]
    atributos = list(atributos or ATRIBUTOS)

    alterados = []
    elementos_ja_usados = set()

    for elem_qa in antes:
        nome_logico = elem_qa.get('nome')
        selector_antigo = elem_qa.get('selector')
        if not selector_antigo:
            continue

        novo_selector, elem_novo, score, campo, idx = fuzzy_matching_selector(
            selector_antigo, depois, nome_logico=nome_logico, elementos_ja_usados=elementos_ja_usados
        )

        if novo_selector and novo_selector != selector_antigo:
            alterados.append({
                'nome': nome_logico,
                'selector_antigo': selector_antigo,
                'novo_seletor': novo_selector,
                'score': score,
                'motivo': f'matching_{campo}_{score:.2f}',
                'xpath': elem_novo.get('xpath') if elem_novo else None,
                'tag': elem_novo.get('tag') if elem_novo else None
            })
            if idx is not None:
                elementos_ja_usados.add(idx)

    return {'alterados': alterados} if alterados else {}
