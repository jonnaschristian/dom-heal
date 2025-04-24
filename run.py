#!/usr/bin/env python3
# run_simplificado.py
# Orquestra snapshots e diff em uma única instância de Chrome

import os
# Suprimir logs de TensorFlow Lite
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_CPP_MIN_VLOG_LEVEL'] = '3'

import sys
# Filtrar mensagens indesejadas (TensorFlow Lite e similares)
class FilteredWriter:
    def __init__(self, orig):
        self.orig = orig
    def write(self, text):
        # ignora linhas sobre TensorFlow Lite ou delegates
        if 'TensorFlow Lite' in text:
            return
        self.orig.write(text)
    def flush(self):
        self.orig.flush()

sys.stdout = FilteredWriter(sys.stdout)
sys.stderr = FilteredWriter(sys.stderr)

import time
import json
from pathlib import Path
from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler

from self_healing.core.extractor import criar_driver, obter_xpath, carregar_pagina, GET_DATA_ATTRS_JS
from self_healing.core.comparator import gerar_diferencas, ler_snapshot
from selenium.webdriver.common.by import By

# Configurações
PORTA = 8000
INTERVALO = 10  # segundos entre T0 e T1
DIRETORIO_DADOS = Path(__file__).parent / 'data'
DIRETORIO_DADOS.mkdir(exist_ok=True)
URL = f'http://localhost:{PORTA}/index.html'

# Servidor HTTP silencioso (suprime logs e erros)
class QuietHandler(SimpleHTTPRequestHandler):
    def log_request(self, *args): pass
    def log_error(self, *args): pass
    def log_message(self, *args): pass
    def do_GET(self):
        try:
            super().do_GET()
        except ConnectionResetError:
            pass

class QuietHTTPServer(HTTPServer):
    def handle_error(self, request, client_address):
        # Suprime exceções de conexão forçada no log
        pass

# Inicia servidor em background
Thread(
    target=lambda: QuietHTTPServer(('localhost', PORTA), QuietHandler).serve_forever(),
    daemon=True
).start()

# 1) Inicializa driver e carrega página
driver = criar_driver()
carregar_pagina(driver, URL)

# 2) Captura snapshot T0
snapshot_t0 = []
elements = driver.find_elements(By.XPATH, "//body//*")
for el in elements:
    info = {
        'tag': el.tag_name,
        'id': el.get_attribute('id') or '',
        'class': el.get_attribute('class') or '',
        'text': el.text.strip(),
        'name': el.get_attribute('name') or '',
        'type': el.get_attribute('type') or '',
        'aria_label': el.get_attribute('aria-label') or '',
        'xpath': obter_xpath(driver, el)
    }
    data_attrs = driver.execute_script(GET_DATA_ATTRS_JS, el)
    info.update(data_attrs)
    snapshot_t0.append(info)
(DIRETORIO_DADOS / 't0.json').write_text(
    json.dumps(snapshot_t0, ensure_ascii=False, indent=2), encoding='utf-8'
)

# 3) Espera intervalo para o script do index.html atualizar o DOM
time.sleep(INTERVALO)

# 4) Captura snapshot T1 na mesma instância
snapshot_t1 = []
elements = driver.find_elements(By.XPATH, "//body//*")
for el in elements:
    info = {
        'tag': el.tag_name,
        'id': el.get_attribute('id') or '',
        'class': el.get_attribute('class') or '',
        'text': el.text.strip(),
        'name': el.get_attribute('name') or '',
        'type': el.get_attribute('type') or '',
        'aria_label': el.get_attribute('aria-label') or '',
        'xpath': obter_xpath(driver, el)
    }
    data_attrs = driver.execute_script(GET_DATA_ATTRS_JS, el)
    info.update(data_attrs)
    snapshot_t1.append(info)
(DIRETORIO_DADOS / 't1.json').write_text(
    json.dumps(snapshot_t1, ensure_ascii=False, indent=2), encoding='utf-8'
)

# Fecha driver
driver.quit()

# 5) Gera diff e aplica ordem: Adicionado, Removido, Alterado, Movido
raw = gerar_diferencas(
    ler_snapshot(DIRETORIO_DADOS / 't0.json'),
    ler_snapshot(DIRETORIO_DADOS / 't1.json')
)
ordered = {
    'Adicionado': raw['adicionados'],
    'Removido': raw['removidos'],
    'Alterado': raw['alterados'],
    'Movido': raw['movidos'],
}
(DIRETORIO_DADOS / 'diff.json').write_text(
    json.dumps(ordered, ensure_ascii=False, indent=2), encoding='utf-8'
)

# 6) Resumo (apenas print)
print(
    f"Adicionado: {len(ordered['Adicionado'])}, "
    f"Removido: {len(ordered['Removido'])}, "
    f"Alterado: {len(ordered['Alterado'])}, "
    f"Movido: {len(ordered['Movido'])}"
)
