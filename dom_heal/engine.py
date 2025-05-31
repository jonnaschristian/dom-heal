"""
Engine
======

Módulo responsável por orquestrar o fluxo principal do mecanismo de self-healing da DOM-Heal.

Principais responsabilidades:
- Extrair o DOM atual da página (via extractor)
- Comparar com o JSON de seletores fornecido (via comparator)
- Atualizar automaticamente o arquivo de seletores (via healing)
- Gerar log detalhado das alterações sugeridas (JSON de log)

Ideal para integração via linha de comando ou como biblioteca em outros projetos de automação.
"""

from pathlib import Path
import json
from typing import Any, Dict
from dom_heal.extractor import extrair_dom
from dom_heal.comparator import gerar_diferencas
from dom_heal.healing import atualizar_seletores
from dom_heal.utils import normalizar_elementos

def gravar_json(caminho: Path, dados: Any) -> None:
    """
    Grava dados em um arquivo JSON no caminho especificado.

    Args:
        caminho (Path): Caminho para o arquivo.
        dados (Any): Dados serializáveis em JSON.
    """
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')

def salvar_diff_alterados(diferencas: dict, caminho_seletores: Path):
    """
    Salva o log detalhado de alterações em 'ElementosAlterados.json', caso existam diferenças.

    Args:
        diferencas (dict): Dicionário retornado por gerar_diferencas().
        caminho_seletores (Path): Caminho do arquivo de seletores original.
    """
    caminho_alterados = caminho_seletores.parent / "ElementosAlterados.json"
    resumo = {k: v for k, v in diferencas.items() if v}
    if resumo:
        with caminho_alterados.open("w", encoding="utf-8") as arquivo:
            json.dump(resumo, arquivo, ensure_ascii=False, indent=2)

def self_heal(caminho_json: str, url: str) -> Dict[str, Any]:
    """
    Executa o processo completo de self-healing:

    - Extrai o DOM atual da URL informada.
    - Carrega o JSON de seletores do usuário.
    - Compara os seletores antigos com o novo DOM.
    - Atualiza automaticamente os seletores.
    - Gera e salva o log de alterações.

    Args:
        caminho_json (str): Caminho para o arquivo JSON de seletores.
        url (str): URL da página a ser analisada.

    Returns:
        dict: Informações sobre o processo, incluindo caminho dos logs e JSON atualizado.

    Raises:
        RuntimeError: Caso o JSON de seletores não possa ser lido.
    """
    caminho_json = Path(caminho_json)
    dom_atual = extrair_dom(url)
    try:
        raw_data = json.loads(caminho_json.read_text(encoding="utf-8"))
        seletores_antigos = normalizar_elementos(raw_data)
    except Exception as e:
        raise RuntimeError(f"Erro ao ler JSON de seletores: {e}")

    diferencas = gerar_diferencas(seletores_antigos, dom_atual)
    atualizar_seletores(diferencas, caminho_json)
    salvar_diff_alterados(diferencas, caminho_json)
    return {
        "msg": "Self-healing finalizado.",
        "log_detalhado": str(caminho_json.parent / "ElementosAlterados.json"),
        "json_atualizado": str(caminho_json)
    }
