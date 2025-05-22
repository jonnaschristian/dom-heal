"""
Módulo healing: responsável por atualizar o arquivo de seletores com base nas diferenças detectadas.
Aplica automaticamente adições, remoções, alterações e movimentações de elementos conforme o diff gerado, garantindo a manutenção dos seletores mais atuais e funcionais.
"""

import json
from pathlib import Path
from typing import Any, Dict

def atualizar_seletores(diferencas: Dict[str, Any], caminho_seletores: Path) -> None:
    """
    Atualiza o arquivo de seletores com base nas diferenças detectadas.
    Suporta adição, remoção, alteração e movimentação de elementos pelo XPath.
    """
    if not caminho_seletores.exists():
        raise FileNotFoundError(f"Arquivo de seletores não encontrado em {caminho_seletores}")

    with caminho_seletores.open('r', encoding='utf-8') as arquivo:
        seletores: Dict[str, Any] = json.load(arquivo)

    # Adicionados
    for xpath in diferencas.get('adicionados', []):
        if xpath not in seletores:
            seletores[xpath] = {}

    # Removidos
    for xpath in diferencas.get('removidos', []):
        seletores.pop(xpath, None)

    # Alterados
    for alterado in diferencas.get('alterados', []):
        xpath = alterado.get('xpath')
        mudancas = alterado.get('diferencas', {})
        if xpath in seletores:
            for atributo, valor in mudancas.items():
                seletores[xpath][atributo] = valor['depois']

    # Movidos
    for movido in diferencas.get('movidos', []):
        xpath_antigo = movido.get('de')
        xpath_novo = movido.get('para')
        if xpath_antigo in seletores:
            seletores[xpath_novo] = seletores.pop(xpath_antigo)

    with caminho_seletores.open('w', encoding='utf-8') as arquivo:
        json.dump(seletores, arquivo, ensure_ascii=False, indent=2)
