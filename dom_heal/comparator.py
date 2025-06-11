"""
Comparator
==========

Módulo responsável por comparar seletores antigos com o novo DOM para identificar e sugerir ajustes automáticos de seletores quebrados em testes automatizados.

Principais funcionalidades:
- Matching fuzzy entre seletores antigos e novos elementos do DOM (id, name, class, xpath)
- Mecanismo de self-healing para sugerir novos seletores, inclusive via ajuste inteligente de XPath
- Suporte a múltiplos boosts (prefixo, sufixo, palavras, caractere) para maior precisão na recuperação de elementos
- Auxilia na manutenção e robustez de suites de testes automatizados

Ideal para ser utilizado como núcleo de mecanismos de self-healing, integrando-se a frameworks de automação, adaptadores e engines customizadas.
"""

from rapidfuzz import fuzz
from lxml import html
import re

ATRIBUTOS = ['id', 'name', 'class', 'xpath']
LIMIARES_POR_CAMPO = {
    'id': 0.70,
    'name': 0.70,
    'class': 0.60,
    'xpath': 0.80
}

def formatar_selector(campo, valor, tag=None):
    """
    Gera um seletor CSS ou XPath formatado a partir do campo e valor informado.

    Args:
        campo (str): Tipo do seletor (id, name, class, xpath).
        valor (str): Valor do seletor.
        tag (str, optional): Tag HTML para composição de class selectors.

    Returns:
        str: Seletor formatado conforme o tipo.
    """
    if campo == 'id':
        return f'#{valor}'
    elif campo == 'name':
        return f'[name="{valor}"]'
    elif campo == 'class':
        classes = valor.strip().split()
        if tag:
            return f"{tag}." + ".".join(classes)
        return '.' + '.'.join(classes)
    elif campo == 'xpath':
        return valor
    return valor

def detectar_tipo_selector(selector: str) -> str:
    """
    Detecta o tipo do seletor a partir do seu formato textual.

    Args:
        selector (str): Seletor no formato string.

    Returns:
        str: Tipo do seletor ('id', 'name', 'class' ou 'xpath').
    """
    if selector.startswith('#'):
        return 'id'
    elif selector.startswith('[name='):
        return 'name'
    elif selector.startswith('.'):
        return 'class'
    else:
        return 'xpath'

def score_fuzzy(a: str, b: str) -> float:
    """
    Calcula a similaridade fuzzy entre duas strings usando RapidFuzz.

    Args:
        a (str): Primeira string.
        b (str): Segunda string.

    Returns:
        float: Score de similaridade entre 0 e 1.
    """
    return fuzz.ratio(a.lower(), b.lower()) / 100.0

def boost_prefixo(a: str, b: str) -> float:
    """
    Aplica um pequeno bônus se o início das strings for igual.

    Args:
        a (str): String original.
        b (str): String de comparação.

    Returns:
        float: Bônus (0.1) ou 0.
    """
    return 0.1 if b.lower().startswith(a.lower()[:max(2, int(0.5*len(a)))]) else 0

def boost_sufixo(a: str, b: str) -> float:
    """
    Aplica um pequeno bônus se o final das strings for igual.

    Args:
        a (str): String original.
        b (str): String de comparação.

    Returns:
        float: Bônus (0.1) ou 0.
    """
    return 0.1 if b.lower().endswith(a.lower()[-max(2, int(0.5*len(a))):]) else 0

def boost_um_char(a: str, b: str) -> float:
    """
    Aplica bônus se as strings diferirem em apenas um caractere.

    Args:
        a (str): String original.
        b (str): String de comparação.

    Returns:
        float: Bônus (0.1) ou 0.
    """
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    if abs(len(a) - len(b)) > 1:
        return 0
    for i in range(min(len(a), len(b))):
        if a[:i] + a[i+1:] == b or b[:i] + b[i+1:] == a:
            return 0.1
    if len(a) == len(b):
        diff = sum(1 for x, y in zip(a, b) if x != y)
        if diff == 1:
            return 0.1
    return 0

def boost_palavras_iguais(a: str, b: str) -> float:
    """
    Aplica bônus se as palavras contidas nas duas strings forem idênticas.

    Args:
        a (str): String original.
        b (str): String de comparação.

    Returns:
        float: Bônus (0.1) ou 0.
    """
    pa = set(re.findall(r'[a-zA-Z0-9]+', a.lower()))
    pb = set(re.findall(r'[a-zA-Z0-9]+', b.lower()))
    return 0.1 if pa == pb and pa else 0

