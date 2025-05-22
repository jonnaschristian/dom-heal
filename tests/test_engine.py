"""
Testes unitários para o módulo engine.
Cobre as principais funções utilitárias e o fluxo de self-healing:
- Criação e gravação de JSON
- Geração de log de alterações
- Execução do fluxo principal com mocks (criação do baseline)
"""

import pytest
import json
from pathlib import Path
from dom_heal.engine import gravar_json, salvar_diff_alterados, self_heal

def test_gravar_json_cria_arquivo_e_diretorio(tmp_path):
    # Testa criação de JSON e diretório novo
    dados = {"campo": 123}
    caminho = tmp_path / "nova_pasta" / "arquivo.json"
    gravar_json(caminho, dados)
    assert caminho.exists()
    with caminho.open(encoding="utf-8") as arq:
        salvo = json.load(arq)
    assert salvo == dados

def test_salvar_diff_alterados(tmp_path):
    # Testa se só campos com valor diferente são salvos
    seletores_json = tmp_path / "seletores.json"
    seletores_json.write_text("{}", encoding="utf-8")
    diferencas = {"adicionados": ["el1"], "removidos": [], "alterados": [], "movidos": ["el2"]}
    salvar_diff_alterados(diferencas, seletores_json)
    caminho_log = seletores_json.parent / "ElementosAlterados.json"
    assert caminho_log.exists()
    with caminho_log.open(encoding="utf-8") as arq:
        log = json.load(arq)
    assert "adicionados" in log and "movidos" in log
    assert "removidos" not in log  # pois está vazio
    assert "alterados" not in log  # pois está vazio

def test_self_heal_baseline(monkeypatch, tmp_path):
    # Testa comportamento quando o snapshot baseline ainda não existe
    caminho_json = tmp_path / "seletores.json"
    caminho_json.write_text(json.dumps([{"xpath": "/a", "id": "x"}]), encoding="utf-8")

    # Mock extrair_snapshot para simular retorno da página (T1)
    monkeypatch.setattr("dom_heal.engine.extrair_snapshot", lambda url: [{"xpath": "/a", "id": "x"}])
    # Mock gerar_diferencas para não comparar nada
    monkeypatch.setattr("dom_heal.engine.gerar_diferencas", lambda t0, t1: {})
    # Mock atualizar_seletores só para não dar erro
    monkeypatch.setattr("dom_heal.engine.atualizar_seletores", lambda diff, caminho: None)

    from dom_heal.engine import DIRETORIO_SNAPSHOTS
    resultado = self_heal(str(caminho_json), "http://dummy")
    # O baseline deve ser salvo e não rodar o healing completo
    id_url = caminho_json.stem.replace(" ", "_").replace(".", "_")
    caminho_snapshot = DIRETORIO_SNAPSHOTS / f"{id_url}.json"
    assert "Self-healing finalizado" in resultado["msg"]

def test_self_heal_aplica_healing(monkeypatch, tmp_path):
    # Simula baseline já existente e aplica um diff fictício
    caminho_json = tmp_path / "seletores.json"
    caminho_json.write_text(json.dumps([{"xpath": "/a", "id": "x"}]), encoding="utf-8")
    id_url = caminho_json.stem.replace(" ", "_").replace(".", "_")
    from dom_heal.engine import DIRETORIO_SNAPSHOTS
    DIRETORIO_SNAPSHOTS.mkdir(exist_ok=True)
    caminho_snapshot = DIRETORIO_SNAPSHOTS / f"{id_url}.json"
    caminho_snapshot.write_text(json.dumps([{"xpath": "/a", "id": "x"}]), encoding="utf-8")
    # Mocks
    monkeypatch.setattr("dom_heal.engine.extrair_snapshot", lambda url: [{"xpath": "/b", "id": "y"}])
    monkeypatch.setattr("dom_heal.engine.gerar_diferencas", lambda t0, t1: {"adicionados": ["/b"]})
    logs = []
    monkeypatch.setattr("dom_heal.engine.atualizar_seletores", lambda diff, caminho: logs.append(diff))
    resultado = self_heal(str(caminho_json), "http://dummy")
    assert "Self-healing finalizado" in resultado["msg"]