"""
Arquivo utilitário para execuções manuais e testes rápidos.
NÃO faz parte do pacote oficial dom_heal.
Use o CLI para integração real.
"""


from pathlib import Path
import json
from typing import Any, Dict
from dom_heal.extractor import extrair_snapshot
from dom_heal.comparator import gerar_diferencas
from dom_heal.healing import atualizar_selectors

# Diretórios de trabalho do projeto
BASE_DIR = Path.cwd()
SNAPSHOTS_DIR = BASE_DIR / 'snapshots'
DIFFS_DIR     = BASE_DIR / 'diffs'


def _write_json(path: Path, data: Any) -> None:
    """Garante diretório e grava `data` como JSON em `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def heal(tela: str, elements_file: str) -> Dict[str, Any]:
    """
    Realiza self-healing para a etapa `tela`, usando o arquivo de elementos especificado:

    1. Captura o estado atual do DOM (snapshot).
    2. Se não existe baseline em snapshots/<tela>.json:
       - Grava o snapshot como baseline (T0).
       - Retorna esse snapshot.
    3. Caso exista baseline:
       a) Lê snapshots/<tela>.json (T0).
       b) Gera diff entre T0 e o snapshot atual (T1).
       c) Salva diffs/<tela>_diff.json.
       d) Se `elements_file` já existe:
          - Atualiza esse JSON de elementos via atualizar_selectors.
          - Retorna o conteúdo atualizado desse JSON.
       e) Se `elements_file` não existe:
          - Cria um novo JSON em `elements_file` com {'suggestions': diffs}.
          - Retorna esse dicionário de sugestões.
    """
    elems_path = Path(elements_file)
    snapshot_path = SNAPSHOTS_DIR / f"{tela}.json"

    # 1) Captura DOM atual
    current = extrair_snapshot(tela)

    # 2) Baseline: primeira execução
    if not snapshot_path.exists():
        _write_json(snapshot_path, current)
        return current

    # 3) Healing: baseline existe
    t0 = json.loads(snapshot_path.read_text(encoding='utf-8'))
    diffs = gerar_diferencas(t0, current)

    # 3c) Salva diff em disco
    diff_path = DIFFS_DIR / f"{tela}_diff.json"
    _write_json(diff_path, diffs)

    # 3d) Atualiza ou cria JSON de elementos/sugestões
    if elems_path.exists() and elems_path.suffix.lower() == '.json':
        updated = atualizar_selectors(diffs, elems_path)
        return updated
    else:
        suggestions = {'suggestions': diffs}
        _write_json(elems_path, suggestions)
        return suggestions