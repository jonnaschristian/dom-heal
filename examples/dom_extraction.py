import os
from self_healing.core.extractor import extract_dom_elements, save_data_as_json

website_url = "https://www.globalsqa.com/angularJs-protractor/BankingProject/#/login"
extracted_elements = extract_dom_elements(website_url)

# caminho absoluto baseado na localização atual do script
current_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(current_dir, "..", "data", "extracted_data.json")

save_data_as_json(extracted_elements, output_file)

print("✅ DOM extraction completed successfully.")
