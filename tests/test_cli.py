import json
import pytest
from typer.testing import CliRunner
from dom_heal import cli
import dom_heal.engine as eng

runner = CliRunner()

@pytest.fixture(autouse=True)
def patch_self_heal(monkeypatch, tmp_path):
    """
    Por padrão, simula um retorno de sucesso do self_heal().
    Os testes podem sobrescrever essa fixture conforme necessário.
    """
    class DummyResult(dict):
        pass

    default = DummyResult({
        "log_detalhado": "log.txt",
        "json_atualizado": str(tmp_path / "updated.json")
    })
    monkeypatch.setattr(eng, "self_heal", lambda json_path, url: default)
    return default

def test_sobre_command():
    result = runner.invoke(cli.app, ["sobre"])
    assert result.exit_code == 0
    assert "DOM-Heal: Biblioteca de Self-Healing para Testes Automatizados" in result.stdout
    assert "2025" in result.stdout

def test_help_option():
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "rodar" in result.stdout
    assert "sobre" in result.stdout

def test_missing_options_rodar():
    # Sem opções obrigatórias, deve exibir mensagem de erro
    result = runner.invoke(cli.app, ["rodar"])
    assert result.exit_code != 0
    assert "Missing option" in result.stdout
