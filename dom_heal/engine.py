"""
Engine
======

Módulo responsável por orquestrar o fluxo de self-healing: extração do DOM, comparação dos seletores, atualização automática e geração de logs de alteração.

Principais funcionalidades:
- Executa o ciclo completo de self-healing a partir do JSON e URL informados
- Integra os módulos de extração, comparação, normalização e atualização dos seletores
- Gera logs detalhados dos elementos alterados para auditoria e rastreabilidade

Ideal para uso como ponto central da automação self-healing.
"""

from pathlib import Path
import json
from typing import Any, Dict
from dom_heal.extractor import extrair_dom
from dom_heal.comparator import gerar_diferencas
from dom_heal.healing import atualizar_seletores
from dom_heal.utils import normalizar_elementos

import requests

def gravar_json(caminho: Path, dados: Any) -> None:
    """
    Grava um dicionário ou lista como JSON em disco, criando diretórios necessários.

    Args:
        caminho (Path): Caminho do arquivo a ser salvo.
        dados (Any): Dados a serem serializados e gravados.
    """
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')

def salvar_diff_alterados(diferencas: dict, caminho_seletores: Path):
    """
    Salva um resumo das diferenças detectadas no processo de self-healing
    em um arquivo 'ElementosAlterados.json' na mesma pasta do JSON original.

    Args:
        diferencas (dict): Dicionário com diferenças entre seletores antigos e novos.
        caminho_seletores (Path): Caminho para o arquivo JSON de seletores.
    """
    caminho_alterados = caminho_seletores.parent / "ElementosAlterados.json"
    resumo = {k: v for k, v in diferencas.items() if v}
    if resumo:
        with caminho_alterados.open("w", encoding="utf-8") as arquivo:
            json.dump(resumo, arquivo, ensure_ascii=False, indent=2)

def self_heal(caminho_json: str, url: str) -> Dict[str, Any]:
    """
    Executa o processo completo de self-healing:
      - Extrai o DOM atual da URL informada
      - Carrega o JSON de seletores do usuário
      - Compara os seletores antigos com o novo DOM
      - Atualiza automaticamente os seletores
      - Gera e salva o log de alterações

    Args:
        caminho_json (str): Caminho para o arquivo JSON de seletores.
        url (str): URL da página a ser processada.

    Returns:
        Dict[str, Any]: Dicionário com mensagem de status e caminhos dos arquivos de log e JSON atualizado.

    Raises:
        RuntimeError: Se ocorrer erro ao baixar o HTML ou ler o JSON de seletores.
    """
    caminho_json = Path(caminho_json)
    dom_atual = extrair_dom(url)
    try:
        html_puro = requests.get(url).text
    except Exception as e:
        raise RuntimeError(f"Erro ao baixar HTML da página: {e}")
    try:
        raw_data = json.loads(caminho_json.read_text(encoding="utf-8"))
        seletores_antigos = normalizar_elementos(raw_data)
    except Exception as e:
        raise RuntimeError(f"Erro ao ler JSON de seletores: {e}")

    # Passa o HTML puro para o gerar_diferencas
    diferencas = gerar_diferencas(seletores_antigos, dom_atual, html_puro=html_puro)
    atualizar_seletores(diferencas, caminho_json)
    salvar_diff_alterados(diferencas, caminho_json)
    return {
        "msg": "Self-healing finalizado.",
        "log_detalhado": str(caminho_json.parent / "ElementosAlterados.json"),
        "json_atualizado": str(caminho_json)
    }
