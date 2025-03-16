import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def extract_dom_elements(url):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")

    driver_service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=driver_service, options=chrome_options)

    browser.get(url)
    time.sleep(5)  # aguarda carregamento completo

    # Títulos principais da página
    headings = [element.text.strip() for element in browser.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //strong") if element.text.strip()]

    # Links e botões que se comportam como links
    clickable_elements = browser.find_elements(By.XPATH, "//a[@href] | //button[contains(@onclick, 'location.href') or @ng-click]")
    links_and_buttons = []
    for element in clickable_elements:
        text = element.text.strip()
        if text:
            element_type = "Link" if element.tag_name == "a" else "Button as link"
            link_url = element.get_attribute("href") if element.tag_name == "a" else None
            links_and_buttons.append({"type": element_type, "text": text, "url": link_url})

    # Botões comuns
    standard_buttons = [btn.text.strip() for btn in browser.find_elements(By.XPATH, "//button[not(contains(@onclick, 'location.href')) and not(@ng-click)]") if btn.text.strip()]

    # Imagens encontradas
    images = [{"src": img.get_attribute("src"), "alt": img.get_attribute("alt")} for img in browser.find_elements(By.TAG_NAME, "img") if img.get_attribute("src")]

    # Campos de entrada (inputs)
    input_fields = [{"type": field.tag_name, "name": field.get_attribute("name")} for field in browser.find_elements(By.XPATH, "//input | //textarea | //select") if field.get_attribute("name")]

    # Tabelas
    tables = [{"table_index": idx, "row_count": len(table.find_elements(By.TAG_NAME, "tr"))} for idx, table in enumerate(browser.find_elements(By.TAG_NAME, "table"))]

    # Classes de div e span
    div_classes = [div.get_attribute("class") for div in browser.find_elements(By.TAG_NAME, "div") if div.get_attribute("class")]
    span_classes = [span.get_attribute("class") for span in browser.find_elements(By.TAG_NAME, "span") if span.get_attribute("class")]

    # IDs dos elementos
    elements_with_id = [{"tag": el.tag_name, "id": el.get_attribute("id")} for el in browser.find_elements(By.XPATH, "//*[@id]")]

    browser.quit()

    extracted_data = {
        "headings": headings,
        "links_and_buttons": links_and_buttons,
        "standard_buttons": standard_buttons,
        "images": images,
        "input_fields": input_fields,
        "tables": tables,
        "div_classes": div_classes,
        "span_classes": span_classes,
        "elements_with_id": elements_with_id
    }

    return extracted_data


def save_data_as_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
