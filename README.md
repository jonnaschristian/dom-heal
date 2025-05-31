# 🧬 DOM-Heal: Biblioteca Genérica de Self-Healing para Testes Automatizados de Interfaces Web

[![PyPI version](https://badge.fury.io/py/dom-heal.svg)](https://pypi.org/project/dom-heal/)

DOM-Heal é uma biblioteca Python open-source que automatiza a detecção e correção de seletores quebrados em testes web, permitindo auto-recuperação (self-healing) de scripts de automação frente a mudanças no DOM.

Desenvolvido como Trabalho de Conclusão de Curso em Ciência da Computação (UECE, 2025).

---

## ✨ Por que usar DOM-Heal?

- Reduz falhas em testes automatizados causadas por mudanças de ID, nome, classe ou estrutura no DOM.
- Mantenha seus testes E2E de quaisquer frameworks, sem editar todos os seletores manualmente.
- Heurística robusta baseada em similaridade, palavras-chave e contexto, funcionando em QUALQUER sistema web.

---

## 🚀 Instalação

Requer Python 3.7+.

```bash
pip install dom-heal
```
---

## 📖 Como usar

### 1. Prepare seu arquivo JSON de seletores

Você precisa usar um arquivo `.json` com os seletores lógicos dos elementos do seu teste. Exemplo:

```json
{
  "inputEmail": "#email",
  "btnEnviar": "#submit",
  "mensagemSucesso": ".alert-success"
}
```

### 2. Execute o self-healing pelo CLI

Com a biblioteca instalada, rode o comando apontando para o arquivo de seletores e a URL do sistema que deseja analisar:

```bash
dom-heal rodar --json caminho/para/seletores.json --url https://seusistema.com/sua_pagina
```