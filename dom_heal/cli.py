"""
CLI
===

Interface de linha de comando (CLI) para execução do mecanismo de self-healing da biblioteca DOM-Heal.

Após instalar via pip, basta rodar:
    dom-heal rodar --json <CAMINHO> --url <URL>

Funcionalidades:
- Executa o self-healing a partir de um JSON de seletores e URL informada
- Exibe logs detalhados e informações sobre o projeto
"""

import typer
from dom_heal.engine import self_heal

app = typer.Typer(help="Executa o self-healing externo da biblioteca dom-heal.")

@app.command()
def rodar(
    json: str = typer.Option(..., "--json", "-j", help="Caminho para o arquivo JSON de seletores."),
    url: str = typer.Option(..., "--url", "-u", help="URL da página a ser analisada."),
):
    """
    Executa o mecanismo de self-healing, atualizando o JSON de seletores
    e gerando o relatório de alterações.

    Args:
        json (str): Caminho para o arquivo de seletores (.json).
        url (str): URL da página alvo.

    Example:
        dom-heal rodar --json ./meus_seletores.json --url https://site.com/pagina
    """
    try:
        resultado = self_heal(json, url)
        typer.secho("✅ Self-healing executado com sucesso!", fg=typer.colors.GREEN)
        typer.echo(f"📄 Log de alterações: {resultado['log_detalhado']}")
        typer.echo(f"🗃️ JSON atualizado: {resultado['json_atualizado']}")
    except Exception as e:
        typer.secho(f"❌ Erro ao executar self-healing: {e}", fg=typer.colors.RED)

@app.command()
def sobre():
    """
    Exibe informações sobre a biblioteca DOM-Heal e autoria.

    Example:
        dom-heal sobre
    """
    typer.echo("DOM-Heal: Biblioteca de Self-Healing para Testes Automatizados - Projeto de TCC (Jonnas Christian, UECE, 2025)")

def main():
    """
    Função principal para permitir execução direta do CLI.
    """
    app()

if __name__ == "__main__":
    main()
