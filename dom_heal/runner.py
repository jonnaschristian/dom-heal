"""
Módulo runner: orquestra a captura de snapshots T0/T1, gera diff.json e aplica execução principal do self-healing.
"""
import os
import time
import json
from pathlib import Path
from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Suprime logs de TensorFlow Lite para não poluir a saída
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_CPP_MIN_VLOG_LEVEL'] = '3'

# Silencia logs HTTP do servidor
for fn in ("log_request", "log_error", "log_message"):
    setattr(SimpleHTTPRequestHandler, fn, lambda *args, **kwargs: None)
HTTPServer.handle_error = lambda self, request, client_address: None

from dom_heal.extractor import criar_driver, carregar_pagina, obter_xpath, GET_DATA_ATTRS_JS
from dom_heal.comparator import gerar_diferencas, ler_snapshot
from selenium.webdriver.common.by import By


def resumir_diff(ordered: dict) -> str:
    """
    Gera um resumo das diferenças encontradas no diff.json.

    Args:
        ordered (dict): Dicionário com chaves 'Adicionado', 'Removido', 'Alterado', 'Movido'.

    Returns:
        str: String formatada como 'Adicionado: X, Removido: Y, Alterado: Z, Movido: W'.
    """
    return (
        f"Adicionado: {len(ordered['Adicionado'])}, "
        f"Removido: {len(ordered['Removido'])}, "
        f"Alterado: {len(ordered['Alterado'])}, "
        f"Movido: {len(ordered['Movido'])}"
    )


def main():
    """
    Fluxo principal:
      1. Inicia servidor HTTP silencioso para servir arquivos locais.
      2. Captura snapshot T0 do DOM.
      3. Aguarda intervalo configurado.
      4. Captura snapshot T1 do DOM.
      5. Gera e grava diff.json com diferenças entre T0 e T1.
      6. Imprime resumo das alterações.
    """
    PORTA = 8000
    INTERVALO = 10  # segundos entre T0 e T1
    DIRETORIO_DADOS = Path(__file__).parent / 'data'
    DIRETORIO_DADOS.mkdir(exist_ok=True)
    URL = f'http://localhost:{PORTA}/index.html'

    # Inicia servidor HTTP em background
    Thread(
        target=lambda: HTTPServer(('localhost', PORTA), SimpleHTTPRequestHandler).serve_forever(),
        daemon=True
    ).start()

    # Inicializa driver e carrega página
    driver = criar_driver()
    carregar_pagina(driver, URL)

    # Captura snapshot T0
    snapshot_t0 = []
    for el in driver.find_elements(By.XPATH, "//body//*"):
        info = {
            'tag':        el.tag_name,
            'id':         el.get_attribute('id') or '',
            'class':      el.get_attribute('class') or '',
            'text':       el.text.strip(),
            'name':       el.get_attribute('name') or '',
            'type':       el.get_attribute('type') or '',
            'aria_label': el.get_attribute('aria-label') or '',
            'xpath':      obter_xpath(driver, el)
        }
        data_attrs = driver.execute_script(GET_DATA_ATTRS_JS, el)
        info.update(data_attrs)
        snapshot_t0.append(info)

    (DIRETORIO_DADOS / 't0.json').write_text(
        json.dumps(snapshot_t0, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    # Espera o intervalo
    time.sleep(INTERVALO)

    # Captura snapshot T1
    snapshot_t1 = []
    for el in driver.find_elements(By.XPATH, "//body//*"):
        info = {
            'tag':        el.tag_name,
            'id':         el.get_attribute('id') or '',
            'class':      el.get_attribute('class') or '',
            'text':       el.text.strip(),
            'name':       el.get_attribute('name') or '',
            'type':       el.get_attribute('type') or '',
            'aria_label': el.get_attribute('aria-label') or '',
            'xpath':      obter_xpath(driver, el)
        }
        data_attrs = driver.execute_script(GET_DATA_ATTRS_JS, el)
        info.update(data_attrs)
        snapshot_t1.append(info)

    (DIRETORIO_DADOS / 't1.json').write_text(
        json.dumps(snapshot_t1, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    # Fecha o driver
    driver.quit()

    # Gera diff e grava
    raw = gerar_diferencas(
        ler_snapshot(DIRETORIO_DADOS / 't0.json'),
        ler_snapshot(DIRETORIO_DADOS / 't1.json')
    )
    ordered = {
        'Adicionado': raw['adicionados'],
        'Removido':   raw['removidos'],
        'Alterado':   raw['alterados'],
        'Movido':     raw['movidos'],
    }
    (DIRETORIO_DADOS / 'diff.json').write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    # Imprime resumo
    print(resumir_diff(ordered))

if __name__ == "__main__":
    main()
