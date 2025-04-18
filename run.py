
import os
from self_healing.core.extractor import extrair_elementos_dom, salvar_como_json

# URL do site a ser testado (ajuste conforme necessário)
url_site = "http://localhost:8000/dynamic_test.html"

# Realiza a extração dos elementos do DOM
elementos_extraidos = extrair_elementos_dom(url_site)

# Define o caminho para salvar o JSON na pasta "data" na raiz do projeto
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_saida = os.path.join(diretorio_atual, "data")
os.makedirs(caminho_saida, exist_ok=True)
arquivo_saida = os.path.join(caminho_saida, "elementos_extraidos.json")

salvar_como_json(elementos_extraidos, arquivo_saida)
