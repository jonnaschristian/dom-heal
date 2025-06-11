from pathlib import Path
import json
from typing import Any, Dict
from dom_heal.extractor import extrair_dom
from dom_heal.comparator import gerar_diferencas
from dom_heal.healing import atualizar_seletores
from dom_heal.utils import normalizar_elementos

import requests  # Adiciona requests para baixar o HTML puro

def gravar_json(caminho: Path, dados: Any) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')

def salvar_diff_alterados(diferencas: dict, caminho_seletores: Path):
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
    """
    caminho_json = Path(caminho_json)
    dom_atual = extrair_dom(url)
    # Baixe o HTML puro da página também
    try:
        html_puro = requests.get(url).text
    except Exception as e:
        raise RuntimeError(f"Erro ao baixar HTML da página: {e}")
    try:
        raw_data = json.loads(caminho_json.read_text(encoding="utf-8"))
        seletores_antigos = normalizar_elementos(raw_data)
    except Exception as e:
        raise RuntimeError(f"Erro ao ler JSON de seletores: {e}")

    # Passa o HTML puro para o gerar_diferencas (ajuste o comparator.py para receber esse param)
    diferencas = gerar_diferencas(seletores_antigos, dom_atual, html_puro=html_puro)
    atualizar_seletores(diferencas, caminho_json)
    salvar_diff_alterados(diferencas, caminho_json)
    return {
        "msg": "Self-healing finalizado.",
        "log_detalhado": str(caminho_json.parent / "ElementosAlterados.json"),
        "json_atualizado": str(caminho_json)
    }
