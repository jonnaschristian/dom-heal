from setuptools import setup, find_packages

setup(
    name='self_healing',
    version='0.1.0',
    description='Motor de Self-Healing para testes funcionais automatizados',
    author='Jonnas Christian Sousa de Paiva',
    packages=find_packages(),
    install_requires=[
        'selenium',
        'webdriver-manager'
    ],
    entry_points={
        'console_scripts': [
            'extrair-dom = self_healing.core.extractor:extrair_elementos_dom'
        ]
    }
)
