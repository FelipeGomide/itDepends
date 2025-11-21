import click
import re

from .application import run

DEFAULT_MAX_MONTHS = 12

@click.command()
@click.argument('repository_name', metavar = "<repository_name>")
@click.option('--max_months',
              help= 'Number of months without commits to consider a repository inactive',
              type=int,
              default= DEFAULT_MAX_MONTHS)
def cli(repository_name, max_months):
    """
    \b
    <repository_name>: Target repository on GitHub.
        Format: owner/repo
    """
    click.echo(click.style("itDepends initialized.", fg="green"))

    valid = parse_repo_name(repository_name)

    if not valid:
        raise click.UsageError(f"Invalid repository name: {repository_name}")

    run(repository_name, max_months)
    
    return

def parse_repo_name(repository_name):
    regex_match = re.match(r'^[a-zA-Z0-9-]+/[a-zA-Z0-9._-]+(?:/[a-zA-Z0-9._/-]+)*$', repository_name)

    if regex_match:
        return True
    
    return False

if __name__ == '__main__':
    cli()