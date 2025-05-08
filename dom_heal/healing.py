import json
from pathlib import Path
from typing import Any, Dict


def atualizar_selectors(diffs: Dict[str, Any]) -> None:
    """
    Atualiza o arquivo selectors.json com base nas diferenças geradas pelo diff:
      1. Carrega selectors.json na raiz do projeto.
      2. Para cada entrada em `diffs`, aplica a atualização necessária nos seletores.
      3. Grava o arquivo selectors.json corrigido.
    """
    selectors_path = Path.cwd() / 'selectors.json'
    if not selectors_path.exists():
        raise FileNotFoundError(f"Arquivo selectors.json não encontrado em {selectors_path}")

    # 1) Carrega selectors existentes
    with selectors_path.open('r', encoding='utf-8') as f:
        selectors: Dict[str, Any] = json.load(f)

    # 2) Lógica de healing (exemplo simplificado)
    # TODO: implementar a lógica real de substituição de seletores
    for diff in diffs.get('moved', []):
        old_sel = diff.get('old_selector')
        new_sel = diff.get('new_selector')
        if old_sel in selectors:
            selectors[old_sel] = new_sel

    # 3) Grava selectors atualizados
    with selectors_path.open('w', encoding='utf-8') as f:
        json.dump(selectors, f, ensure_ascii=False, indent=2)