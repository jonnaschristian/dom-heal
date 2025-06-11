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
    if selector.startswith('#'):
        return 'id'
    elif selector.startswith('[name='):
        return 'name'
    elif selector.startswith('.'):
        return 'class'
    else:
        return 'xpath'

def score_fuzzy(a, b):
    return fuzz.ratio(a.lower(), b.lower()) / 100.0

# Boost somente em id e name (mantido exatamente como estava)
def boost_prefixo(a, b):
    return 0.1 if b.lower().startswith(a.lower()[:max(2, int(0.5*len(a)))]) else 0

def boost_sufixo(a, b):
    return 0.1 if b.lower().endswith(a.lower()[-max(2, int(0.5*len(a))):]) else 0

def boost_um_char(a, b):
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

def boost_palavras_iguais(a, b):
    pa = set(re.findall(r'[a-zA-Z0-9]+', a.lower()))
    pb = set(re.findall(r'[a-zA-Z0-9]+', b.lower()))
    return 0.1 if pa == pb and pa else 0

def aplicar_boost(campo, a, b, fuzzy_score):
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

def score_class(conj_antigo, conj_novo):
    melhor_score = 0
    for classe_antiga in conj_antigo:
        for classe_nova in conj_novo:
            score = fuzz.ratio(classe_antiga, classe_nova) / 100.0
            if score > melhor_score:
                melhor_score = score
    return melhor_score

def validar_xpath(xpath, html_dom):
    try:
        elementos = html_dom.xpath(xpath)
        return len(elementos) > 0
    except:
        return False

def heal_xpath(selector_antigo, dom_novo_html):
    if not dom_novo_html or dom_novo_html.strip() == '':
        raise ValueError("HTML passado para heal_xpath está vazio!")
    if selector_antigo.strip().startswith('//'):
        LIMIAR_XPATH = 0.6
    else:
        LIMIAR_XPATH = 0.8

    pattern = r"(contains\(@(class|id|name),\s*'([^']+)'\))"
    matches = re.findall(pattern, selector_antigo)
    if not matches:
        print(f"[DEBUG] XPath '{selector_antigo}' não tem pattern 'contains(@class|id|name, ...)'. Não será curado.")
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
                    print(f"[DEBUG] Classe antiga: '{valor_antigo}' | Classe nova: '{classe_indiv}' | Score fuzzy: {score:.2f}")
                    if score > melhor_score:
                        melhor_score = score
                        melhor_valor = classe_indiv
            else:
                score = score_fuzzy(valor_antigo, valor_novo)
                print(f"[DEBUG] Valor antigo: '{valor_antigo}' | Valor novo: '{valor_novo}' | Score fuzzy: {score:.2f}")
                if score > melhor_score:
                    melhor_score = score
                    melhor_valor = valor_novo

        print(f"[DEBUG] Melhor valor para '{valor_antigo}': '{melhor_valor}' com score: {melhor_score:.2f}")

        if melhor_score >= LIMIAR_XPATH:
            encontrou_alguma_substituicao = True
            xpath_sugerido = xpath_sugerido.replace(match_full, f"contains(@{atributo}, '{melhor_valor}')")
            scores.append(melhor_score)
            print(f"[DEBUG] Substituindo '{valor_antigo}' por '{melhor_valor}' no XPath. Sugerido: {xpath_sugerido}")
        else:
            print(f"[DEBUG] '{valor_antigo}' não atingiu limiar ({LIMIAR_XPATH}). Score: {melhor_score:.2f}")

    # Validação final
    is_valid = False
    if encontrou_alguma_substituicao:
        is_valid = validar_xpath(xpath_sugerido, html_dom)
        print(f"[DEBUG] XPath sugerido '{xpath_sugerido}' é válido no DOM? {is_valid}")

    print(f"[DEBUG] Resultado final: {'Alterado' if encontrou_alguma_substituicao and is_valid else 'Nenhuma substituição feita.'}")
    if encontrou_alguma_substituicao and is_valid:
        return xpath_sugerido, sum(scores)/len(scores), None
    return None, None, None



def fuzzy_matching_selector(selector_antigo, dom_novo, nome_logico=None, elementos_ja_usados=None, html_puro=None):
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

def gerar_diferencas(antes: list, depois: list, html_puro: str = None, atributos: list = None) -> dict:
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
