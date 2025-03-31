
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def extrair_elementos_dom(url):
    """
    Abre a URL em modo headless, aguarda brevemente e rola parte da página para carregar
    conteúdo dinâmico. Em seguida, extrai aproximadamente 80% dos elementos do DOM (excluindo
    tags menos relevantes: script, style, meta, link e head) com seus atributos: tag, id, name e class.
    """
    # Configuração do WebDriver
    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument("--headless")
    opcoes.add_argument("--disable-gpu")
    opcoes.add_argument("--log-level=3")
    navegador = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opcoes)

    navegador.set_page_load_timeout(20)
    try:
        navegador.get(url)
    except Exception as erro:
        print("Erro ao carregar a página:", erro)

    navegador.implicitly_wait(2)
    time.sleep(1)

    # Rolagem parcial para acionar o carregamento de conteúdo dinâmico
    navegador.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(1)

    # Extrai os elementos do DOM, excluindo tags que não interessam para testes
    consulta_xpath = "//body//*[not(self::script or self::style or self::meta or self::link or self::head)]"
    elementos = navegador.find_elements(By.XPATH, consulta_xpath)
    resultado = []
    for elemento in elementos:
        resultado.append({
            "tag": elemento.tag_name,
            "id": elemento.get_attribute("id"),
            "name": elemento.get_attribute("name"),
            "class": elemento.get_attribute("class")
        })

    navegador.quit()

    return {"elementos_relevantes": resultado}

def salvar_como_json(dados, caminho_arquivo):
    """Salva os dados extraídos em um arquivo JSON."""
    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)
