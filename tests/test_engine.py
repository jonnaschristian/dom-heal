"""
Testes unitários para o módulo engine da biblioteca DOM-Heal.

Esses testes validam a correta gravação e manipulação de arquivos JSON, 
a filtragem de logs para alterações relevantes e o fluxo completo do processo 
de self-healing via mocks. Garantem que as funções essenciais de persistência, 
log e execução do motor funcionam como esperado, prevenindo regressões em operações 
críticas do ciclo de atualização automática dos seletores.
"""

import pytest
import json
from pathlib import Path
from dom_heal.engine import gravar_json, salvar_diff_alterados, self_heal

def test_gravar_json_cria_arquivo(tmp_path):
    """Testa se a função grava_json salva corretamente o dicionário como JSON."""
    dados = {"campo": 123}
    caminho = tmp_path / "arquivo.json"
    gravar_json(caminho, dados)
    assert caminho.exists(), "Arquivo JSON não foi criado"
    with caminho.open(encoding="utf-8") as arq:
        salvo = json.load(arq)
    assert salvo == dados, "Conteúdo salvo difere do esperado"

def test_salvar_diff_alterados(tmp_path):
    """Testa se só campos não vazios são salvos no log."""
    seletores_json = tmp_path / "seletores.json"
    seletores_json.write_text("{}", encoding="utf-8")
    diferencas = {
        "alterados": [{"nome": "btn", "selector_antigo": "#a", "novo_seletor": "#b"}],
        "removidos": [],
        "adicionados": []
    }
    salvar_diff_alterados(diferencas, seletores_json)
    caminho_log = seletores_json.parent / "ElementosAlterados.json"
    assert caminho_log.exists(), "Arquivo de log não foi criado"
    with caminho_log.open(encoding="utf-8") as arq:
        log = json.load(arq)
    assert "alterados" in log, "Campo 'alterados' não foi salvo"
    assert "removidos" not in log, "Campo 'removidos' deveria ter sido omitido"
    assert "adicionados" not in log, "Campo 'adicionados' deveria ter sido omitido"

def test_self_heal_fluxo(monkeypatch, tmp_path):
    """Testa se o self_heal executa todo o fluxo e retorna os caminhos dos arquivos."""
    caminho_json = tmp_path / "seletores.json"
    caminho_json.write_text(json.dumps([
        {"nome": "btnEnviar", "selector": "#antigo"}
    ]), encoding="utf-8")

    # Mocks
    monkeypatch.setattr("dom_heal.engine.extrair_dom", lambda url: [
        {"tag": "button", "id": "btnEnviar", "class": "btn", "xpath": "/html/body/button[1]"}
    ])
    monkeypatch.setattr("dom_heal.engine.gerar_diferencas", lambda antes, depois: {
        "alterados": [
            {"nome": "btnEnviar", "selector_antigo": "#antigo", "novo_seletor": "#btnEnviar"}
        ]
    })
    monkeypatch.setattr("dom_heal.engine.atualizar_seletores", lambda diff, caminho: None)

    resultado = self_heal(str(caminho_json), "http://teste")
    assert "msg" in resultado, "Resultado deve conter 'msg'"
    assert "log_detalhado" in resultado, "Resultado deve conter 'log_detalhado'"
    assert "json_atualizado" in resultado, "Resultado deve conter 'json_atualizado'"
