import os
from self_healing.core.extractor import extract_dom_elements, save_data_as_json

# URL do site a ser testado (ajuste conforme necessário)
website_url = "https://open.spotify.com/"

# Realiza a extração dos elementos do DOM
dados_extraidos = extract_dom_elements(website_url)

# Define o caminho para salvar o JSON na pasta "data" na raiz do projeto
current_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(current_dir, "data")
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "dados_extraidos.json")

save_data_as_json(dados_extraidos, output_file)
print(f"✅ Extração concluída. Dados salvos em: {output_file}")
