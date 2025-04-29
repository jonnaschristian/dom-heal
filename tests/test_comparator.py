# Suíte de testes unitários para comparator.py: valida leitura de snapshots e geração de diffs (adições, remoções, movimentos e alterações)

import json
import pytest
from pathlib import Path

# Ajuste este import conforme sua estrutura de pastas:
# from core.comparator import ler_snapshot, gerar_diferencas
from self_healing.core.comparator import ler_snapshot, gerar_diferencas


# Caso de Teste: Ler snapshot com JSON válido deve retornar lista
def test_ls_valido_retorna_lista(tmp_path: Path):
    data = [{"xpath": "/html", "id": "elem"}]
    arquivo = tmp_path / "valid.json"
    arquivo.write_text(json.dumps(data), encoding="utf-8")
    resultado = ler_snapshot(arquivo)
    assert isinstance(resultado, list)


# Caso de Teste: Ler snapshot com JSON válido deve retornar conteúdo exato
def test_ls_valido_retorna_conteudo(tmp_path: Path):
    data = [{"xpath": "/html", "id": "elem"}]
    arquivo = tmp_path / "valid.json"
    arquivo.write_text(json.dumps(data), encoding="utf-8")
    resultado = ler_snapshot(arquivo)
    assert resultado == data


# Caso de Teste: Ler snapshot com JSON malformado deve retornar lista vazia
def test_ls_invalido_retorna_vazio(tmp_path: Path):
    arquivo = tmp_path / "invalid.json"
    arquivo.write_text("not a json", encoding="utf-8")
    resultado = ler_snapshot(arquivo)
    assert resultado == []


# Caso de Teste: Ler snapshot com caminho inexistente deve retornar lista vazia
def test_ls_arquivo_inexistente_retorna_vazio(tmp_path: Path):
    arquivo = tmp_path / "no_file.json"
    resultado = ler_snapshot(arquivo)
    assert resultado == []


# Caso de Teste: Gerar diferenças com snapshots idênticos deve retornar tudo vazio
def test_diff_identicos_sem_alteracoes():
    antes = [{"xpath": "/a", "id": "", "tag": "div"}]
    depois = [{"xpath": "/a", "id": "", "tag": "div"}]
    diff = gerar_diferencas(antes, depois)
    assert diff == {
        "adicionados": [],
        "removidos": [],
        "alterados": [],
        "movidos": []
    }


# Caso de Teste: Gerar diferenças com apenas adições deve preencher somente “adicionados”
def test_diff_somente_adicoes():
    antes = []
    depois = [{"xpath": "/a", "id": "", "tag": "div"}]
    diff = gerar_diferencas(antes, depois)
    assert diff["adicionados"] == ["/a"]


# Caso de Teste: Gerar diferenças com apenas remoções deve preencher somente “removidos”
def test_diff_somente_remocoes():
    antes = [{"xpath": "/a", "id": "", "tag": "div"}]
    depois = []
    diff = gerar_diferencas(antes, depois)
    assert diff["removidos"] == ["/a"]


# Caso de Teste: Gerar diferenças com alteração de atributo deve preencher “alterados”
def test_diff_alteracao_atributo():
    antes = [{"xpath": "/a", "id": "", "tag": "div", "class": "old"}]
    depois = [{"xpath": "/a", "id": "", "tag": "div", "class": "new"}]
    diff = gerar_diferencas(antes, depois)
    assert diff["alterados"] == [
        {"xpath": "/a", "diferencas": {"class": {"antes": "old", "depois": "new"}}}
    ]


# Caso de Teste: Gerar diferenças com movimento por ID deve preencher “movidos”
def test_diff_movimento_por_id():
    antes = [{"xpath": "/a", "id": "ID1", "tag": "div"}]
    depois = [{"xpath": "/b", "id": "ID1", "tag": "div"}]
    diff = gerar_diferencas(antes, depois, limiar=1.1)
    assert diff["movidos"] == [{"id": "ID1", "de": "/a", "para": "/b"}]


# Caso de Teste: Gerar diferenças com movimento fuzzy deve preencher “movidos”
def test_diff_movimento_fuzzy():
    antes = [{"xpath": "/x1", "id": "", "tag": "p", "text": "foo"}]
    depois = [{"xpath": "/x2", "id": "", "tag": "p", "text": "foo"}]
    diff = gerar_diferencas(antes, depois)
    mov = diff["movidos"][0]
    assert isinstance(mov["similaridade"], float)


# Caso de Teste: Gerar diferenças com limiar alto não deve movimentar
def test_diff_sem_movimento_limiar_alto():
    antes = [{"xpath": "/x1", "id": "", "tag": "p", "text": "foo"}]
    depois = [{"xpath": "/x2", "id": "", "tag": "p", "text": "foo"}]
    diff = gerar_diferencas(antes, depois, limiar=1.1)
    assert diff["movidos"] == []


# Caso de Teste: Gerar diferenças com alteração em data_* deve detectar em “alterados”
def test_diff_alteracao_data_attr():
    antes = [{"xpath": "/d", "id": "", "tag": "div", "data_test": "foo"}]
    depois = [{"xpath": "/d", "id": "", "tag": "div", "data_test": "bar"}]
    diff = gerar_diferencas(antes, depois)
    assert diff["alterados"] == [
        {"xpath": "/d", "diferencas": {"data_test": {"antes": "foo", "depois": "bar"}}}
    ]


# Caso de Teste: Removidos seguem ordem de antes (hierarquia T0)
def test_diff_preserva_ordem_removidos():
    antes = [
        {'xpath': '/html/body/div[1]', 'id': '', 'tag': 'div'},
        {'xpath': '/html/body/div[2]', 'id': '', 'tag': 'div'},
        {'xpath': '/html/body/div[3]', 'id': '', 'tag': 'div'},
    ]
    depois = []
    diff = gerar_diferencas(antes, depois)
    assert diff["removidos"] == [
        '/html/body/div[1]',
        '/html/body/div[2]',
        '/html/body/div[3]',
    ]


# Caso de Teste: Adicionados seguem ordem de depois (hierarquia T1)
def test_diff_preserva_ordem_adicionados():
    antes = []
    depois = [
        {'xpath': '/html/body/section[1]', 'id': '', 'tag': 'section'},
        {'xpath': '/html/body/section[2]', 'id': '', 'tag': 'section'},
        {'xpath': '/html/body/section[3]', 'id': '', 'tag': 'section'},
    ]
    diff = gerar_diferencas(antes, depois)
    assert diff["adicionados"] == [
        '/html/body/section[1]',
        '/html/body/section[2]',
        '/html/body/section[3]',
    ]
