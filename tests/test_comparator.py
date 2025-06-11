"""
Testes unitários para o módulo comparator da biblioteca DOM-Heal.

Cobrem diversos aspectos e funções do mecanismo de comparação de seletores, incluindo:
- Formatação e detecção de tipos de seletores
- Algoritmos de similaridade fuzzy e boosts aplicados
- Cálculo de score entre classes e validação de XPath
- Lógica de self-healing para sugestão automática de novos seletores
- Matching de seletores antigos vs DOM novo, com cenários de empate e aplicação de boost
- Cobertura da função gerar_diferencas para múltiplos casos, incluindo vazios e limiares

Esses testes garantem a robustez das heurísticas e dos fluxos internos do comparator, servindo de base para validação do comportamento do self-healing.
"""

import pytest
from rapidfuzz import fuzz
from dom_heal.comparator import (
    formatar_selector,
    detectar_tipo_selector,
    score_fuzzy,
    boost_prefixo, boost_sufixo, boost_um_char, boost_palavras_iguais,
    aplicar_boost,
    score_class,
    validar_xpath,
    heal_xpath,
    fuzzy_matching_selector,
    gerar_diferencas,
)

def test_formatar_selector_various():
    assert formatar_selector('id', 'a') == '#a'
    assert formatar_selector('name', 'b') == '[name="b"]'
    assert formatar_selector('class', 'x y', 'div') == 'div.x.y'
    assert formatar_selector('xpath', '//p') == '//p'
    assert formatar_selector('outro', 'z') == 'z'

def test_detectar_tipo_selector():
    assert detectar_tipo_selector('#a') == 'id'
    assert detectar_tipo_selector('[name="a"]') == 'name'
    assert detectar_tipo_selector('.c') == 'class'
    assert detectar_tipo_selector('//x') == 'xpath'

def test_score_fuzzy_and_boosts():
    assert pytest.approx(score_fuzzy('abc', 'abc'), 0.0001) == 1.0
    assert boost_prefixo('abcd', 'abzz') == 0.1
    assert boost_sufixo('abcd', 'zzcd') == 0.1
    assert boost_um_char('abcd', 'abce') == 0.1
    assert boost_palavras_iguais('a b', 'b a') == 0.1
    assert boost_palavras_iguais('', '') == 0

def test_aplicar_boost_limits():
    btotal, details = aplicar_boost('id', 'abc', 'abc', '')
    assert 0 <= btotal <= 0.2
    assert 'boost_total' in details

def test_score_class():
    conj1 = {'a', 'b'}
    conj2 = {'b', 'c', 'a'}
    assert score_class(conj1, conj2) > 0

def test_validar_xpath_success_and_fail():
    from lxml import html as lh
    dom = lh.fromstring("<html><body><p>hi</p></body></html>")
    assert validar_xpath('//p', dom)
    assert not validar_xpath('//nosuch', dom)

def test_heal_xpath_error_empty():
    with pytest.raises(ValueError):
        heal_xpath('//x', '')

HTML = "<body><div id='foo' class='bar baz'></div></body>"
def test_heal_xpath_success_replace():
    xpath_old = "//div[contains(@id,'foo')]"
    new, score, _ = heal_xpath(xpath_old, HTML)
    assert new != xpath_old and 'foo' in new

def test_heal_xpath_no_matches():
    new, score, _ = heal_xpath("//div[contains(@class,'zzz')]", HTML)
    assert new is None and score is None

DOM = [
    {'tag': 'input', 'id': 'campoX', 'class': None, 'xpath': '/a'},
    {'tag': 'div', 'id': None, 'class': 'meu-classe', 'xpath': '/b'}
]

def test_fuzzy_selector_xpath_branch():
    sel, elem, score, tipo, idx, boosts = fuzzy_matching_selector("//a", DOM, html_puro="<html></html>")
    assert tipo == 'xpath'
    assert sel is None or sel.startswith('/')

def test_fuzzy_selector_id_branch():
    sel, elem, score, tipo, idx, boosts = fuzzy_matching_selector("#campoX", DOM)
    assert tipo == 'id' and sel == '#campoX'

def test_fuzzy_selector_class_branch_and_used():
    sel, *rest = fuzzy_matching_selector(".meu-classe", DOM, elementos_ja_usados={1})
    assert sel is None

def test_fuzzy_selector_noboost_no_match():
    sel, *rest = fuzzy_matching_selector("#zzz", DOM)
    assert sel is None

def test_gerar_diferencas_empty_and_invalid():
    assert gerar_diferencas([], []) == {}
    assert gerar_diferencas([{'nome': None, 'selector': None}], DOM) == {}

def test_gerar_diferencas_tie(monkeypatch):
    """
    Quando o score fica exatamente no limiar (ex: 0.70 para 'id'), sem boost,
    deve retornar dict vazio (nenhuma alteração).
    """
    antes = [{'nome': 'n', 'selector': '#n'}]
    depois = [{'tag': 'div', 'id': 'n', 'class': 'n', 'xpath': '/n'}]

    import dom_heal.comparator as cmp
    monkeypatch.setattr(cmp, 'fuzzy_matching_selector',
        lambda *args, **kwargs: ("#n", {}, cmp.LIMIARES_POR_CAMPO['id'], 'id', 0, {}))

    diff = cmp.gerar_diferencas(antes, depois)
    assert diff == {}, "Empate exato sem boost deve resultar em diff vazio"

def test_aplicar_boost_each_case():

    boost, det = aplicar_boost('name', 'abcde', 'abzzz', 0.5)
    assert det.get('prefixo') == 0.1

    boost, det = aplicar_boost('name', 'abcde', 'zzzde', 0.5)
    assert det.get('sufixo') == 0.1

    boost, det = aplicar_boost('name', 'abcde', 'abxde', 0.5)
    assert det.get('um_char') == 0.1

    boost, det = aplicar_boost('name', 'foo bar', 'bar foo', 0.5)
    assert det.get('palavras_iguais') == 0.1
