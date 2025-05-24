"""
Testes unitários para o módulo comparator.
Cobrem todos os tipos de diferenças entre snapshots: adicionados, removidos, alterados, movidos,
incluindo atributos padrão, atributos data-* e edge cases.
"""

import pytest
from dom_heal.comparator import ler_snapshot, gerar_diferencas
from pathlib import Path
import json

def criar_arquivo_json(tmp_path, nome, dados):
    caminho = tmp_path / nome
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho

def test_ler_snapshot_valido(tmp_path):
    dados = [{"xpath": "/html[1]/body[1]/div[1]", "id": "a"}]
    arquivo = criar_arquivo_json(tmp_path, "t0.json", dados)
    resultado = ler_snapshot(arquivo)
    assert resultado == dados

def test_ler_snapshot_invalido(tmp_path):
    arquivo = tmp_path / "invalido.json"
    arquivo.write_text("{nao_eh_json}", encoding="utf-8")
    resultado = ler_snapshot(arquivo)
    assert resultado == []

def test_adicionado_removido(tmp_path):
    antes = [{"xpath": "/a[1]", "id": "um"}]
    depois = [{"xpath": "/b[1]", "id": "dois"}]
    diff = gerar_diferencas(antes, depois)
    assert diff["adicionados"] == ["/b[1]"]
    assert diff["removidos"] == ["/a[1]"]

def test_alterado_simples():
    antes = [{"xpath": "/a[1]", "id": "um", "class": "foo"}]
    depois = [{"xpath": "/a[1]", "id": "um", "class": "bar"}]
    diff = gerar_diferencas(antes, depois)
    assert len(diff["alterados"]) == 1
    alterado = diff["alterados"][0]
    assert alterado["xpath"] == "/a[1]"
    assert alterado["diferencas"]["class"] == {"antes": "foo", "depois": "bar"}

def test_movido_por_id():
    antes = [
        {"xpath": "/a[1]", "id": "um"},
        {"xpath": "/b[1]", "id": "dois"},
    ]
    depois = [
        {"xpath": "/b[1]", "id": "um"},
        {"xpath": "/a[1]", "id": "dois"},
    ]
    diff = gerar_diferencas(antes, depois)
    assert any(m["id"] == "um" and m["de"] == "/a[1]" and m["para"] == "/b[1]" for m in diff["movidos"])
    assert any(m["id"] == "dois" and m["de"] == "/b[1]" and m["para"] == "/a[1]" for m in diff["movidos"])

def test_movido_por_fuzzy():
    antes = [{"xpath": "/a[1]", "id": "", "class": "foo"}]
    depois = [{"xpath": "/b[1]", "id": "", "class": "foo"}]
    diff = gerar_diferencas(antes, depois)
    assert any(m["de"] == "/a[1]" and m["para"] == "/b[1]" for m in diff["movidos"])

def test_atributos_data(tmp_path):
    antes = [{"xpath": "/a[1]", "id": "um", "data_teste": "X"}]
    depois = [{"xpath": "/a[1]", "id": "um", "data_teste": "Y"}]
    diff = gerar_diferencas(antes, depois)
    assert diff["alterados"][0]["diferencas"]["data_teste"] == {"antes": "X", "depois": "Y"}

def test_varios_tipos_ao_mesmo_tempo():
    antes = [
        {"xpath": "/a[1]", "id": "um", "class": "foo", "text": "A"},
        {"xpath": "/b[1]", "id": "dois", "class": "bar", "text": "B"},
        {"xpath": "/c[1]", "id": "tres", "class": "baz", "text": "C"},
    ]
    depois = [
        {"xpath": "/b[1]", "id": "um", "class": "foo", "text": "A"},  # movido id=um
        {"xpath": "/a[1]", "id": "dois", "class": "bar", "text": "B"}, # movido id=dois
        {"xpath": "/d[1]", "id": "quatro", "class": "qux", "text": "D"}, # adicionado
    ]
    diff = gerar_diferencas(antes, depois)
    assert len(diff["movidos"]) == 2
    assert diff["adicionados"] == ["/d[1]"]
    assert diff["removidos"] == ["/c[1]"]

def test_ordem_e_hierarquia():
    antes = [
        {"xpath": "/div[1]/span[1]", "id": "s1"},
        {"xpath": "/div[2]/span[1]", "id": "s2"},
    ]
    depois = [
        {"xpath": "/div[2]/span[1]", "id": "s2"},
        {"xpath": "/div[1]/span[1]", "id": "s1"},
    ]
    diff = gerar_diferencas(antes, depois)
    assert not diff.get("movidos", []) or all("id" in m for m in diff["movidos"])

def test_alterado_multiplos_atributos():
    antes = [{"xpath": "/x[1]", "id": "i1", "class": "foo", "type": "text"}]
    depois = [{"xpath": "/x[1]", "id": "i1", "class": "bar", "type": "password"}]
    diff = gerar_diferencas(antes, depois)
    diferencas = diff["alterados"][0]["diferencas"]
    assert diferencas["class"] == {"antes": "foo", "depois": "bar"}
    assert diferencas["type"] == {"antes": "text", "depois": "password"}

def test_alterado_aria_label():
    antes = [{"xpath": "/a[1]", "aria_label": "Foo"}]
    depois = [{"xpath": "/a[1]", "aria_label": "Bar"}]
    diff = gerar_diferencas(antes, depois)
    assert diff["alterados"][0]["diferencas"]["aria_label"] == {"antes": "Foo", "depois": "Bar"}
