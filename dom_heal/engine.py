from pathlib import Path
import json
from typing import Any, Dict
from dom_heal.extractor import extrair_snapshot
from dom_heal.comparator import gerar_diferencas

# Diretórios base (raiz do projeto)
BASE_DIR = Path.cwd()
SNAPSHOTS_DIR = BASE_DIR / 'snapshots'
DIFFS_DIR    = BASE_DIR / 'diffs'

# Cache temporário de snapshots T0
_snapshot_cache: Dict[str, Any] = {}


def _write_json(path: Path, data: Any) -> None:
    """Cria diretórios necessários e grava `data` como JSON em `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def iniciar_snapshot(tela: str) -> None:
    """
    Captura o estado atual do DOM (T0) para a etapa `tela` e armazena em cache.
    """
    _snapshot_cache[tela] = extrair_snapshot(tela)


def concluir_com_sucesso(tela: str) -> None:
    """
    Grava o snapshot T0 no diretório de snapshots e limpa o cache.
    """
    try:
        snapshot = _snapshot_cache.pop(tela)
    except KeyError:
        raise ValueError(f"Snapshot não iniciado para '{tela}'")
    _write_json(SNAPSHOTS_DIR / f"{tela}.json", snapshot)


def tratar_falha(tela: str, framework: str = 'cypress') -> None:
    """
    Em caso de falha na etapa `tela`:
    1) Captura T1 (novo snapshot)
    2) Lê T0 oficial de disco
    3) Calcula diffs entre T0 e T1
    4) Grava diffs em arquivo e:
       - se `cypress`, chama a lógica de healing para atualizar seletores;
       - caso contrário, gera relatorio_sugestoes.json.
    """
    # 1) T1
    t1 = extrair_snapshot(tela)

    # 2) T0 do disco
    t0_file = SNAPSHOTS_DIR / f"{tela}.json"
    if not t0_file.exists():
        raise FileNotFoundError(f"Snapshot oficial não encontrado: {t0_file}")
    t0 = json.loads(t0_file.read_text(encoding='utf-8'))

    # 3) diffs
    diffs = gerar_diferencas(t0, t1)

    # 4a) grava diffs
    _write_json(DIFFS_DIR / f"{tela}_diff.json", diffs)

    # 4b) atualiza ou sugere
    if framework.lower() == 'cypress':
        from dom_heal.healing import atualizar_selectors
        atualizar_selectors(diffs)
    else:
        report = {'suggestions': diffs}
        _write_json(BASE_DIR / 'relatorio_sugestoes.json', report)
