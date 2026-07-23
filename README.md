# Dashboard Forense

Dashboard full stack para análise exploratória de ocorrências sintéticas, desenvolvido como projeto de portfólio em Data Science e desenvolvimento web.

[![CI](https://github.com/Riclacper/data-Science-Dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/Riclacper/data-Science-Dashboard/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1)](https://supabase.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Demonstração online

- **Frontend:** https://data-science-dashboard-vafr.onrender.com
- **API:** https://data-science-dashboard-api.onrender.com
- **Health check:** https://data-science-dashboard-api.onrender.com/health

> O serviço utiliza a camada gratuita do Render e pode levar alguns segundos para iniciar após um período de inatividade.

## Visão geral

O projeto demonstra uma arquitetura completa, desde a geração e persistência dos dados até a publicação de um dashboard responsivo:

- frontend público, modular e acessível;
- API REST desenvolvida com Flask;
- persistência em PostgreSQL/Supabase com SQLAlchemy;
- filtros combináveis e paginação processada no backend;
- gráficos interativos com Chart.js;
- exportação CSV do conjunto filtrado;
- pipeline de classificação com scikit-learn;
- inicialização automática e idempotente do ambiente demonstrativo;
- testes automatizados, lint e integração contínua.

## Arquitetura

```mermaid
flowchart LR
    U[Usuário] --> F[Frontend estático<br/>HTML, CSS e ES Modules]
    F -->|HTTPS / JSON| A[API Flask / Gunicorn]
    A --> D[(PostgreSQL / Supabase)]
    A --> M[Pipeline Random Forest<br/>scikit-learn]
    G[GitHub Actions] -->|lint e testes| R[Repositório GitHub]
    R -->|deploy automático| F
    R -->|deploy automático| A
```

## Funcionalidades

### Dashboard

- indicadores gerais de volume, status, tipo e cidade;
- filtros por texto, tipo, status, cidade, UF e período;
- gráficos de distribuição por tipo, status e cidade;
- tabela com paginação, ordenação e seleção de quantidade por página;
- exportação CSV compatível com caracteres acentuados;
- estados de carregamento, indisponibilidade e nova tentativa;
- layout responsivo para desktop, tablet e celular.

### Machine learning

- pré-processamento categórico com `OneHotEncoder`;
- variáveis numéricas para hora e tempo desde a ocorrência;
- classificador `RandomForestClassifier`;
- pipeline único para treinamento e inferência;
- importância agregada das variáveis;
- precisão, cobertura, F1-score e matriz de confusão;
- formulário público para simulação de classificação.

### Backend

- inicialização automática das tabelas;
- atualização segura da base sintética legada;
- carga idempotente de dados demonstrativos;
- treinamento automático quando os artefatos não existem;
- validação de payloads;
- paginação, ordenação, busca e filtros no servidor;
- endpoint de health check.

## Dados sintéticos

Os registros são gerados de maneira determinística e controlada. O status possui relações probabilísticas com a idade da ocorrência e o tipo registrado, permitindo demonstrar um pipeline de aprendizado supervisionado com padrões verificáveis.

Os nomes, endereços, equipes e demais informações são fictícios. As métricas não representam desempenho sobre dados policiais reais e não devem ser utilizadas em decisões operacionais.

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Frontend | HTML5, CSS3, JavaScript ES Modules, Chart.js |
| Backend | Python, Flask, Flask-CORS, Gunicorn |
| Banco | PostgreSQL, Supabase, SQLAlchemy, psycopg |
| Data Science | pandas, scikit-learn, joblib |
| Qualidade | pytest, Ruff, GitHub Actions |
| Deploy | Render Static Site, Render Web Service |

## Estrutura do projeto

```text
data-Science-Dashboard/
├── .github/workflows/
│   └── ci.yml
├── backend/
│   ├── tests/
│   │   └── test_api.py
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── popular_base.py
│   ├── train_model_avaliado.py
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/
│   ├── css/
│   │   ├── variables.css
│   │   ├── components.css
│   │   └── dashboard.css
│   ├── js/
│   │   ├── api.js
│   │   ├── charts.js
│   │   ├── config.js
│   │   ├── main.js
│   │   ├── table.js
│   │   └── utils.js
│   ├── index.html
│   ├── login.html
│   └── logo.png
├── .env.example
├── LICENSE
├── pyproject.toml
└── README.md
```

## Execução local

### 1. Clone o projeto

```bash
git clone https://github.com/Riclacper/data-Science-Dashboard.git
cd data-Science-Dashboard
```

### 2. Configure o ambiente Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

No Windows, ative com:

```powershell
.venv\Scripts\activate
```

### 3. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Exemplo:

```env
DATABASE_URL=postgresql+psycopg://usuario:senha@host:6543/postgres?sslmode=require
CORS_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
FLASK_DEBUG=false
AUTO_SEED_DEMO_DATA=true
DEMO_SAMPLE_SIZE=300
```

### 4. Inicie a API

```bash
cd backend
python app.py
```

Na primeira execução, a aplicação cria as tabelas, insere a base demonstrativa e treina o modelo automaticamente.

### 5. Inicie o frontend

Em outro terminal:

```bash
cd frontend
python -m http.server 8000
```

Acesse `http://localhost:8000`.

## Endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/` | Metadados básicos da API |
| GET | `/health` | Estado do banco, modelo e quantidade de registros |
| GET | `/casos` | Lista completa das ocorrências |
| GET | `/casos/paginados` | Paginação, busca, filtros e ordenação |
| POST | `/casos` | Insere uma ocorrência validada |
| GET | `/features` | Importância agregada das variáveis |
| GET | `/avaliar-modelo` | Métricas e matriz de confusão |
| GET | `/classes` | Mapeamento das classes do modelo |
| POST | `/predict` | Executa uma classificação demonstrativa |

### Parâmetros de `/casos/paginados`

| Parâmetro | Exemplo |
|---|---|
| `pagina` | `1` |
| `porPagina` | `20` |
| `ordenarPor` | `data` |
| `ordem` | `desc` |
| `busca` | `Recife` |
| `tipoCrime` | `Furto` |
| `status` | `Concluído` |
| `cidade` | `Recife` |
| `uf` | `PE` |
| `dataInicial` | `2026-01-01` |
| `dataFinal` | `2026-07-22` |

## Testes e qualidade

```bash
pip install -r backend/requirements-dev.txt
cd backend
ruff check .
pytest -q
```

O workflow em `.github/workflows/ci.yml` executa essas verificações em pushes e pull requests.

## Segurança e privacidade

- credenciais são carregadas exclusivamente por variáveis de ambiente;
- o arquivo `.env` é ignorado pelo Git;
- o dashboard não utiliza autenticação simulada no navegador;
- os dados são fictícios e identificados como sintéticos;
- o CORS pode ser restrito aos domínios efetivamente publicados.

## Limitações conhecidas

- os dados não refletem uma distribuição real de ocorrências;
- as métricas servem apenas para validação técnica do pipeline;
- os artefatos do modelo são gerados no filesystem efêmero do serviço e podem ser recriados após novos deploys;
- o envio de relatórios por e-mail não integra o escopo atual do projeto.

## Próximas evoluções

- documentação OpenAPI/Swagger;
- testes de integração com PostgreSQL em ambiente isolado;
- versionamento formal do dataset e do modelo;
- monitoramento de performance e observabilidade;
- migração opcional do frontend para React e Vite.

## Autor

**Ricardo Lacerda Pereira**  
Análise e Desenvolvimento de Sistemas · Data Science · Desenvolvimento Full Stack

## Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE).
