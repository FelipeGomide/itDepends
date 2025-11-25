# Mineração de Repositórios de Software
Trabalho prático da disciplina Engenharia de Software II.

## Objetivo 

O projeto consiste no desenvolvimento de uma ferramenta de linha de comando em Python capaz de analisar as dependências de um projeto a partir de arquivos como requirements.txt ou poetry.lock.

A ferramenta consulta a API do PyPI para verificar versões vulneráveis, dependências desatualizadas ou repositórios que foram descontinuados. Além disso, avalia o histórico de atualizações, medindo a frequência de releases e o tempo médio de adoção de novas versões pelo projeto.

Os resultados são apresentados em um relatório HTML, contendo gráficos e tabelas interativas que destacam riscos de segurança, obsolescência e padrões de manutenção das dependências.

- Origem dos dados: GitHub

- Artefatos analisados: arquivos de dependências e configuração do projeto, histórico de dependências.

- Apresentação de resultados: relatório HTML, contendo gráficos e tabelas interativas que destacam métricas de dependências.

- Tecnologias utilizadas: pydriller, PyPI API, GitHub API, click

## Membros

- Cecilia Junqueira Vieira Machado Pereira

- Felipe Lopes Gomide

- Lucas Junqueira Carvalhido

- Lucca Alvarenga de Magalhaes Pinto

## Como instalar a ferramenta.

1. Faça o clone do repositório
2. Na pasta raiz, execute:
  `python -m pip install .`

obs: Recomendamos que faça isso num ambiente virtual Python

## Como utilizar a ferramenta.

Para executar a ferramenta, use o comando:

`python -m itdepends <owner/repo>`

A ferramenta também aceita outros parâmetros opcionais:

```
Opções:
  --path TEXT                Caminho para a pasta do repositório clonado anteriormente
  --since_months INTEGER     Número de meses para buscar por commits
  --inactive_months INTEGER  Quantidade de meses sem commits para considerar um repositório inativo
```

Obs: Para a execução da análise de depreciação, são realizadas consultas na API do GitHub, que possui um rate limit considerado baixo (60 por hora).
Para extender esse limite e evitar erros, gere um TOKEN de consulta da API do GitHub e salve como uma variável de ambiente com o comando:
`export GITHUB_TOKEN=<seu_token_gerado>`


Os resultados são salvos na pasta `results/owner_repo/`
São salvas duas planilhas `.csv`, deprecation e history,
 bem como um relatório completo dos dados extraídos, em `report.html`.

## Como executar os testes localmente.

Execute utilizando a biblioteca Pytest.

`python3 pytest`
