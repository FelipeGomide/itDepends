import click
import re
import logging
import sys
from itdepends.analyzer import analyze_repository

@click.command()
@click.argument('repository_name', metavar="<repository_name>")
@click.option('--verbose', '-v', is_flag=True, help="Habilita logs detalhados (DEBUG)")
def cli(repository_name, verbose):
    """
    \b
    Análise forense de dependências de repositórios Git.
    <repository_name>: Caminho local ou 'owner/repo' no GitHub.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    logger = logging.getLogger("itdepends.cli")
    logger.info("itDepends initialized.")

    if not validate_repo_name(repository_name):
        raise click.UsageError(f"Nome de repositório inválido: {repository_name}")

    try:
        df = analyze_repository(repository_name)
        if not df.empty:
            click.echo(f"Análise concluída. {len(df)} registros de mudança encontrados.")
            # salvar o CSV: df.to_csv("output.csv")
        else:
            click.echo("Nenhuma alteração de dependência encontrada.")
            
    except Exception as e:
        logger.critical(f"Erro fatal na execução: {e}")
        sys.exit(1)

def validate_repo_name(name):
    # Aceita caminhos locais (./projeto) ou github (user/repo)
    if name.startswith(".") or "/" in name or "\\" in name:
        return True
    return False

if __name__ == '__main__':
    cli()