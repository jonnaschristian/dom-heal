"""
Módulo healing: responsável por atualizar o arquivo de seletores (JSON de elementos lógicos)
com base nas diferenças detectadas.
Aplica automaticamente alterações, remoções e atualizações de seletores CSS por nome lógico.
"""

import json
from pathlib import Path
from typing import Any, Dict

def atualizar_seletores(diferencas: Dict[str, Any], caminho_seletores: Path) -> None:
    """
    Atualiza o arquivo de seletores (JSON de elementos lógicos: nome → seletor) com base nas diferenças.
    - Alterados/movidos: atualiza o seletor CSS da chave correspondente
    - Removidos: deleta a chave
    - Adicionados: cria chave (opcional, se desejar)
    """
    if not caminho_seletores.exists():
        raise FileNotFoundError(f"Arquivo de seletores não encontrado em {caminho_seletores}")

    with caminho_seletores.open('r', encoding='utf-8') as arquivo:
        seletores: Dict[str, Any] = json.load(arquivo)

    # Alterados (atualiza seletor da chave)
    for alterado in diferencas.get('alterados', []):
        chave = alterado.get('nome_logico') or alterado.get('xpath')  # depende do diff
        novo_seletor = alterado.get('novo_seletor')
        if chave and novo_seletor:
            seletores[chave] = novo_seletor

    # Movidos (atualiza seletor da chave)
    for movido in diferencas.get('movidos', []):
        chave = movido.get('nome_logico') or movido.get('xpath')
        novo_seletor = movido.get('novo_seletor')
        if chave and novo_seletor:
            seletores[chave] = novo_seletor

    # Removidos (deleta chave)
    for removido in diferencas.get('removidos', []):
        if removido in seletores:
            del seletores[removido]

    # Adicionados (opcional — depende se o diff traz algum campo)
    for adicionado in diferencas.get('adicionados', []):
        nome = adicionado.get('nome_logico')
        seletor = adicionado.get('novo_seletor')
        if nome and seletor and nome not in seletores:
            seletores[nome] = seletor

    with caminho_seletores.open('w', encoding='utf-8') as arquivo:
        json.dump(seletores, arquivo, ensure_ascii=False, indent=2)
