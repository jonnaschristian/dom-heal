"""
Testes unitários para o módulo healing.
Valida o comportamento da função atualizar_seletores no formato moderno:
- Atualiza valores por nome lógico
- Remove, adiciona e altera corretamente
"""

import json
import pytest
from pathlib import Path
from dom_heal.healing import atualizar_seletores

# ——— Testes antigos (mantidos para regressão) ———

def test_atualiza_apenas_alterados(tmp_path):
    seletores = {"x": "#oldx", "y": "#oldy"}
    arquivo = tmp_path / "base.json"
    arquivo.write_text(json.dumps(seletores), encoding="utf-8")

    diff = {"alterados": [{"nome_logico": "x", "novo_seletor": "#newx"}]}

    atualizar_seletores(diff, arquivo)
    resultado = json.loads(arquivo.read_text(encoding="utf-8"))
    assert resultado["x"] == "#newx"
    assert resultado["y"] == "#oldy"

# ——— Novos testes para 100% de cobertura ———

def test_file_not_found(tmp_path):
    arquivo = tmp_path / "arquivo_inexistente.json"
    with pytest.raises(FileNotFoundError) as exc:
        atualizar_seletores({}, arquivo)
    assert "Arquivo de seletores não encontrado" in str(exc.value)

def test_invalid_json(tmp_path):
    arquivo = tmp_path / "seletores_inv.json"
    arquivo.write_text("conteudo inválido", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        atualizar_seletores({}, arquivo)

def test_aplica_alterados_movidos(tmp_path):
    seletores = {"a": "#old_a", "b": "#old_b"}
    arquivo = tmp_path / "sel.json"
    arquivo.write_text(json.dumps(seletores), encoding="utf-8")

    diff = {
        "alterados": [{"nome": "a", "novo_seletor": "#new_a"}],
        "movidos": [{"nome": "b", "novo_seletor": "#new_b"}]
    }

    atualizar_seletores(diff, arquivo)
    result = json.loads(arquivo.read_text(encoding="utf-8"))
    assert result["a"] == "#new_a"
    assert result["b"] == "#new_b"

def test_remove_seletores(tmp_path):
    seletores = {"c": "#c", "d": "#d"}
    arquivo = tmp_path / "sel2.json"
    arquivo.write_text(json.dumps(seletores), encoding="utf-8")

    diff = {"removidos": [{"nome": "c"}, "d"]}

    atualizar_seletores(diff, arquivo)
    result = json.loads(arquivo.read_text(encoding="utf-8"))
    assert "c" not in result
    assert "d" not in result

def test_adiciona_novos(tmp_path):
    seletores = {"e": "#e"}
    arquivo = tmp_path / "sel3.json"
    arquivo.write_text(json.dumps(seletores), encoding="utf-8")

    diff = {"adicionados": [{"nome": "f", "novo_seletor": "#f"}, {"xpath": "/g", "selector": "#g"}]}

    atualizar_seletores(diff, arquivo)
    result = json.loads(arquivo.read_text(encoding="utf-8"))
    assert result["f"] == "#f"
    assert result["/g"] == "#g"

def test_nao_sobrescreve_existente(tmp_path):
    seletores = {"h": "#existent"}
    arquivo = tmp_path / "sel4.json"
    arquivo.write_text(json.dumps(seletores), encoding="utf-8")

    diff = {"adicionados": [{"nome": "h", "novo_seletor": "#new_h"}]}
    atualizar_seletores(diff, arquivo)
    result = json.loads(arquivo.read_text(encoding="utf-8"))
    assert result["h"] == "#existent"

