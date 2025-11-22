import pandas as pd
import plotly.express as px
from jinja2 import Template
from typing import Optional
from pathlib import Path


def get_template_padrao() -> str:
    """
    Retorna o template HTML padrão para o relatório.

    Pode ser usado como base para criar templates customizados.
    """
    return """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Relatório de Dependências - {{ nome_projeto }}</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">

    <style>
        :root {
            --bg-main: #020617;
            --bg-card: #020617;
            --bg-page: #020617;
            --border-subtle: #1f2937;
            --text-primary: #e5e7eb;
            --text-secondary: #9ca3af;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.15);
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 24px;
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
            background: radial-gradient(circle at top left, #0f172a 0, #020617 45%, #0b1120 100%);
            color: var(--text-primary);
        }

        .page-header {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 32px;
            padding: 24px;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 16px;
            border: 1px solid var(--border-subtle);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }

        .project-name {
            margin: 0;
            font-size: 36px;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px var(--accent-glow);
            line-height: 1.2;
        }

        .report-title {
            margin: 0;
            font-size: 16px;
            font-weight: 500;
            color: var(--text-secondary);
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .header-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 8px;
            flex-wrap: wrap;
            gap: 12px;
        }

        .subtitle {
            margin: 0;
            color: var(--text-secondary);
            font-size: 13px;
        }

        .tag {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 11px;
            background: rgba(148, 163, 184, 0.15);
            border: 1px solid rgba(148, 163, 184, 0.3);
        }

        .tag-dot {
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: #22c55e;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .kpi-row {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 22px;
        }

        .kpi-card {
            background: rgba(15, 23, 42, 0.9);
            border-radius: 12px;
            padding: 10px 14px;
            border: 1px solid var(--border-subtle);
            min-width: 170px;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.8);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 22px 55px rgba(15, 23, 42, 0.9);
        }

        .kpi-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }

        .kpi-value {
            font-size: 18px;
            font-weight: 600;
        }

        .kpi-extra {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 2px;
        }

        /* Layout em coluna única */
        .dashboard {
            display: grid;
            grid-template-columns: 1fr;
            gap: 22px;
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
        }

        .plot-container {
            background: rgba(15, 23, 42, 0.92);
            border-radius: 16px;
            padding: 16px 18px 14px 18px;
            box-shadow: 0 22px 55px rgba(15, 23, 42, 0.85);
            border: 1px solid var(--border-subtle);
            backdrop-filter: blur(10px);
            transition: box-shadow 0.3s;

            /* CRÍTICO para evitar overflow */
            width: 100%;
            max-width: 100%;
            min-width: 0;
            overflow: hidden;

            /* Garantir que o conteúdo interno se adapte */
            display: flex;
            flex-direction: column;
        }

        .plot-container:hover {
            box-shadow: 0 24px 65px rgba(15, 23, 42, 0.95);
        }

        .plot-container h2 {
            margin-top: 0;
            margin-bottom: 6px;
            font-size: 17px;
            flex-shrink: 0;
        }

        .plot-description {
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 10px;
            flex-shrink: 0;
        }

        /* Forçar gráficos Plotly a respeitarem o container */
        .plot-container .js-plotly-plot,
        .plot-container .plotly,
        .plot-container .plotly-graph-div {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
        }

        .plot-container .js-plotly-plot .plot-container,
        .plot-container svg.main-svg {
            max-width: 100% !important;
            width: 100% !important;
        }

        .dataframe-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-top: 4px;
            overflow-x: auto;
        }

        .dataframe-table th,
        .dataframe-table td {
            border-bottom: 1px solid #111827;
            padding: 6px 8px;
            text-align: left;
            vertical-align: top;
        }

        .dataframe-table th {
            font-weight: 500;
            color: var(--text-secondary);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .dataframe-table tr:hover {
            background: rgba(15, 23, 42, 0.9);
        }

        footer {
            margin-top: 32px;
            padding: 16px;
            font-size: 11px;
            color: var(--text-secondary);
            text-align: center;
            border-top: 1px solid var(--border-subtle);
        }

        @media (max-width: 640px) {
            body {
                padding: 16px;
            }

            .page-header {
                padding: 16px;
            }

            .project-name {
                font-size: 28px;
            }

            .header-info {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    </style>
</head>
<body>
    <header class="page-header">
        <h2 class="report-title">Relatório de Dependências</h2>
        <h1 class="project-name">{{ nome_projeto }}</h1>
        <div class="header-info">
            <p class="subtitle">Evolução das versões por commit</p>
            <div class="tag">
                <span class="tag-dot"></span>
                <span>Última atualização em {{ ultima_data }}</span>
            </div>
        </div>
    </header>

    <section class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">Dependências analisadas</div>
            <div class="kpi-value">{{ total_dependencias }}</div>
        </div>

        <div class="kpi-card">
            <div class="kpi-label">Commits analisados</div>
            <div class="kpi-value">{{ total_commits }}</div>
            <div class="kpi-extra">Commits com pelo menos uma dependência registrada</div>
        </div>
    </section>

    <section class="dashboard">
        <article class="plot-container">
            <h2>Linha do tempo das versões</h2>
            <p class="plot-description">
                Cada ponto representa a versão de uma dependência em um commit específico.
                Use o zoom e o hover para investigar mudanças pontuais.
            </p>
            {{ plot_timeline|safe }}
        </article>

        <article class="plot-container">
            <h2>Quantidade de versões por dependência</h2>
            <p class="plot-description">
                Histograma de quantas versões diferentes foram observadas para cada biblioteca.
            </p>
            {{ plot_upgrades|safe }}
        </article>

        <article class="plot-container">
            <h2>Resumo por dependência</h2>
            <p class="plot-description">
                Para cada dependência, veja a primeira e última versão observada, período coberto e
                quantidade de commits.
            </p>
            {{ tabela_resumo|safe }}
        </article>
    </section>

    <footer>
        Relatório gerado automaticamente
    </footer>
</body>
</html>
"""


