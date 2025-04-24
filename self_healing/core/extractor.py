#!/usr/bin/env python3
# extractor.py
# Biblioteca de extração de elementos do DOM via Selenium
# Versão finalizada: funções encapsuladas e comentários gerais explicativos

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
    var name = attrs[i].name;
    if (name.startsWith('data-')) {
        var key = name.replace(/-/g, '_');
        result[key] = attrs[i].value || '';
    }
}
return result;
"""

def criar_driver() -> webdriver.Chrome:
    # Configura o Chrome em modo headless e retorna o driver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')                       # suprime logs do ChromeDriver
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # Baixa/atualiza automaticamente o ChromeDriver compatível
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def carregar_pagina(driver: webdriver.Chrome, url: str, timeout: int = 10):
    # Abre a página, espera readyState == 'complete' e faz scroll até o fim
    driver.get(url)
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == 'complete'
    )
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
    time.sleep(1)

def obter_xpath(driver: webdriver.Chrome, elemento) -> str:
    # Executa o snippet JS para obter o XPath absoluto
    return driver.execute_script(GET_XPATH_JS, elemento)

def extrair_elementos_dom(url: str) -> list:
    # Extrai todos os elementos do <body> e retorna lista de dicionários
    driver = criar_driver()
    try:
        carregar_pagina(driver, url)
        elementos = driver.find_elements(By.XPATH, "//body//*")
        resultados = []
        for el in elementos:
            info = {
                'tag':         el.tag_name,
                'id':          el.get_attribute('id') or '',
                'class':       el.get_attribute('class') or '',
                'text':        el.text.strip(),
                'name':        el.get_attribute('name') or '',
                'type':        el.get_attribute('type') or '',
                'aria_label':  el.get_attribute('aria-label') or '',
                'xpath':       obter_xpath(driver, el)
            }
            # Extrai todos os atributos data-* e adiciona ao dicionário
            data_attrs = driver.execute_script(GET_DATA_ATTRS_JS, el)
            info.update(data_attrs)
            resultados.append(info)
        return resultados
    finally:
        driver.quit()
