
# DOM-Heal

**Auto-recuperação de seletores DOM para testes web automatizados**

![PyPI - Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-Experimental-yellow)

DOM-Heal é uma biblioteca de _self-healing_ para automação de testes web. Ela identifica seletores quebrados no DOM, faz o ajuste inteligente e atualiza automaticamente seu arquivo de elementos, minimizando falhas causadas por mudanças no front-end. Compatível com qualquer framework de teste (Cypress, Selenium, Robot Framework, Playwright, etc).

---

## ✨ Principais Funcionalidades

- **Self-healing de seletores:** Ajusta e recupera seletores (`id`, `name`, `class`, `xpath`) automaticamente usando algoritmos fuzzy.
- **Matching inteligente:** Aplica boosts e estratégias avançadas para encontrar o elemento mais parecido possível.
- **Log detalhado:** Gera um arquivo extra (`ElementosAlterados.json`) mostrando todas as alterações feitas.
- **Atualização automática:** O JSON original de seletores é atualizado de acordo com o DOM atual da página.
- **Independente de framework:** Funciona para qualquer ferramenta de automação que utilize JSON para armazenamento de elementos.
- **Uso por página:** Cada execução é feita para uma página específica, garantindo máxima precisão.

---

## 🚀 Instalação

> **Pré-requisitos:** Python 3.7+ e [Google Chrome](https://www.google.com/chrome/)

```bash
pip install dom-heal
```

---

## ⚡ Como Usar

### 1. Crie seu arquivo de seletores (um JSON por página!)

Recomenda-se criar um arquivo JSON para cada página que deseja validar/atualizar.  
**Exemplo (`formulario.json`):**

```json
{
  "inputEmail": "#email",
  "btnEnviar": "#enviar",
  "menuContato": "#menu-contato"
}
```

---

### 2. Execute o self-healing para a página desejada

```bash
dom-heal rodar --json ./formulario.json --url https://seusite.com/formulario
```

- **Importante:**  
  - O arquivo JSON passado será **atualizado** automaticamente com os novos seletores encontrados.
  - Será gerado, na mesma pasta, um arquivo `ElementosAlterados.json` com um relatório detalhado das alterações.

#### Exemplo de saída:

```
✅ Self-healing executado com sucesso!
📄 Log de alterações: ./ElementosAlterados.json
🗃️ JSON atualizado: ./home_selectors.json
```

---

### 3. Consulte o log de alterações

O arquivo `ElementosAlterados.json` mostra detalhadamente:
- Qual elemento foi alterado
- Seletor antigo vs novo seletor sugerido
- Pontuação de similaridade
- Motivo
- boost (se houve boost)

**Exemplo:**
```json
{
  "alterados": [
    {
      "nome": "inputEmail",
      "selector_antigo": "#email",
      "novo_seletor": "#input-email",
      "score": 0.88,
      "motivo": "id",
      "boost": true
    }
  ]
}
```

---

### 4. Integração com qualquer framework de teste

O arquivo de seletores (JSON) pode ser consumido diretamente pelos seus testes automatizados.  
Basta garantir que cada framework (Cypress, Selenium, Robot, Playwright etc.) leia os seletores do JSON atualizado pelo DOM-Heal.

**Exemplo prático:**  
Seu teste carrega o JSON e usa os seletores para interagir com a página — após o self-healing, não precisa alterar o teste, apenas garantir que os seletores estejam sempre atualizados.

---

## 🛠️ Fluxo Completo

1. **Execute o self-healing para a página desejada.**
2. **Valide o JSON atualizado nos seus testes.**
3. **Verifique o log `ElementosAlterados.json` para saber o que mudou.**
4. **Se necessário, ajuste manualmente seletores muito específicos (casos raros).**
5. **Repita o processo para cada página relevante do seu sistema.**

---

## 💡 Dicas e Boas Práticas

- Sempre utilize **um JSON por página** para facilitar a manutenção.
- Versione seus arquivos de seletores (use Git).
- Valide os seletores após rodar o self-healing, principalmente se seu front-end sofreu grandes mudanças estruturais.
- O log detalhado pode ser usado como documentação da evolução dos seletores do seu sistema.
- O mecanismo não depende do framework de teste: funciona com qualquer solução que use arquivos/dicionários de seletores.
- Chrome deve estar instalado localmente para o funcionamento correto do Selenium headless.
- O processo não interfere no código dos seus testes — apenas atualiza o arquivo de seletores consumido por eles.

---

## 🧑‍💻 Estrutura do Projeto

```
dom_heal/
├── cli.py         # Interface de linha de comando
├── engine.py      # Orquestra o ciclo completo de self-healing
├── extractor.py   # Extrai todos os elementos do DOM usando Selenium
├── comparator.py  # Matching fuzzy e seleção do melhor elemento
├── healing.py     # Atualiza o JSON de seletores
└── utils.py       # Funções utilitárias e normalização
```

---


## 👨‍🏫 Autor

Projeto desenvolvido por **Jonnas Christian Sousa de Paiva**  
Contato: [jonnaschristian@gmail.com](mailto:jonnaschristian@gmail.com)

---

## 📄 Licença

MIT — sinta-se livre para usar, estudar e contribuir!

---

**Contribua, reporte bugs e mande sugestões no [GitHub](https://github.com/jonnaschristian/dom-heal)**

---
