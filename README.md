# Dashboard Forense — Análise e Predição de Casos Criminais

Projeto acadêmico de Data Science com API Flask, banco PostgreSQL/Supabase, frontend HTML/JavaScript com Chart.js e um modelo Random Forest para predição do status das ocorrências.

## Estrutura

```text
data-Science-Dashboard/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── popular_base.py
│   ├── popular_em_investigacao.py
│   ├── verificar_status_banco.py
│   ├── train_model_avaliado.py
│   ├── schema.sql
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── login.html
│   └── script.js
├── .env.example
└── README.md
```

## Pré-requisitos

- Python 3.10 ou superior
- PostgreSQL ou um projeto no Supabase
- `pip`

## Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/Riclacper/data-Science-Dashboard.git
cd data-Science-Dashboard
```

### 2. Crie o ambiente virtual e instale as dependências

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
```

No Linux ou macOS:

```bash
source .venv/bin/activate
```

Depois:

```bash
pip install -r backend/requirements.txt
```

### 3. Configure o banco

Copie `.env.example` para `.env` e informe a URI do PostgreSQL/Supabase:

```env
DATABASE_URL=postgresql+psycopg://usuario:senha@host:6543/postgres?sslmode=require
CORS_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
FLASK_DEBUG=false
```

No Supabase, a URI fica em **Settings > Database > Connection string**. Use preferencialmente a conexão pelo pooler para aplicações web.

A API cria a tabela `ocorrencias` automaticamente ao iniciar. Como alternativa, execute `backend/schema.sql` no SQL Editor do Supabase.

### 4. Popule dados de demonstração

```bash
cd backend
python popular_base.py
python popular_em_investigacao.py
```

### 5. Treine o modelo

```bash
python train_model_avaliado.py
```

Esse comando gera localmente:

- `backend/model.pkl`
- `backend/avaliacao_modelo.json`

O artefato inclui o pré-processamento categórico e o classificador, evitando divergência entre o treinamento e a API.

### 6. Inicie a API

```bash
python app.py
```

A API estará em `http://127.0.0.1:5000`.

### 7. Inicie o frontend

Em outro terminal:

```bash
cd frontend
python -m http.server 8000
```

Abra `http://localhost:8000/login.html`.

## Endpoints atuais

| Endpoint | Método | Descrição |
|---|---|---|
| `/` | GET | Estado básico da API e do modelo |
| `/casos` | GET | Lista as ocorrências |
| `/casos` | POST | Insere uma ocorrência |
| `/features` | GET | Retorna a importância agregada das variáveis |
| `/predict` | POST | Prediz o status de uma ocorrência |
| `/teste` | GET | Testa a consulta ao banco |
| `/avaliar-modelo` | GET | Retorna a avaliação gerada no treinamento |
| `/classes` | GET | Retorna os rótulos conhecidos pelo modelo |

## Exemplo de ocorrência

```json
{
  "tipoCrime": "Furto",
  "status": "Em investigação",
  "data": "2026-07-22",
  "hora": "14:30",
  "descricao": "Registro de demonstração",
  "nomeVitima": "Pessoa de exemplo",
  "local": "Rua Exemplo",
  "cidade": "Recife",
  "uf": "PE",
  "coordenadas": "",
  "perito": "Perito de exemplo",
  "fotos": [],
  "anexos": []
}
```

## Segurança

- Nunca coloque senhas ou URIs reais no código ou no Git.
- O arquivo `.env` não deve ser versionado.
- Restrinja `CORS_ORIGINS` aos endereços efetivamente usados.
- Revogue qualquer credencial que já tenha sido publicada anteriormente no histórico do repositório.

## Observações sobre o modelo

Os scripts de população geram dados sintéticos. Eles servem para demonstrar a integração técnica, não para produzir conclusões forenses reais. Para métricas confiáveis, utilize um conjunto de dados legítimo, documentado e com relação estatística entre as variáveis e o alvo.
