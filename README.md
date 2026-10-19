# Retain — Gestão de Retenção

Sistema web para gestão e acompanhamento de indicadores de retenção, desenvolvido em Python com Flask e SQLite.

O Retain permite registrar o desempenho diário dos operadores, acompanhar resultados por equipe e gerar relatórios gerenciais para apoiar a análise dos indicadores de retenção.

## Funcionalidades

- **Dashboard:** visualização de indicadores, gráficos de evolução, comparação entre equipes e ranking de operadores.
- **Gestão de operadores:** cadastro, edição, organização por equipe e controle de status ativo ou inativo.
- **Histórico de lançamentos:** consulta e edição dos registros diários.
- **Configurações:** definição da meta de retenção.
- **Relatórios gerenciais:** análise por período, com indicadores gerais, comparativo entre equipes e desempenho individual.
- **Exportação em PDF:** geração de relatórios com tabelas, indicadores e identificação do sistema.
- **Validações:** prevenção de registros duplicados para o mesmo operador e data, além de validação dos dados informados.

## Indicadores

O sistema calcula automaticamente a quantidade de retenções e o percentual de retenção com base nos dados registrados.

**Cálculo de retenções:**

Retenções = Ligações atendidas − Cancelamentos

**Taxa de retenção:**

Taxa de retenção (%) = (Retenções ÷ Ligações atendidas) × 100

A meta de retenção pode ser configurada diretamente no sistema.

## Tecnologias utilizadas

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- HTML
- CSS
- JavaScript
- Chart.js
- ReportLab

## Estrutura do projeto

```text
Retain/
├── app.py
├── models.py
├── requirements.txt
├── README.md
├── templates/
│   ├── dashboard.html
│   ├── operators.html
│   ├── new_operator.html
│   ├── operator_detail.html
│   ├── edit_record.html
│   ├── edit_operator.html
│   ├── settings.html
│   ├── records.html
│   └── reports.html
└── static/
    └── css/
        └── style.css
```

O banco de dados SQLite é criado localmente, conforme a configuração de inicialização da aplicação.

## Como executar localmente

### 1. Pré-requisitos

- Python instalado.
- Git instalado, caso queira clonar o repositório.

### 2. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
cd Retain
```

Substitua `URL_DO_REPOSITORIO` pelo endereço do repositório no GitHub.

### 3. Criar um ambiente virtual

No Windows:

```bash
python -m venv .venv
```

### 4. Ativar o ambiente virtual

No Prompt de Comando:

```bat
.venv\Scripts\activate
```

No PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 6. Executar a aplicação

```bash
python app.py
```

Acesse no navegador o endereço local informado pelo Flask, normalmente:

`http://127.0.0.1:5000`

> **Observação:** a criação automática do banco e das tabelas depende da configuração de inicialização da aplicação.

## Banco de dados

O projeto utiliza SQLite para armazenar operadores, lançamentos diários e configurações.

O arquivo do banco é local e não deve conter dados de teste ou informações operacionais no repositório público.

## Objetivo do projeto

O Retain foi desenvolvido para centralizar o acompanhamento dos indicadores de retenção, facilitar a comparação de resultados entre equipes e operadores e simplificar a geração de relatórios gerenciais.

## Autor

**Matheus Ribeiro**

Projeto desenvolvido para gestão e acompanhamento de indicadores de retenção.