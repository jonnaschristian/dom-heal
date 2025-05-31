"""
Comparator
==========

Módulo responsável por comparar seletores antigos do teste automatizado com o novo DOM,
sugerindo seletores alternativos de forma inteligente e robusta via heurística fuzzy.

Independente de framework ou convenção, aplicável em qualquer sistema web.

Principais funcionalidades:
- Matching por id, name, class ou xpath.
- Heurística ajustada para empates, priorização de id, boosts de tradução e semântica.
- Matching robusto de nomes com palavras fora de ordem (ex: mensagemSucesso <-> sucessoMensagem).
- Totalmente orientado para auto-recuperação de seletores em testes automatizados (self-healing).
"""

from rapidfuzz import fuzz

ATRIBUTOS = ['id', 'name', 'class', 'xpath']
LIMIARES_POR_CAMPO = {
    'id': 0.60,
    'name': 0.60,
    'class': 0.70,
    'xpath': 0.80
}

TRADUCOES_EN_PT = {
    # ... [igual ao seu dicionário, mantido completo no seu projeto] ...
    'name': 'nome', 'email': 'email', 'phone': 'telefone', 'msg': 'mensagem', 'message': 'mensagem',
    'address': 'endereco', 'user': 'usuario', 'username': 'usuario', 'password': 'senha',
    'login': 'entrar', 'logout': 'sair', 'register': 'registrar', 'signup': 'cadastrar',
    'signin': 'entrar', 'search': 'buscar', 'find': 'buscar', 'save': 'salvar', 'submit': 'enviar',
    'send': 'enviar', 'edit': 'editar', 'update': 'atualizar', 'delete': 'deletar', 'remove': 'remover',
    'cancel': 'cancelar', 'confirm': 'confirmar', 'yes': 'sim', 'no': 'nao', 'ok': 'ok',
    'next': 'proximo', 'previous': 'anterior', 'back': 'voltar', 'continue': 'continuar',
    'finish': 'finalizar', 'success': 'sucesso', 'error': 'erro', 'fail': 'falha', 'warning': 'aviso',
    'info': 'informacao', 'description': 'descricao', 'title': 'titulo', 'header': 'cabecalho',
    'footer': 'rodape', 'content': 'conteudo', 'menu': 'menu', 'item': 'item', 'table': 'tabela',
    'row': 'linha', 'column': 'coluna', 'cell': 'celula', 'list': 'lista', 'details': 'detalhes',
    'home': 'inicio', 'homepage': 'tela inicial', 'main': 'principal', 'dashboard': 'painel',
    'profile': 'perfil', 'settings': 'configuracoes', 'preferences': 'preferencias', 'options': 'opcoes',
    'help': 'ajuda', 'support': 'suporte', 'contact': 'contato', 'about': 'sobre', 'form': 'formulario',
    'field': 'campo', 'value': 'valor', 'amount': 'quantidade', 'price': 'preco', 'total': 'total',
    'status': 'status', 'active': 'ativo', 'inactive': 'inativo', 'blocked': 'bloqueado',
    'pending': 'pendente', 'completed': 'completo', 'date': 'data', 'time': 'hora', 'day': 'dia',
    'month': 'mes', 'year': 'ano', 'upload': 'enviar arquivo', 'download': 'baixar', 'file': 'arquivo',
    'image': 'imagem', 'photo': 'foto', 'picture': 'imagem', 'avatar': 'avatar', 'link': 'link',
    'url': 'url', 'page': 'pagina', 'view': 'visualizar', 'print': 'imprimir', 'map': 'mapa',
    'city': 'cidade', 'state': 'estado', 'country': 'pais', 'zip': 'cep', 'code': 'codigo',
    'number': 'numero', 'id': 'id'
}

def traduzir_selector(selector: str) -> str:
    """
    Traduz uma palavra-chave do seletor para PT-BR se houver mapeamento.
    Usado para aumentar similaridade semântica.
    """
    return TRADUCOES_EN_PT.get(selector.lower(), selector)

def palavras_iguais_qualquer_ordem(a: str, b: str) -> bool:
    """
    Checa se as palavras (substrings) em duas strings são as mesmas, independente da ordem.
    Ex: mensagemSucesso vs sucessoMensagem => True
    """
    import re
    def palavras(s):
        return set(re.findall(r'[a-zA-Z]+', s.lower()))
    return palavras(a) == palavras(b) and len(palavras(a)) > 0

def formatar_selector(campo, valor):
    """
    Retorna o seletor CSS/XPath no formato correto para cada atributo.
    """
    if campo == 'id':
        return f'#{valor}'
    elif campo == 'name':
        return f'[name="{valor}"]'
    elif campo == 'class':
        return f'.{valor.split()[0]}'
    elif campo == 'xpath':
        return valor
    return valor

