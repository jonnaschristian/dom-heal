"""
self_healing.core.extractor

Módulo de extração de elementos do DOM em modo "full" para manutenção de testes automatizados.

Coleta para cada elemento:
- tag: nome da tag HTML
- id: atributo id
- name: atributo name
- class: atributo class
- type: tipo de input (quando aplicável)
- text: texto interno do elemento
- aria_label: valor do atributo aria-label
- xpath: caminho absoluto no DOM
"""
import json
import time
from typing import List, Dict, Any

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def obter_xpath(elemento) -> str:
    """
    Gera o XPath absoluto de um elemento WebElement subindo na árvore DOM e contando irmãos.

    Args:
        elemento (WebElement): elemento cujo XPath será extraído.

    Returns:
        str: XPath absoluto.
    """
    partes: List[str] = []
    atual = elemento

    while True:
        pai = atual.find_element(By.XPATH, "..")
        irmaos = pai.find_elements(By.XPATH, f"./{atual.tag_name}")
        indice = irmaos.index(atual) + 1
        partes.insert(0, f"{atual.tag_name}[{indice}]")
        if pai.tag_name.lower() == 'html':
            break
        atual = pai

    return '/' + '/'.join(partes)


def extrair_elementos_dom(url: str) -> List[Dict[str, Any]]:
    """
    Extrai atributos de todos os elementos dentro de <body> em modo full.

    Realiza:
      1) Navegação headless ao URL
      2) Espera explícita de até 10s pelo document.readyState == "complete"
      3) Scroll até o fim para carregar conteúdo dinâmico
      4) Coleta de tag, id, name, class, type, text, aria_label e xpath

    Args:
        url (str): endereço da página.

    Returns:
        List[Dict[str, Any]]: lista de dicionários com informações dos elementos.
    """
    # Configuração do Chrome headless
    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument("--headless")
    opcoes.add_argument("--disable-gpu")
    opcoes.add_argument("--log-level=3")
    opcoes.add_experimental_option('excludeSwitches', ['enable-logging'])

    navegador = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opcoes
    )

    try:
        navegador.get(url)
        # Espera até que a página esteja completamente carregada (máx. 10s)
        WebDriverWait(navegador, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except WebDriverException as e:
        print(f"Erro ao acessar {url}: {e}")
        navegador.quit()
        return []

    # Aguarda carregamento de scripts dinâmicos e faz scroll
    navegador.implicitly_wait(2)
    time.sleep(1)
    navegador.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)

    # Captura todos os elementos de <body>, excluindo meta, script, style, link e head
    consulta = (
        "//body//*[not(self::script or self::style or self::meta "
        "or self::link or self::head)]"
    )
    elementos = navegador.find_elements(By.XPATH, consulta)

    resultados: List[Dict[str, Any]] = []
    for el in elementos:
        info: Dict[str, Any] = {
            "tag": el.tag_name,
            "id": el.get_attribute("id"),
            "name": el.get_attribute("name"),
            "class": el.get_attribute("class"),
            "type": el.get_attribute("type"),
            "text": el.text.strip(),
            "aria_label": el.get_attribute("aria-label"),
            "xpath": obter_xpath(el)
        }
        resultados.append(info)

    navegador.quit()
    return resultados


def salvar_como_json(dados: List[Dict[str, Any]], caminho_arquivo: str) -> None:
    """
    Salva a lista de elementos extraídos em arquivo JSON formatado.

    Args:
        dados (List[Dict[str, Any]]): lista de dicionários com informações.
        caminho_arquivo (str): caminho de destino do JSON.
    """
    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)
    print(f"✅ Dados salvos em: {caminho_arquivo}")
