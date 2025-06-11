"""
Extractor
=========

Módulo responsável por extrair todos os elementos do DOM de uma página utilizando Selenium WebDriver.
Retorna uma lista de dicionários contendo os principais atributos de cada elemento, prontos para uso no mecanismo de self-healing.

Principais funcionalidades:
- Navegação e carregamento headless do DOM
- Extração de todos os elementos do <body> com atributos importantes (id, class, name, text, type, aria-label, placeholder, xpath, data-*)

Ideal para rodar como backend para engines de self-healing.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
    Configura e retorna uma instância headless do Chrome para extração de elementos.

    Returns:
        webdriver.Chrome: Instância configurada para execução headless.
    """
    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument('--headless')  # Comente para debug local
    opcoes.add_argument('--disable-gpu')
    opcoes.add_argument('--log-level=3')
    opcoes.add_experimental_option('excludeSwitches', ['enable-logging'])
    servico = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=servico, options=opcoes)

def carregar_pagina(driver: webdriver.Chrome, url: str, tempo_max: int = 10, wait_after_load: float = 1):
    """
    Carrega a página informada e aguarda o carregamento completo do DOM.

    Args:
        driver: Instância do Chrome.
        url: URL da página a ser carregada.
        tempo_max: Tempo máximo de espera em segundos (default=10).
        wait_after_load: Espera adicional após o carregamento (default=1s).
    """
    driver.get(url)
    WebDriverWait(driver, tempo_max).until(
        lambda drv: drv.execute_script("return document.readyState") == 'complete'
    )
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
    if wait_after_load > 0:
        time.sleep(wait_after_load)

def obter_elementos(driver: webdriver.Chrome) -> list:
    """
    Retorna todos os elementos WebElements presentes em <body>.

    Args:
        driver: Instância do Chrome.

    Returns:
        list: Lista de WebElements.
    """
    return driver.find_elements(By.XPATH, "//body//*")

def montar_info_elemento(driver: webdriver.Chrome, elemento) -> dict:
    """
    Extrai os principais atributos de um WebElement.

    Args:
        driver: Instância do Chrome.
        elemento: Elemento do DOM.

    Returns:
        dict: Dados do elemento (tag, id, class, text, name, type, aria_label, placeholder, xpath e data-*).
    """
    info = {
        'tag':        elemento.tag_name,
        'id':         elemento.get_attribute('id') or '',
        'class':      elemento.get_attribute('class') or '',
        'text':       elemento.text.strip(),
        'name':       elemento.get_attribute('name') or '',
        'type':       elemento.get_attribute('type') or '',
        'aria_label': elemento.get_attribute('aria-label') or '',
        'placeholder': elemento.get_attribute('placeholder') or '',
        'xpath':      driver.execute_script(JS_OBTER_XPATH, elemento),
    }
    dados = driver.execute_script(JS_OBTER_DATA_ATTRS, elemento)
    info.update(dados)
    return info

def obter_xpath(driver: webdriver.Chrome, elemento) -> str:
    """
    Calcula o XPath absoluto do elemento via JavaScript.

    Args:
        driver: Instância do Chrome.
        elemento: Elemento do DOM.

    Returns:
        str: XPath absoluto do elemento.
    """
    return driver.execute_script(JS_OBTER_XPATH, elemento)

def extrair_dom(url: str, driver=None) -> list:
    """
    Extrai o DOM da URL informada e retorna uma lista de dicionários de elementos.

    Args:
        url (str): URL da página para extração.
        driver: Instância opcional do Chrome WebDriver.

    Returns:
        list: Lista de dicionários com atributos relevantes de cada elemento.
    """
    possui_driver = driver is not None
    drv = driver or criar_driver()
    try:
        carregar_pagina(drv, url)
        elementos = obter_elementos(drv)
        info_list = []
        for el in elementos:
            info = montar_info_elemento(drv, el)
            info_list.append(info)
        return info_list
    finally:
        if not possui_driver:
            drv.quit()