def score_hibrido_robusto(selector_antigo, candidato, nome_logico=None, elem=None):
    """
    Calcula um score heurístico fuzzy robusto entre o seletor antigo e o possível novo valor de id/name/class/xpath.
    Usa múltiplos boosts, penalidades e aproximações para simular a "intuição" de um QA ao atualizar o seletor.
    Inclui boost especial se a diferença for de apenas 1 letra ou underline vs hífen.
    """
    sel_a = selector_antigo.lower()
    cand = candidato.lower()

    score_ratio = fuzz.ratio(sel_a, cand) / 100.0
    score_token = fuzz.token_sort_ratio(sel_a, cand) / 100.0
    score_partial = fuzz.partial_ratio(sel_a, cand) / 100.0

    boost_prefixo = 0.18 if cand.startswith(sel_a) else 0
    boost_exato = 0.22 if sel_a == cand else 0
    boost_substring = 0.12 if sel_a in cand or cand in sel_a else 0

    selector_traduzido = traduzir_selector(sel_a)
    boost_traducao = 0.22 if cand.startswith(selector_traduzido) else 0
    boost_traducao_token = 0.12 if selector_traduzido in cand else 0

    boost_semantico = 0
    if nome_logico:
        for palavra in [
            "nome", "email", "telefone", "msg", "mensagem", "erro", "sucesso", "contato", "senha",
            "login", "user", "submit", "send", "search", "tabela", "table", "pagina", "home",
            "form", "campo", "data", "hora", "preco", "status", "usuario"
        ]:
            if palavra in nome_logico.lower() and palavra in cand:
                boost_semantico += 0.18

    # Boost para nomes iguais com palavras fora de ordem
    boost_palavras_iguais = 0
    if palavras_iguais_qualquer_ordem(sel_a, cand):
        boost_palavras_iguais += 0.24

    # Boost especial para diferença de só uma letra (inclusão, remoção ou substituição)
    def diff_de_uma_letra(a, b):
        if a == b:
            return False
        if len(a) == len(b) + 1:
            for i in range(len(a)):
                if a[:i] + a[i+1:] == b:
                    return True
        if len(a) + 1 == len(b):
            for i in range(len(b)):
                if b[:i] + b[i+1:] == a:
                    return True
        if len(a) == len(b):
            dif = sum(1 for x, y in zip(a, b) if x != y)
            if dif == 1:
                return True
        return False

    boost_um_char = 0
    if diff_de_uma_letra(sel_a, cand):
        boost_um_char = 0.20  # Agora garantidamente suficiente para passar limiar!

    # Boost extra para hífen vs underline
    boost_hifen_underline = 0
    if sel_a.replace('_', '-') == cand.replace('_', '-'):
        boost_hifen_underline = 0.18

    penalidade_generico = 0
    if any(x in cand for x in ["container", "row", "col", "main", "section"]):
        penalidade_generico -= 0.20

    boost_tag = 0
    if elem and nome_logico:
        tag_elem = elem.get("tag", "").lower()
        if any(t in nome_logico.lower() for t in ["btn", "button", "submit", "enviar"]) and tag_elem in ["button", "input"]:
            boost_tag += 0.14
        elif any(t in nome_logico.lower() for t in ["input", "campo", "field", "form"]) and tag_elem in ["input", "textarea", "select"]:
            boost_tag += 0.12

    boost_class_parcial = 0
    if elem and elem.get("class"):
        if sel_a in elem.get("class", "").lower():
            boost_class_parcial += 0.13
        elif nome_logico and nome_logico.lower() in elem.get("class", "").lower():
            boost_class_parcial += 0.11

    score = (
        0.22 * score_ratio +
        0.19 * score_token +
        0.16 * score_partial +
        boost_prefixo +
        boost_exato +
        boost_substring +
        boost_traducao +
        boost_traducao_token +
        boost_semantico +
        boost_tag +
        boost_class_parcial +
        boost_palavras_iguais +
        boost_um_char +
        boost_hifen_underline +
        penalidade_generico
    )

    return max(0.0, min(score, 1.0))


def fuzzy_matching_selector(selector_antigo, dom_novo, nome_logico=None, elementos_ja_usados=None):
    """
    Faz o matching fuzzy entre um seletor antigo e o novo DOM,
    priorizando: id > name > class > xpath,
    e garantindo que nenhum elemento seja mapeado mais de uma vez.
    """
    seletor_val = selector_antigo.lstrip('#.')

    CLASSES_IGNORADAS = {'d-none', 'hidden', 'container', 'row', 'col', 'col-md-12', 'main', 'section'}

    # 1. Matching por ID exato e disponível
    for idx, elem in enumerate(dom_novo):
        if elementos_ja_usados and idx in elementos_ja_usados:
            continue
        id_novo = elem.get('id', '')
        if id_novo and (id_novo == seletor_val or id_novo == nome_logico):
            return (formatar_selector('id', id_novo), elem, 1.0, 'id', idx)

    # 2. Matching por NAME exato e disponível
    for idx, elem in enumerate(dom_novo):
        if elementos_ja_usados and idx in elementos_ja_usados:
            continue
        name_novo = elem.get('name', '')
        if name_novo and (name_novo == seletor_val or name_novo == nome_logico):
            return (formatar_selector('name', name_novo), elem, 1.0, 'name', idx)

    # 3. Matching fuzzy e semântico
    candidatos_validos = []
    for idx, elem in enumerate(dom_novo):
        if elementos_ja_usados and idx in elementos_ja_usados:
            continue
        for campo in ATRIBUTOS:
            valor = elem.get(campo, '')
            if not valor:
                continue
            if campo == 'class' and any(cls in valor.split() for cls in CLASSES_IGNORADAS):
                continue

            score = score_hibrido_robusto(seletor_val, valor, nome_logico=nome_logico, elem=elem)
            limiar_campo = LIMIARES_POR_CAMPO.get(campo, 0.6)
            if score >= limiar_campo:
                candidatos_validos.append({
                    'score': score,
                    'selector': formatar_selector(campo, valor),
                    'elemento': elem,
                    'campo': campo,
                    'idx': idx
                })

    # 4. Matching com prioridade id > name > class > xpath
    if candidatos_validos:
        ordem_prioridade = {'id': 3, 'name': 2, 'class': 1, 'xpath': 0}
        candidatos_validos.sort(key=lambda x: (ordem_prioridade.get(x['campo'], 0), x['score']), reverse=True)
        melhor = candidatos_validos[0]
        return (melhor['selector'], melhor['elemento'], melhor['score'], melhor['campo'], melhor['idx'])

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
