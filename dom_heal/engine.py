"""
Módulo engine: orquestra o fluxo principal de self-healing externo.
Gerencia extração do DOM atual, comparação com o JSON de seletores fornecido pelo usuário,
atualização automática do arquivo de seletores e geração dos logs detalhados de alterações.
"""

from pathlib import Path
import json
from typing import Any, Dict
from dom_heal.extractor import extrair_dom
from dom_heal.comparator import gerar_diferencas
from dom_heal.healing import atualizar_seletores

def gravar_json(caminho: Path, dados: Any) -> None:
    """Cria diretórios necessários e grava `dados` como JSON em `caminho`."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')

def salvar_diff_alterados(diferencas: dict, caminho_seletores: Path):
    """
    Salva apenas as alterações detectadas em um novo JSON no mesmo diretório do arquivo original de seletores.
    """
    caminho_alterados = caminho_seletores.parent / "ElementosAlterados.json"
    resumo = {k: v for k, v in diferencas.items() if v}
    if resumo:
        with caminho_alterados.open("w", encoding="utf-8") as arquivo:
            json.dump(resumo, arquivo, ensure_ascii=False, indent=2)

def self_heal(caminho_json: str, url: str) -> Dict[str, Any]:
    """
    Fluxo externo de self-healing (sem baseline/snapshots):
      1. Extrai DOM atual da página (via Selenium)
      2. Carrega JSON de seletores antigo (fornecido pelo usuário)
      3. Compara JSON de seletores antigo com DOM atual
      4. Atualiza JSON de seletores com as sugestões (healing)
      5. Gera log das alterações no mesmo diretório do JSON
    """
    caminho_json = Path(caminho_json)

    # 1. Extrai DOM atual
    dom_atual = extrair_dom(url)

    # 2. Carrega JSON de seletores antigo
    try:
        seletores_antigos = json.loads(caminho_json.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Erro ao ler JSON de seletores: {e}")

    # 3. Compara seletores antigos com DOM atual
    diferencas = gerar_diferencas(seletores_antigos, dom_atual)

    # 4. Atualiza seletores com as sugestões de healing
    atualizar_seletores(diferencas, caminho_json)

    # 5. Salva log detalhado no mesmo diretório do JSON original
    salvar_diff_alterados(diferencas, caminho_json)

    return {
        "msg": "Self-healing finalizado.",
        "log_detalhado": str(caminho_json.parent / "ElementosAlterados.json"),
        "json_atualizado": str(caminho_json)
    }
