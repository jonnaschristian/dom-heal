"""
Healing
=======

Módulo responsável por atualizar o arquivo de seletores (JSON de elementos lógicos)
com base nas diferenças detectadas pelo mecanismo de self-healing.

Principais responsabilidades:
- Atualizar seletores alterados (nome_lógico → novo seletor)
- Remover seletores obsoletos
- Adicionar novos seletores identificados
- Compatível com múltiplos formatos de diff (nome, nome_lógico, xpath)

Ideal para ser chamado pelo engine ou integrado diretamente a outros fluxos de automação.

"""

import json
from pathlib import Path
from typing import Any, Dict

def atualizar_seletores(diferencas: Dict[str, Any], caminho_seletores: Path) -> None:
    """
    Atualiza o arquivo de seletores (JSON: nome_lógico → seletor) conforme as diferenças encontradas.
    Aplica alterações, remoções ou adições de seletores de acordo com as chaves do diff.

    Args:
        diferencas (dict): Dicionário de alterações (ex: 'alterados', 'removidos', 'adicionados').
        caminho_seletores (Path): Caminho do arquivo JSON de seletores.

    Raises:
        FileNotFoundError: Se o arquivo de seletores não existir.
    """
    if not caminho_seletores.exists():
        raise FileNotFoundError(f"Arquivo de seletores não encontrado em {caminho_seletores}")

    with caminho_seletores.open('r', encoding='utf-8') as arquivo:
        seletores: Dict[str, Any] = json.load(arquivo)

    # Atualiza seletores alterados
    for alterado in diferencas.get('alterados', []):
        chave = alterado.get('nome_logico') or alterado.get('nome') or alterado.get('xpath')
        novo_seletor = alterado.get('novo_seletor')
        if chave and novo_seletor:
            seletores[chave] = novo_seletor

    # Atualiza seletores movidos (compatibilidade com diffs futuros)
    for movido in diferencas.get('movidos', []):
        chave = movido.get('nome_logico') or movido.get('nome') or movido.get('xpath')
        novo_seletor = movido.get('novo_seletor')
        if chave and novo_seletor:
            seletores[chave] = novo_seletor

    # Remove seletores
    for removido in diferencas.get('removidos', []):
        chave = (removido.get('nome_logico') or removido.get('nome') or removido.get('xpath')) if isinstance(removido, dict) else removido
        if chave in seletores:
            del seletores[chave]

    # Adiciona seletores novos (compatibilidade)
    for adicionado in diferencas.get('adicionados', []):
        nome = adicionado.get('nome_logico') or adicionado.get('nome') or adicionado.get('xpath')
        seletor = adicionado.get('novo_seletor') or adicionado.get('selector')
        if nome and seletor and nome not in seletores:
            seletores[nome] = seletor

    with caminho_seletores.open('w', encoding='utf-8') as arquivo:
        json.dump(seletores, arquivo, ensure_ascii=False, indent=2)