def aplicar_boost(campo: str, a: str, b: str, fuzzy_score: float):
    """
    Aplica todos os boosts possíveis para 'id' e 'name'.

    Args:
        campo (str): Campo sendo avaliado ('id', 'name', etc).
        a (str): Valor original.
        b (str): Valor de comparação.
        fuzzy_score (float): Score fuzzy base.

    Returns:
        Tuple[float, dict]: Bônus total (máx 0.2) e detalhes dos boosts aplicados.
    """
    boost_details = {}
    if campo in ['id', 'name']:
        bp = boost_prefixo(a, b)
        bs = boost_sufixo(a, b)
        bc = boost_um_char(a, b)
        bw = boost_palavras_iguais(a, b)
        boosts = [bp, bs, bc, bw]
        detail_map = ['prefixo', 'sufixo', 'um_char', 'palavras_iguais']
        boost_details = {k: v for k, v in zip(detail_map, boosts) if v > 0}
        boost_total = min(sum(boosts), 0.20)
        boost_details["boost_total"] = boost_total
        return boost_total, boost_details
    return 0, {"boost_total": 0.0}

def score_class(conj_antigo: set, conj_novo: set) -> float:
    """
    Calcula o melhor score de similaridade entre classes antigas e novas.

    Args:
        conj_antigo (set): Conjunto de classes antigas.
        conj_novo (set): Conjunto de classes novas.

    Returns:
        float: Score de similaridade entre as classes.
    """
    melhor_score = 0
    for classe_antiga in conj_antigo:
        for classe_nova in conj_novo:
            score = fuzz.ratio(classe_antiga, classe_nova) / 100.0
            if score > melhor_score:
                melhor_score = score
    return melhor_score

def validar_xpath(xpath: str, html_dom) -> bool:
    """
    Valida se o XPath existe no DOM fornecido.

    Args:
        xpath (str): XPath a ser validado.
        html_dom (lxml.html.HtmlElement): DOM para busca.

    Returns:
        bool: True se encontrar pelo menos um elemento, False caso contrário.
    """
    try:
        elementos = html_dom.xpath(xpath)
        return len(elementos) > 0
    except Exception:
        return False

def heal_xpath(selector_antigo: str, dom_novo_html: str):
    """
    Realiza tentativa de 'cura' de um XPath quebrado, buscando substituir valores por similares encontrados no novo DOM.

    Args:
        selector_antigo (str): XPath antigo a ser curado.
        dom_novo_html (str): Novo HTML para busca de valores substitutos.

    Returns:
        Tuple[str or None, float or None, None]: XPath sugerido, score médio ou None caso não haja cura possível.
    Raises:
        ValueError: Se o HTML novo está vazio.
    """
    if not dom_novo_html or dom_novo_html.strip() == '':
        raise ValueError("HTML passado para heal_xpath está vazio!")
    if selector_antigo.strip().startswith('//'):
        LIMIAR_XPATH = 0.6
    else:
        LIMIAR_XPATH = 0.8

    pattern = r"(contains\(@(class|id|name),\s*'([^']+)'\))"
    matches = re.findall(pattern, selector_antigo)
    if not matches:
        # Não encontrou pattern válido para curar.
        return None, None, None

    html_dom = html.fromstring(dom_novo_html)
    xpath_sugerido = selector_antigo
    scores = []

    encontrou_alguma_substituicao = False

    for match_full, atributo, valor_antigo in matches:
        melhor_score = 0
        melhor_valor = None

        for elemento in html_dom.xpath(f"//*[@{atributo}]"):
            valor_novo = elemento.get(atributo)
            # Ajuste: se for 'class', compara cada classe individualmente!
            if atributo == "class":
                for classe_indiv in valor_novo.split():
                    score = score_fuzzy(valor_antigo, classe_indiv)
                    if score > melhor_score:
                        melhor_score = score
                        melhor_valor = classe_indiv
            else:
                score = score_fuzzy(valor_antigo, valor_novo)
                if score > melhor_score:
                    melhor_score = score
                    melhor_valor = valor_novo

        if melhor_score >= LIMIAR_XPATH:
            encontrou_alguma_substituicao = True
            xpath_sugerido = xpath_sugerido.replace(match_full, f"contains(@{atributo}, '{melhor_valor}')")
            scores.append(melhor_score)

    # Validação final
    is_valid = False
    if encontrou_alguma_substituicao:
        is_valid = validar_xpath(xpath_sugerido, html_dom)

    if encontrou_alguma_substituicao and is_valid:
        return xpath_sugerido, sum(scores)/len(scores), None
    return None, None, None

