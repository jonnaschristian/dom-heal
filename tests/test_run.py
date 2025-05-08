# Suíte de testes unitários para run.py: valida formatação do resumo de diff via a função resumir_diff

import pytest
from runner import resumir_diff

# Caso de Teste: Resumo com todas as listas vazias deve mostrar zeros
def test_resumir_diff_zero():
    ordered = {'Adicionado': [], 'Removido': [], 'Alterado': [], 'Movido': []}
    assert resumir_diff(ordered) == "Adicionado: 0, Removido: 0, Alterado: 0, Movido: 0"

# Caso de Teste: Resumo com contagens variadas deve refletir corretamente cada valor
def test_resumir_diff_varias_contagens():
    ordered = {
        'Adicionado': [None, None],
        'Removido':  [None],
        'Alterado':  [None, None, None],
        'Movido':    [None, None, None, None]
    }
    assert resumir_diff(ordered) == "Adicionado: 2, Removido: 1, Alterado: 3, Movido: 4"
