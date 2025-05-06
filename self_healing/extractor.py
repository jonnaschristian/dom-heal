# Biblioteca de extração de elementos do DOM via Selenium: coleta atributos e XPath de cada nó

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Snippet JavaScript para cálculo do XPath absoluto
GET_XPATH_JS = """
function absoluteXPath(el){
    var segs = [];
    for (; el && el.nodeType==1; el=el.parentNode){
        var i=1, sib=el.previousSibling;
        for (; sib; sib= sib.previousSibling)
            if (sib.nodeType==1 && sib.nodeName==el.nodeName) i++;
        segs.unshift(el.nodeName.toLowerCase() + '[' + i + ']');
    }
    return '/' + segs.join('/');
}
return absoluteXPath(arguments[0]);
"""

# Snippet JavaScript para extrair atributos data-* dinamicamente
GET_DATA_ATTRS_JS = """
var attrs = arguments[0].attributes;
var result = {};
for (var i = 0; i < attrs.length; i++) {
    var nome = attrs[i].name;
    if (nome.startsWith('data-')) {
        var chave = nome.replace(/-/g, '_');
        result[chave] = attrs[i].value || '';
    }
}
return result;
"""


def criar_driver() -> webdriver.Chrome:
    """Configura e retorna instância headless do Chrome"""
    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument('--headless')
    opcoes.add_argument('--disable-gpu')
    opcoes.add_argument('--log-level=3')
    opcoes.add_experimental_option('excludeSwitches', ['enable-logging'])
    servico = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=servico, options=opcoes)


def carregar_pagina(driver: webdriver.Chrome, url: str, timeout: int = 10):
    """Carrega página e aguarda readyState == 'complete'"""
    driver.get(url)
    WebDriverWait(driver, timeout).until(
        lambda drv: drv.execute_script("return document.readyState") == 'complete'
    )
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
    time.sleep(1)


def obter_elementos(driver: webdriver.Chrome) -> list:
    """Retorna lista de WebElements do <body>"""
    return driver.find_elements(By.XPATH, "//body//*")


def montar_info_elemento(driver: webdriver.Chrome, elemento) -> dict:
    """Monta dict com atributos e XPath de um WebElement"""
    info = {
        'tag':        elemento.tag_name,
        'id':         elemento.get_attribute('id') or '',
        'class':      elemento.get_attribute('class') or '',
        'text':       elemento.text.strip(),
        'name':       elemento.get_attribute('name') or '',
        'type':       elemento.get_attribute('type') or '',
        'aria_label': elemento.get_attribute('aria-label') or '',
        'xpath':      driver.execute_script(GET_XPATH_JS, elemento),
    }
    dados = driver.execute_script(GET_DATA_ATTRS_JS, elemento)
    info.update(dados)
    return info


def obter_xpath(driver: webdriver.Chrome, elemento) -> str:
    """Retorna o XPath absoluto de um elemento via JS"""
    return driver.execute_script(GET_XPATH_JS, elemento)


def extrair_snapshot(url: str, driver=None) -> list:
    """
    Extrai snapshot do DOM de uma URL.
    Se driver for fornecido, reutiliza; caso contrário, instancia um novo.
    Retorna lista de dicts com info de cada elemento em <body>.
    """
    possui_driver = driver is not None
    drv = driver or criar_driver()
    try:
        carregar_pagina(drv, url)
        elementos = obter_elementos(drv)
        return [montar_info_elemento(drv, el) for el in elementos]
    finally:
        if not possui_driver:
            drv.quit()