def fuzzy_matching_selector(
    selector_antigo: str, dom_novo: list, nome_logico=None, elementos_ja_usados=None, html_puro=None
):
    """
    Busca no novo DOM o melhor elemento equivalente ao selector antigo usando matching fuzzy.

    Args:
        selector_antigo (str): Seletor antigo.
        dom_novo (list): Lista de dicionários do novo DOM.
        nome_logico (str, optional): Nome lógico do elemento (usado para logs/contexto).
        elementos_ja_usados (set, optional): Índices já usados para evitar duplicidade.
        html_puro (str, optional): HTML puro (necessário para healing de xpath).

    Returns:
        Tuple[str or None, dict or None, float, str or None, int or None, dict]:
            Novo seletor, elemento novo, score, tipo, índice, detalhes de boost.
    """
    import re
    tipo = detectar_tipo_selector(selector_antigo)
    seletor_val = selector_antigo
    tag_esperada = None
    if tipo == 'id':
        seletor_val = selector_antigo.lstrip('#')
    elif tipo == 'name':
        match = re.match(r'\[name\s*=\s*[\'"]?(.+?)[\'"]?\]', selector_antigo)
        seletor_val = match.group(1) if match else selector_antigo
    elif tipo == 'class':
        classes_antigas = set(selector_antigo.strip('.').split('.'))
    elif tipo == 'xpath':
        novo_xpath, score, _ = heal_xpath(selector_antigo, html_puro)
        if novo_xpath and novo_xpath != selector_antigo:
            return novo_xpath, None, score, tipo, None, {}
        else:
            return None, None, 0, tipo, None, {}

    candidatos_validos = []

    for idx, elem in enumerate(dom_novo):
        if elementos_ja_usados and idx in elementos_ja_usados:
            continue
        valor = elem.get(tipo, '')
        tag = elem.get('tag')
        if not valor:
            continue

        if tipo == 'class':
            classes_novas = set(valor.strip().split())
            score_total = score_class(classes_antigas, classes_novas)
        else:
            fuzzy_score = score_fuzzy(seletor_val, valor)
            boost, boost_details = aplicar_boost(tipo, seletor_val, valor, fuzzy_score)
            score_total = fuzzy_score + boost

        if score_total >= LIMIARES_POR_CAMPO[tipo]:
            entry = {'score': score_total, 'selector': formatar_selector(tipo, valor, tag=tag), 'elemento': elem, 'campo': tipo, 'idx': idx}
            if tipo in ['id', 'name']:
                entry['boost_details'] = boost_details
            candidatos_validos.append(entry)

    if candidatos_validos:
        candidatos_validos.sort(key=lambda x: (x['score'], x.get('boost_details', {}).get('boost_total', 0)), reverse=True)
        melhor = candidatos_validos[0]
        return melhor['selector'], melhor['elemento'], melhor['score'], tipo, melhor['idx'], melhor.get('boost_details', {})

    return None, None, 0, None, None, {}

def gerar_diferencas(
    antes: list, depois: list, html_puro: str = None, atributos: list = None
) -> dict:
    """
    Gera as diferenças entre dois DOMs, indicando quais seletores foram alterados após o self-healing.

    Args:
        antes (list): Lista de elementos do DOM antigo (dicts).
        depois (list): Lista de elementos do DOM novo (dicts).
        html_puro (str, optional): HTML puro do novo DOM (necessário para healing de xpath).
        atributos (list, optional): Lista de atributos a considerar.

    Returns:
        dict: Dicionário com elementos alterados e seus novos seletores.
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

        novo_selector, elem_novo, score, campo, idx, boost_details = fuzzy_matching_selector(
            selector_antigo, depois, nome_logico, elementos_ja_usados, html_puro=html_puro
        )

        if novo_selector and novo_selector != selector_antigo:
            entry = {'nome': nome_logico, 'selector_antigo': selector_antigo, 'novo_seletor': novo_selector, 'score': score}
            if campo in ['id', 'name']:
                entry["motivo"] = campo
                entry["boost"] = boost_details.get("boost_total", 0) > 0
            alterados.append(entry)
            if idx is not None:
                elementos_ja_usados.add(idx)

    return {'alterados': alterados} if alterados else {}
