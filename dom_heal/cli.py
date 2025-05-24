"""
Módulo CLI: executa o self-healing via terminal de forma simples e clara.
Após instalar a biblioteca, basta rodar: dom-heal --json seletores.json --url https://site.com
"""

import typer
from pathlib import Path
from dom_heal.engine import self_heal

app = typer.Typer(help="Executa o self-healing externo da biblioteca dom-heal.")

@app.command()
def rodar(
    json: Path = typer.Option(..., "--json", "-j", help="Caminho para o arquivo JSON de seletores."),
    url: str = typer.Option(..., "--url", "-u", help="URL da página a ser analisada."),
):
    """
    Executa o self-healing: atualiza o JSON de seletores e gera relatório de alterações.
    """
    resultado = self_heal(str(json), url)
    typer.echo("\n=== Resultado do Self-Healing ===")
    for chave, valor in resultado.items():
        typer.echo(f"{chave}: {valor}")

def main():
    app()

if __name__ == "__main__":
    main()
