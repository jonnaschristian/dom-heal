
# 🧠 Self-Healing Test Automation (DOM-based)

Este projeto é uma prova de conceito de um mecanismo *self-healing* para testes automatizados, com foco em páginas web com DOM dinâmico. O objetivo é extrair elementos da estrutura HTML, comparar mudanças entre versões e permitir readequação automática de seletores.

---

## 🔧 Requisitos

- Python 3.7+
- Google Chrome instalado
- pip (para instalar bibliotecas)

---

## 📁 Estrutura do Projeto

```
.
├── data/                      # Onde os arquivos JSON extraídos são salvos
├── dom_test_env/              # Página com DOM que muda dinamicamente
├── self_healing/  # Lógica de extração de DOM com Selenium
└── run_traduzido.py           # Script principal de extração
```

---

## 🚀 Como executar

### 1. Servir a página HTML localmente

No terminal, dentro da pasta `dom_test_env`:

```bash
python -m http.server 8000
```

Acesse no navegador:

```
http://localhost:8000/
```

Isso abrirá a página `dynamic_test.html`, onde os elementos HTML mudam dinamicamente a cada 20 segundos.

---

### 2. Executar o script Python para extrair elementos do DOM

Antes, instale os pacotes necessários:

```bash
pip install selenium webdriver-manager
```

Em seguida, execute o script:

```bash
python run.py
```

Isso irá:
- Acessar a página
- Esperar ela carregar
- Extrair os elementos do DOM
- Salvar em: `./data/elementos_extraidos.json`


---

## 📄 Licença

Este projeto foi desenvolvido como parte de um TCC de Ciência da Computação com fins educacionais e de pesquisa.
