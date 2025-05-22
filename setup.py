from setuptools import setup, find_packages

setup(
    name="dom-heal",                # nome do pacote no PyPI
    version="0.1.0",                # versão inicial
    description="Auto-recuperação de seletores DOM para testes web",
    author="Jonnas Christian Sousa de Paiva",
    author_email="jonnaschristian@gmail.com",
    url="https://github.com/jonnaschristian/dom-heal",
    packages=find_packages(),       # encontra automaticamente dom_heal/
    python_requires=">=3.7",
    install_requires=[              # dependências de runtime
        "rapidfuzz>=3.13.0",
        "selenium>=4.29.0",
        "webdriver-manager>=4.0.2",
    ],
    extras_require={                # dependências só para desenvolvimento
        "dev": [
            "pytest>=8.0.0",
            "python-dotenv>=1.0.0",
        ]
    },
    entry_points={
    "console_scripts": [
        "dom-heal = dom_heal.cli:main",
    ],
},

)
