"""
Módulo extractor: extrai snapshots do DOM via Selenium e fornece utilitários para cálculo de XPath e coleta de atributos.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Snippet JavaScript para cálculo do XPath absoluto
JS_OBTER_XPATH = """
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
JS_OBTER_DATA_ATTRS = """
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
    """
    Configura e retorna uma instância headless do Chrome para extração.
    """
    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument('--headless')
    opcoes.add_argument('--disable-gpu')
    opcoes.add_argument('--log-level=3')
    opcoes.add_experimental_option('excludeSwitches', ['enable-logging'])
    servico = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=servico, options=opcoes)

def carregar_pagina(driver: webdriver.Chrome, url: str, tempo_max: int = 10):
    """
    Carrega a página fornecida e aguarda até que o document.readyState seja 'complete'.

    Parâmetros:
        driver (webdriver.Chrome): Instância do Chrome a ser usada.
        url (str): URL da página a carregar.
        tempo_max (int, opcional): Tempo máximo de espera em segundos. Padrão: 10.
    """
    driver.get(url)
    WebDriverWait(driver, tempo_max).until(
        lambda drv: drv.execute_script("return document.readyState") == 'complete'
    )
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
    time.sleep(1)

def obter_elementos(driver: webdriver.Chrome) -> list:
    """
    Retorna todos os elementos WebElements presentes dentro de <body>.

    Parâmetros:
        driver (webdriver.Chrome): Driver Chrome ativo.

    Retorna:
        list: Lista de WebElements encontrados.
    """
    return driver.find_elements(By.XPATH, "//body//*")

def montar_info_elemento(driver: webdriver.Chrome, elemento) -> dict:
    """
    Extrai atributos principais e o XPath absoluto de um WebElement.

    Parâmetros:
        driver (webdriver.Chrome): Driver Chrome ativo.
        elemento (WebElement): Elemento do DOM a ser processado.

    Retorna:
        dict: Dicionário contendo tag, id, class, text, name, type, aria_label e xpath, além de data-attributes.
    """
    info = {
        'tag':        elemento.tag_name,
        'id':         elemento.get_attribute('id') or '',
        'class':      elemento.get_attribute('class') or '',
        'text':       elemento.text.strip(),
        'name':       elemento.get_attribute('name') or '',
        'type':       elemento.get_attribute('type') or '',
        'aria_label': elemento.get_attribute('aria-label') or '',
        'xpath':      driver.execute_script(JS_OBTER_XPATH, elemento),
    }
    dados = driver.execute_script(JS_OBTER_DATA_ATTRS, elemento)
    info.update(dados)
    return info

def obter_xpath(driver: webdriver.Chrome, elemento) -> str:
    """
    Calcula e retorna o XPath absoluto de um elemento via JavaScript.

    Parâmetros:
        driver (webdriver.Chrome): Driver Chrome ativo.
        elemento (WebElement): Elemento do DOM.

    Retorna:
        str: XPath absoluto.
    """
    return driver.execute_script(JS_OBTER_XPATH, elemento)

def extrair_snapshot(url: str, driver=None) -> list:
    """
    Extrai um snapshot do DOM de uma URL e retorna como lista de dicionários.

    Se driver for fornecido, reutiliza a instância; caso contrário, cria uma nova.

    Parâmetros:
        url (str): URL da página a extrair.
        driver (webdriver.Chrome, opcional): Instância existente de Chrome.

    Retorna:
        list: Lista de dicionários com informações dos elementos em <body>.
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
