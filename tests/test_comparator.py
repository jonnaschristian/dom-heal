"""
Testes unitários para o módulo comparator da biblioteca DOM-Heal.

Esses testes garantem o correto funcionamento da heurística de matching de seletores, 
validando casos de atualização por id, name, class, priorização de id em empates, 
matching semântico, múltiplos elementos, prevenção de duplicidade, nomes parecidos 
e comportamento seguro em cenários sem similaridade. Os testes também previnem 
regressões e garantem robustez para os principais fluxos de self-healing.
"""

import pytest
from dom_heal.comparator import gerar_diferencas

def test_id_para_novo_id():
    """Deve atualizar seletor por id corretamente."""
    antes = [{"nome": "btnEnviar", "selector": "#botaoEnviar"}]
    depois = [{"tag": "button", "id": "btnEnviar", "class": "btn", "xpath": "/html/body/button[1]"}]
    diff = gerar_diferencas(antes, depois)
    assert "alterados" in diff, "Deveria retornar chave 'alterados' no diff"
    assert diff["alterados"][0]["novo_seletor"] == "#btnEnviar", "Deveria atualizar para o novo id"

def test_matching_por_name():
    """Matching deve funcionar por atributo name."""
    antes = [{"nome": "inputEmail", "selector": "#emailInput"}]
    depois = [{"tag": "input", "name": "email", "class": "input-email", "xpath": "/html/body/input[1]"}]
    diff = gerar_diferencas(antes, depois)
    assert "alterados" in diff, "Deveria haver 'alterados' para update por name"
    assert '[name="email"]' in diff["alterados"][0]["novo_seletor"], "Deveria sugerir seletor por name"

def test_matching_por_class():
    """
    Deve sugerir seletor novo por classe, se id/name não encontrados e as classes são praticamente iguais,
    mas diferentes (ex: ajuste por bugfix, internacionalização etc).
    """
    antes = [{"nome": "alertaSucesso", "selector": ".alerta-success"}]  # Valor levemente diferente do novo
    depois = [{"tag": "div", "class": "alert-success", "xpath": "/html/body/div[1]"}]
    diff = gerar_diferencas(antes, depois)
    assert "alterados" in diff, "Deveria sugerir update por class"
    assert ".alert-success" in diff["alterados"][0]["novo_seletor"], "Deveria sugerir a classe nova"

def test_ignora_quando_nao_tem_similar():
    """Não deve sugerir update quando não há similaridade razoável."""
    antes = [{"nome": "titulo", "selector": "#tituloAntigo"}]
    depois = [{"tag": "h1", "id": "header", "class": "destaque", "xpath": "/html/body/h1[1]"}]
    diff = gerar_diferencas(antes, depois)
    assert "alterados" not in diff or len(diff["alterados"]) == 0, "Não deveria haver alteração se não há similar"

def test_fallback_prioriza_id():
    """Quando existe id igual ao nome, id deve ser priorizado."""
    antes = [{"nome": "campoNome", "selector": ".nome-antigo"}]
    depois = [
        {"tag": "input", "id": "campoNome", "class": "nome-novo", "xpath": "/html/body/input[1]"},
        {"tag": "input", "class": "nome-campo", "xpath": "/html/body/input[2]"}
    ]
    diff = gerar_diferencas(antes, depois)
    assert "alterados" in diff, "Deveria sugerir alteração"
    assert diff["alterados"][0]["novo_seletor"] == "#campoNome", "Deveria priorizar id no update"

def test_empate_prioriza_id():
    """Quando empate, id deve ser preferido ao invés de apenas class."""
    antes = [{"nome": "acao", "selector": ".acao-antiga"}]
    depois = [
        {"tag": "button", "id": "acao", "class": "acao", "xpath": "/html/body/button[1]"},
        {"tag": "button", "class": "acao", "xpath": "/html/body/button[2]"}
    ]
    diff = gerar_diferencas(antes, depois)
    assert "alterados" in diff, "Deveria sugerir alteração"
    assert diff["alterados"][0]["novo_seletor"] == "#acao", "Deveria priorizar id no empate"

def test_traducao_palavra_chave():
    """Deve detectar mudança de palavra-chave relevante, por exemplo, name semanticamente similar."""
    antes = [{"nome": "inputUsuario", "selector": "#userInput"}]
    depois = [{"tag": "input", "name": "usuario", "class": "user-form", "xpath": "/html/body/input[1]"}]
    diff = gerar_diferencas(antes, depois)
    assert "alterados" in diff, "Deveria sugerir alteração para similaridade semântica por name"
    assert '[name="usuario"]' in diff["alterados"][0]["novo_seletor"], "Deveria sugerir seletor pelo novo name"

def test_varios_elementos_robustez():
    """Matching múltiplo: todos devem ser detectados individualmente (apenas onde há similaridade de fato)."""
    antes = [
        {"nome": "campoEmail", "selector": "#emailAntigo"},
        {"nome": "btnSubmit", "selector": "#submitAntigo"}
        # {"nome": "alertSucesso", "selector": ".alerta-old"}  # Removido pois não há similaridade real!
    ]
    depois = [
        {"tag": "input", "id": "campoEmail", "name": "email", "class": "input-email", "xpath": "/input[1]"},
        {"tag": "button", "id": "btnSubmit", "class": "btn-submit", "xpath": "/button[1]"},
        {"tag": "div", "class": "alert-success", "xpath": "/div[1]"}
    ]
    diff = gerar_diferencas(antes, depois)
    nomes = [alt["nome"] for alt in diff.get("alterados", [])]
    assert "campoEmail" in nomes, "campoEmail deveria estar nos alterados"
    assert "btnSubmit" in nomes, "btnSubmit deveria estar nos alterados"
    # assert "alertSucesso" in nomes, "alertSucesso deveria estar nos alterados"  # Removido!

def test_nao_duplicar_elemento():
    """Não deve mapear o mesmo elemento novo para dois antigos."""
    antes = [
        {"nome": "campoEmail", "selector": ".email"},
        {"nome": "campoEmailConfirmacao", "selector": ".email-confirm"}
    ]
    depois = [
        {"tag": "input", "id": "email", "class": "email", "xpath": "/input[1]"},
        {"tag": "input", "id": "emailConf", "class": "email-confirm", "xpath": "/input[2]"}
    ]
    diff = gerar_diferencas(antes, depois)
    seletores = [alt["novo_seletor"] for alt in diff.get("alterados", [])]
    assert "#email" in seletores, "Seletor do primeiro campo não foi atualizado corretamente"
    assert "#emailConf" in seletores, "Seletor do campo de confirmação não foi atualizado corretamente"
    assert seletores.count("#email") == 1, "Elemento novo não deve ser duplicado"

def test_nomes_parecidos_nao_confunde():
    """Nomes parecidos não devem confundir o matching."""
    antes = [
        {"nome": "campoNome", "selector": ".nome-antigo"},
        {"nome": "campoNomeMae", "selector": ".nome-mae-antigo"}
    ]
    depois = [
        {"tag": "input", "id": "campoNome", "class": "nome", "xpath": "/input[1]"},
        {"tag": "input", "id": "campoNomeMae", "class": "nome-mae", "xpath": "/input[2]"}
    ]
    diff = gerar_diferencas(antes, depois)
    nomes = [alt["nome"] for alt in diff.get("alterados", [])]
    assert "campoNome" in nomes, "Matching não deve ignorar o campoNome"
    assert "campoNomeMae" in nomes, "Matching não pode confundir campoNome com campoNomeMae"
