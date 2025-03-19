import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def extract_dom_elements(url):
    """
    Abre a URL em modo headless, aguarda brevemente e rola parte da página para carregar
    conteúdo dinâmico. Em seguida, extrai aproximadamente 80% dos elementos do DOM (excluindo
    tags menos relevantes: script, style, meta, link e head) com seus atributos: tag, id, name e class.
    """
    # Configuração do WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.set_page_load_timeout(20)
    try:
        driver.get(url)
    except Exception as e:
        print("Erro ao carregar a página:", e)
    
    driver.implicitly_wait(2)
    time.sleep(1)
    
    # Rolagem parcial para acionar o carregamento de conteúdo dinâmico
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(1)
    
    # Extrai os elementos do DOM, excluindo tags que não interessam para testes
    xpath_query = "//body//*[not(self::script or self::style or self::meta or self::link or self::head)]"
    elementos = driver.find_elements(By.XPATH, xpath_query)
    resultados = []
    for e in elementos:
        resultados.append({
            "tag": e.tag_name,
            "id": e.get_attribute("id"),
            "name": e.get_attribute("name"),
            "class": e.get_attribute("class")
        })
    
    driver.quit()
    
    return {"elementos_relevantes": resultados}

def save_data_as_json(data, output_file):
    """Salva os dados extraídos em um arquivo JSON."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
