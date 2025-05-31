"""
Testes unitários para o módulo utils da biblioteca DOM-Heal.

Estes testes garantem o correto funcionamento das funções utilitárias, 
em especial a normalização de elementos, validando a conversão de dicionários 
em listas de elementos padronizados e assegurando compatibilidade entre formatos 
diferentes de entrada dos seletores.
"""

def test_normalizar_elementos_dict():
    from dom_heal.utils import normalizar_elementos
    entrada = {"a": "#a", "b": "#b"}
    saida = normalizar_elementos(entrada)
    assert isinstance(saida, list)
    assert saida[0]["nome"] == "a"

def test_normalizar_elementos_list():
    from dom_heal.utils import normalizar_elementos
    entrada = [{"nome": "x", "selector": "#x"}]
    saida = normalizar_elementos(entrada)
    assert saida == entrada
