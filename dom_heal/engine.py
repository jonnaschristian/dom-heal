"""
Módulo engine: orquestra o fluxo principal de self-healing.
Gerencia extração dos snapshots do DOM, comparação de versões, atualização automática do arquivo de seletores e geração dos logs detalhados de alterações.
"""

from pathlib import Path
import json
from typing import Any, Dict
from dom_heal.extractor import extrair_snapshot
from dom_heal.comparator import gerar_diferencas
from dom_heal.healing import atualizar_seletores

# Diretórios base (raiz do projeto)
DIRETORIO_BASE = Path.cwd()
DIRETORIO_SNAPSHOTS = DIRETORIO_BASE / 'snapshots'
DIRETORIO_DIFFS = DIRETORIO_BASE / 'diffs'

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
    Fluxo externo de self-healing:
      1. Extrai snapshot atual do DOM da URL (T1)
      2. Carrega snapshot baseline salvo (T0) do diretório snapshots/
      3. Compara T0 e T1, gera diferencas
      4. Atualiza JSON de seletores com as sugestões (healing)
      5. Gera log das alterações detalhadas no mesmo diretório do JSON original
      6. Gera log geral das alterações no diretório diffs/
    """
    caminho_json = Path(caminho_json)
    id_url = (caminho_json.stem or "pagina").replace(" ", "_").replace(".", "_")
    caminho_snapshot = DIRETORIO_SNAPSHOTS / f"{id_url}.json"
    caminho_diff = DIRETORIO_DIFFS / f"{id_url}_diff.json"

    # 1. Extrai snapshot T1
    t1 = extrair_snapshot(url)

    # 2. Carrega baseline (T0)
    if not caminho_snapshot.exists():
        # Primeira execução: salva baseline e retorna
        gravar_json(caminho_snapshot, t1)
        return {"msg": f"Baseline salvo em {caminho_snapshot}. Rode novamente para self-healing."}

    t0 = json.loads(caminho_snapshot.read_text(encoding="utf-8"))

    # 3. Compara
    diferencas = gerar_diferencas(t0, t1)

    # 4. Atualiza seletores com as sugestões de healing
    atualizar_seletores(diferencas, caminho_json)

    # 5. Salva log detalhado no mesmo diretório do JSON original
    salvar_diff_alterados(diferencas, caminho_json)

    # 6. Salva log geral no diretório diffs/
    gravar_json(caminho_diff, diferencas)

    return {
        "msg": "Self-healing finalizado.",
        "log_detalhado": str(caminho_json.parent / "ElementosAlterados.json"),
        "diff_log": str(caminho_diff),
        "json_atualizado": str(caminho_json)
    }
