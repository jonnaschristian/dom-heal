"""
Testes unitários para o módulo engine da biblioteca DOM-Heal.

Cobrem o fluxo completo da função `self_heal` incluindo:
- Geração de JSON com seletores antigos
- Chamada e integração de funções internas: extrair_dom, gerar_diferencas, atualizar_seletores
- Mock de requisição HTTP (`requests.get`) para evitar conexões reais
- Verificação dos caminhos retornados no dicionário de resultado
"""
import pytest
import json
from pathlib import Path

import dom_heal.engine as eng

class DummyResponse:
    def __init__(self, text, as_json=None):
        self.text = text
        self._json = as_json
    def json(self):
        if self._json is not None:
            return self._json
        raise ValueError("No JSON")

def test_gravar_json_cria_arquivo(tmp_path):
    data = {"x": 1}
    out = tmp_path / "out.json"
    # Ordem correta: gravar_json(caminho, dados)
    eng.gravar_json(out, data)
    assert out.exists()
    assert json.loads(out.read_text()) == data


def test_self_heal_download_fail(tmp_path, monkeypatch):
    caminho = tmp_path / "seletores.json"
    caminho.write_text(json.dumps([{"nome":"x","selector":"#x"}]), encoding="utf-8")
    monkeypatch.setattr(eng, "extrair_dom", lambda url: [])
    monkeypatch.setattr("requests.get", lambda url: (_ for _ in ()).throw(Exception("fail")))
    with pytest.raises(RuntimeError) as ei:
        eng.self_heal(str(caminho), "http://x")
    assert "Erro ao baixar HTML" in str(ei.value)

def test_self_heal_json_fail(tmp_path, monkeypatch):
    caminho = tmp_path / "invalido.json"
    caminho.write_text("not valid json", encoding="utf-8")
    monkeypatch.setattr(eng, "extrair_dom", lambda url: [])
    monkeypatch.setattr("requests.get", lambda url: DummyResponse("<html></html>"))
    with pytest.raises(RuntimeError) as ei:
        eng.self_heal(str(caminho), "http://ok")
    assert "Erro ao ler JSON" in str(ei.value)

def test_self_heal_success(tmp_path, monkeypatch):
    caminho = tmp_path / "ok.json"
    caminho.write_text(json.dumps([{"nome":"btn","selector":"#a"}]), encoding="utf-8")
    monkeypatch.setattr(eng, "extrair_dom", lambda url: [{"tag":"div"}])
    monkeypatch.setattr(eng, "gerar_diferencas", lambda *a, **k: {"alterados":[{"nome":"btn"}]})
    monkeypatch.setattr(eng, "atualizar_seletores", lambda *a, **k: None)
    monkeypatch.setattr("requests.get", lambda url: DummyResponse("<html></html>"))
    result = eng.self_heal(str(caminho), "http://ok")
    assert "finalizado" in result["msg"]
    assert result["json_atualizado"].endswith(".json")

def test_self_heal_sem_alteracoes(tmp_path, monkeypatch):
    caminho = tmp_path / "nochange.json"
    caminho.write_text(json.dumps([{"nome":"btn","selector":"#a"}]), encoding="utf-8")
    monkeypatch.setattr(eng, "extrair_dom", lambda url: [])
    monkeypatch.setattr(eng, "gerar_diferencas", lambda *a, **k: {})
    monkeypatch.setattr(eng, "atualizar_seletores", lambda *a, **k: None)
    monkeypatch.setattr("requests.get", lambda url: DummyResponse("<html></html>"))
    result = eng.self_heal(str(caminho), "http://ok")
    assert "Self-healing finalizado" in result["msg"]
    assert result["json_atualizado"].endswith(".json")

