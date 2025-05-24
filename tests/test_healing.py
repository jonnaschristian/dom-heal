"""
Testes unitários para o módulo healing.
Valida o comportamento da função atualizar_seletores para todos os tipos de diffs:
adicionados, removidos, alterados e movidos.
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

def test_adiciona_xpath(tmp_path):
    arquivo = criar_json(tmp_path, {"a": {"id": "x"}})
    diff = {"adicionados": ["b"]}
    atualizar_seletores(diff, arquivo)
    atualizado = ler_json(arquivo)
    assert "b" in atualizado
    assert atualizado["b"] == {}

def test_remove_xpath(tmp_path):
    arquivo = criar_json(tmp_path, {"a": {"id": "x"}, "b": {"id": "y"}})
    diff = {"removidos": ["b"]}
    atualizar_seletores(diff, arquivo)
    atualizado = ler_json(arquivo)
    assert "b" not in atualizado
    assert "a" in atualizado

def test_altera_atributos(tmp_path):
    arquivo = criar_json(tmp_path, {"a": {"id": "x", "class": "foo"}})
    diff = {"alterados": [
        {"xpath": "a", "diferencas": {"id": {"antes": "x", "depois": "y"}, "class": {"antes": "foo", "depois": "bar"}}}
    ]}
    atualizar_seletores(diff, arquivo)
    atualizado = ler_json(arquivo)
    assert atualizado["a"]["id"] == "y"
    assert atualizado["a"]["class"] == "bar"

def test_move_xpath(tmp_path):
    arquivo = criar_json(tmp_path, {"a": {"id": "x"}, "c": {"id": "z"}})
    diff = {"movidos": [{"de": "a", "para": "b"}]}
    atualizar_seletores(diff, arquivo)
    atualizado = ler_json(arquivo)
    assert "a" not in atualizado
    assert "b" in atualizado
    assert atualizado["b"]["id"] == "x"
    assert "c" in atualizado  # nada mexeu nela

def test_arquivo_nao_existe(tmp_path):
    arquivo = tmp_path / "inexistente.json"
    diff = {"adicionados": ["x"]}
    with pytest.raises(FileNotFoundError):
        atualizar_seletores(diff, arquivo)

def test_adiciona_existente_remove_inexistente(tmp_path):
    arquivo = criar_json(tmp_path, {"a": {}})
    diff = {"adicionados": ["a"], "removidos": ["b"]}
    # Não deve quebrar nem alterar o existente
    atualizar_seletores(diff, arquivo)
    atualizado = ler_json(arquivo)
    assert "a" in atualizado and isinstance(atualizado["a"], dict)
    # Não adicionou "b" e nem removeu "a" por engano
    assert "b" not in atualizado

