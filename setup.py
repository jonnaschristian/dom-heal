from setuptools import setup, find_packages

setup(
    name='self_healing',
    version='0.1.0',
    description='Motor de Self-Healing para testes funcionais automatizados',
    author='Jonnas Christian Sousa de Paiva',
    packages=find_packages(),
    install_requires=[
        'rapidfuzz>=3.13.0',        # fuzzy matching de alta performance
        'selenium>=4.29.0',         # captura de snapshots via Selenium
        'webdriver-manager>=4.0.2'  # gerencia drivers do navegador
    ],
    entry_points={
        'console_scripts': [
            'extrair-dom = self_healing.core.extractor:extrair_elementos_dom'
        ]
    },
)
