"""
Testes unitários para o módulo healing.
Valida o comportamento da função atualizar_seletores no formato moderno:
- Atualiza valores por nome lógico
- Remove, adiciona e altera corretamente
"""

import pytest
import json
from pathlib import Path
from dom_heal.healing import atualizar_seletores

def criar_json(tmp_path, dados):
    arquivo = tmp_path / "seletores.json"
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return arquivo

def ler_json(arquivo):
    return json.loads(arquivo.read_text(encoding="utf-8"))

def test_altera_selector(tmp_path):
    arquivo = criar_json(tmp_path, {"btnEnviar": "#antigo"})
    diff = {"alterados": [{"nome": "btnEnviar", "selector_antigo": "#antigo", "novo_seletor": "#btnNovo"}]}
    atualizar_seletores(diff, arquivo)
    atualizado = ler_json(arquivo)
    assert atualizado["btnEnviar"] == "#btnNovo"

def test_remove_nome_logico(tmp_path):
    arquivo = criar_json(tmp_path, {"campo": "#abc", "remover": "#remover"})
    diff = {"removidos": [{"nome": "remover"}]}
    atualizar_seletores(diff, arquivo)
    atualizado = ler_json(arquivo)
    assert "remover" not in atualizado
    assert "campo" in atualizado

def test_adiciona_novo(tmp_path):
    arquivo = criar_json(tmp_path, {"a": "#x"})
    diff = {"adicionados": [{"nome": "b", "novo_seletor": "#y"}]}
    atualizar_seletores(diff, arquivo)
    atualizado = ler_json(arquivo)
    assert atualizado["b"] == "#y"
    assert atualizado["a"] == "#x"

def test_idempotente_ao_adicionar_existente(tmp_path):
    arquivo = criar_json(tmp_path, {"a": "#x"})
    diff = {"adicionados": [{"nome": "a", "novo_seletor": "#x"}]}
    atualizar_seletores(diff, arquivo)
    atualizado = ler_json(arquivo)
    assert atualizado["a"] == "#x"

def test_file_not_found(tmp_path):
    arquivo = tmp_path / "nao_existe.json"
    diff = {"alterados": [{"nome": "qualquer", "selector_antigo": "#a", "novo_seletor": "#b"}]}
    with pytest.raises(FileNotFoundError):
        atualizar_seletores(diff, arquivo)

def test_altera_e_remove_ao_mesmo_tempo(tmp_path):
    arquivo = criar_json(tmp_path, {"campo": "#antigo", "deletar": "#del"})
    diff = {
        "alterados": [{"nome": "campo", "selector_antigo": "#antigo", "novo_seletor": "#novo"}],
        "removidos": [{"nome": "deletar"}]
    }
    atualizar_seletores(diff, arquivo)
    atualizado = ler_json(arquivo)
    assert atualizado["campo"] == "#novo"
    assert "deletar" not in atualizado

def test_sem_nenhuma_alteracao(tmp_path):
    arquivo = criar_json(tmp_path, {"a": "#a"})
    diff = {}
    atualizar_seletores(diff, arquivo)
    atualizado = ler_json(arquivo)
    assert atualizado["a"] == "#a"