def gerar_relatorio_dependencias(
    df: pd.DataFrame,
    nome_projeto: str = "ItDepends",
    output_path: str = "relatorio_dependencias.html",
    altura_grafico_timeline: int = 400,
    altura_grafico_barras: int = 380,
    template_html: Optional[str] = None
) -> str:
    """
    Gera um relatório HTML interativo com gráficos de dependências.

    Parâmetros:
    -----------
    df : pd.DataFrame
        DataFrame com as colunas obrigatórias:
        - 'Data_Commit': datas dos commits (str ou datetime)
        - 'Hash_Commit': hash dos commits (str)
        - 'Dependencia': nome da dependência (str)
        - 'Versao': versão da dependência (str)

    nome_projeto : str, opcional
        Nome do projeto para exibir no cabeçalho (default: "ItDepends")

    output_path : str, opcional
        Caminho onde o arquivo HTML será salvo (default: "relatorio_dependencias.html")

    altura_grafico_timeline : int, opcional
        Altura em pixels do gráfico de timeline (default: 400)

    altura_grafico_barras : int, opcional
        Altura em pixels do gráfico de barras (default: 380)

    template_html : str, opcional
        Template HTML customizado. Se None, usa o template padrão.
        Use get_template_padrao() para obter o template base.

    Retorna:
    --------
    str
        Caminho do arquivo HTML gerado

    Exemplos:
    ---------
    Uso básico:
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     'Data_Commit': ['2023-01-01', '2023-02-01'],
    ...     'Hash_Commit': ['abc123', 'def456'],
    ...     'Dependencia': ['requests', 'flask'],
    ...     'Versao': ['2.28.0', '2.2.5']
    ... })
    >>> arquivo = gerar_relatorio_dependencias(df, nome_projeto="MeuApp")

    Com template customizado:
    >>> from gerar_relatorio_dependencias import get_template_padrao
    >>> template = get_template_padrao()
    >>> # Modifique o template conforme necessário
    >>> template = template.replace("--bg-main: #020617", "--bg-main: #ffffff")
    >>> arquivo = gerar_relatorio_dependencias(df, template_html=template)
    """

    # Validação do DataFrame
    colunas_obrigatorias = ['Data_Commit', 'Hash_Commit', 'Dependencia', 'Versao']
    colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]

    if colunas_faltantes:
        raise ValueError(
            f"DataFrame está faltando as seguintes colunas obrigatórias: {', '.join(colunas_faltantes)}"
        )

    if df.empty:
        raise ValueError("DataFrame está vazio. Forneça dados para gerar o relatório.")

    # -------------------------------------------------------
    # Preparar dados
    # -------------------------------------------------------
    df_trabalho = df.copy()
    # Converter datas com formato flexível
    df_trabalho["Data_Commit"] = pd.to_datetime(df_trabalho["Data_Commit"], format='mixed', errors='coerce', utc=True)

    # Verificar se há datas inválidas após conversão
    datas_invalidas = df_trabalho["Data_Commit"].isna().sum()
    if datas_invalidas > 0:
        raise ValueError(
            f"Encontradas {datas_invalidas} datas inválidas na coluna 'Data_Commit'. "
            "Verifique o formato das datas."
        )

    total_commits = df_trabalho["Hash_Commit"].nunique()
    total_dependencias = df_trabalho["Dependencia"].nunique()
    ultima_data = df_trabalho["Data_Commit"].max()
    ultima_data_str = ultima_data.strftime("%d/%m/%Y")

    # -------------------------------------------------------
    # DataFrame de resumo por dependência
    # -------------------------------------------------------
    df_sorted = df_trabalho.sort_values(["Dependencia", "Data_Commit"])

    resumo_dep = (
        df_sorted
        .groupby("Dependencia")
        .agg(
            primeira_versao=("Versao", "first"),
            ultima_versao=("Versao", "last"),
            primeiro_commit=("Data_Commit", "min"),
            ultimo_commit=("Data_Commit", "max"),
            qtd_versoes=("Versao", "nunique"),
            qtd_commits=("Hash_Commit", "nunique"),
        )
        .reset_index()
    )

    resumo_dep["primeiro_commit"] = resumo_dep["primeiro_commit"].dt.date
    resumo_dep["ultimo_commit"] = resumo_dep["ultimo_commit"].dt.date
    resumo_dep = resumo_dep.sort_values("qtd_versoes", ascending=False)

    # Tabela HTML
    tabela_resumo_html = resumo_dep.to_html(
        index=False,
        classes="dataframe-table",
        border=0,
    )

    # -------------------------------------------------------
    # Gráfico 1 – Linha do tempo das versões
    # -------------------------------------------------------
    fig_timeline = px.line(
        df_sorted,
        x="Data_Commit",
        y="Versao",
        color="Dependencia",
        title="Linha do tempo de versões por dependência",
        markers=True,
        hover_data=["Hash_Commit"],
    )

    fig_timeline.update_layout(
        height=altura_grafico_timeline,
        autosize=True,
        margin=dict(l=50, r=30, t=60, b=40),
        xaxis=dict(automargin=True),
        yaxis=dict(automargin=True),
    )

    html_plot_timeline = fig_timeline.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={'responsive': True, 'displayModeBar': True}
    )

    # -------------------------------------------------------
    # Gráfico 2 – Barras
    # -------------------------------------------------------
    fig_bar = px.bar(
        resumo_dep,
        x="Dependencia",
        y="qtd_versoes",
        title="Quantidade de versões diferentes por dependência",
    )

    fig_bar.update_layout(
        height=altura_grafico_barras,
        autosize=True,
        margin=dict(l=50, r=30, t=60, b=80),
        xaxis=dict(automargin=True),
        yaxis=dict(automargin=True),
    )

    html_plot_bar = fig_bar.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={'responsive': True, 'displayModeBar': True}
    )

    # -------------------------------------------------------
    # Template HTML
    # -------------------------------------------------------
    if template_html is None:
        template_html = get_template_padrao()

    # Renderizar o template
    template = Template(template_html)

    output_html = template.render(
        nome_projeto=nome_projeto,
        total_dependencias=total_dependencias,
        total_commits=total_commits,
        ultima_data=ultima_data_str,
        plot_timeline=html_plot_timeline,
        plot_upgrades=html_plot_bar,
        tabela_resumo=tabela_resumo_html,
    )

    # Salvar o arquivo
    output_path = Path(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_html)

    return str(output_path.absolute())


