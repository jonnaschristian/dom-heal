"""
Utils
=====

Funções utilitárias para padronização dos seletores utilizados no mecanismo de self-healing.

Inclui:
- Normalização de entrada para listas de objetos padronizados, compatível com diferentes formatos de frameworks e usuários finais.
"""

def normalizar_elementos(data):
    """
    Normaliza os seletores fornecidos, aceitando tanto listas de objetos quanto dicionários
    no formato {nome: seletor}. Sempre converte para lista de objetos com 'nome' e 'selector'.

    Args:
        data: Lista de objetos (ex: [{'nome': 'campo', 'selector': '#id'}]) ou dicionário {nome: seletor}.

    Returns:
        list: Lista de dicionários uniformizada, ex: [{'nome': 'campo', 'selector': '#id'}]

    Raises:
        ValueError: Se o formato de dados não for suportado.

    Example:
        >>> normalizar_elementos({'inputEmail': '#email', 'btnEnviar': '#submit'})
        [{'nome': 'inputEmail', 'selector': '#email'}, {'nome': 'btnEnviar', 'selector': '#submit'}]
    """
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [{"nome": nome, "selector": seletor} for nome, seletor in data.items()]
    else:
        raise ValueError("Formato de dados de seletores inválido.")
