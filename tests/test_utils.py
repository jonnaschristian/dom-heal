"""
Testes unitários para o módulo utils da biblioteca DOM-Heal.

Estes testes garantem o correto funcionamento das funções utilitárias, 
em especial a normalização de elementos, validando a conversão de dicionários 
em listas de elementos padronizados e assegurando compatibilidade entre formatos 
diferentes de entrada dos seletores.
"""

import pytest
from dom_heal.utils import normalizar_elementos

def test_normalizar_lista():
    data = [
        {"nome": "campo", "selector": "#id1"},
        {"nome": "btn", "selector": ".btn-classe"}
    ]
    resultado = normalizar_elementos(data)
    assert resultado is data  # deve retornar o mesmo objeto
    assert len(resultado) == 2
    assert resultado[0]["nome"] == "campo"
    assert resultado[1]["selector"] == ".btn-classe"

def test_normalizar_dict():
    data = {"campo": "#id1", "btn": ".btn-classe"}
    resultado = normalizar_elementos(data)
    assert isinstance(resultado, list)
    # Ordem não garantida, então validamos via conversão para conjunto de tuplas
    assert set((e["nome"], e["selector"]) for e in resultado) == {("campo", "#id1"), ("btn", ".btn-classe")}

def test_normalizar_dict_vazio():
    data = {}
    resultado = normalizar_elementos(data)
    assert isinstance(resultado, list)
    assert resultado == []

@pytest.mark.parametrize("invalid", [
    "uma string",
    123,
    None,
    5.6,
    (1, 2, 3)
])
def test_normalizar_invalidos_levanta_valueerror(invalid):
    with pytest.raises(ValueError) as exc:
        normalizar_elementos(invalid)
    assert "Formato de dados de seletores inválido" in str(exc.value)