# ============================================================================
# EXEMPLO DE USO
# ============================================================================
if __name__ == "__main__":
    # Criar dados de exemplo
    commit_dates = [
        '2023-01-01 10:00:00',
        '2023-01-15 14:30:00',
        '2023-02-05 09:15:00',
        '2023-03-01 11:00:00',
        '2023-03-20 16:45:00',
        '2023-04-10 12:00:00',
        '2023-04-25 10:00:00',
    ]

    commit_hashes = [
        'a1b2c3d4e5f6g7h8i9j0',
        'b2c3d4e5f6g7h8i9j0k1',
        'c3d4e5f6g7h8i9j0k1l2',
        'd4e5f6g7h8i9j0k1l2m3',
        'e5f6g7h8i9j0k1l2m3n4',
        'f6g7h8i9j0k1l2m3n4o5',
        'g7h8i9j0k1l2m3n4o5p6',
    ]

    # Criar DataFrames para diferentes dependências
    df_requests = pd.DataFrame({
        'Data_Commit': commit_dates,
        'Hash_Commit': commit_hashes,
        'Dependencia': 'requests',
        'Versao': ['2.28.0', '2.28.0', '2.28.1', '2.28.1', '2.29.0', '2.30.0', '2.30.0']
    })

    df_flask = pd.DataFrame({
        'Data_Commit': commit_dates,
        'Hash_Commit': commit_hashes,
        'Dependencia': 'flask',
        'Versao': ['2.2.5', '2.2.5', '2.2.5', '2.3.0', '2.3.0', '3.0.0', '3.0.0']
    })

    df_bs4 = pd.DataFrame({
        'Data_Commit': commit_dates,
        'Hash_Commit': commit_hashes,
        'Dependencia': 'beautifulsoup4',
        'Versao': ['4.11.1', '4.11.1', '4.12.0', '4.12.0', '4.12.0', '4.12.0', '4.12.0']
    })

    # Combinar todos os DataFrames
    df_exemplo = pd.concat([df_requests, df_flask, df_bs4], ignore_index=True)

    # Gerar o relatório
    try:
        arquivo_gerado = gerar_relatorio_dependencias(
            df=df_exemplo,
            nome_projeto="itDepends",
            output_path="relatorio_final.html"
        )

        print("Relatório gerado com sucesso!")
        print(f"Arquivo: {arquivo_gerado}")
        print("Nome do projeto em DESTAQUE")
        print("Template pode ser customizado via parâmetro")

    except ValueError as e:
        print(f"Erro: {e}")