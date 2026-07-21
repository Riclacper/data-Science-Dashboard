# Dashboard Forense — Análise e Predição de Casos Criminais

Projeto de **Data Science Aplicada**, integrando backend em Flask + MongoDB, frontend em HTML/JS (Chart.js) e Machine Learning (RandomForest/scikit-learn), para análise e visualização de ocorrências criminais.

---

## 🗂️ Estrutura do Projeto

```
data-Science-Dashboard/
├── backend/
│   ├── app.py                    # API Flask + Endpoints ML
│   ├── requirements.txt          # Dependências Python
│   ├── train_model_avaliado.py   # Script de treinamento do modelo ML
│   ├── popular_base.py           # Popula o banco com dados simulados
│   ├── popular_em_investigacao.py
│   ├── verificar_status_mongo.py
│   ├── gerar_relatorio_com_email.py
│   └── .env.example              # Modelo de variáveis de ambiente
├── model/
│   └── model.pkl                 # Modelo treinado (gerado por train_model_avaliado.py)
├── frontend/
│   ├── index.html                # Dashboard visual (HTML + CSS)
│   ├── login.html                # Tela de login
│   └── script.js                 # Integração e gráficos (JS)
└── README.md
```

---

## ⚙️ Pré-requisitos

- **Python 3.9+**
- **MongoDB** (local ou Atlas)
- **pip**

---

## 🚀 Instalação e Execução

### 1. Clone o repositório e acesse a pasta
```bash
git clone https://github.com/Riclacper/data-Science-Dashboard.git
cd data-Science-Dashboard
```

### 2. Instale as dependências do backend
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Copie o arquivo de exemplo e preencha com seus dados:
```bash
cp backend/.env.example backend/.env
```

Edite `backend/.env`:
```
MONGO_URI=mongodb+srv://<usuario>:<senha>@<cluster>.mongodb.net/forense?retryWrites=true&w=majority
LOGIN_USER=admin
LOGIN_PASS=minha_senha_segura
SECRET_KEY=gere_uma_chave_aleatoria_longa_aqui
EMAIL_ORIGEM=seuemail@gmail.com
SENHA_APP=senha_de_app_gmail
FLASK_ENV=development
```

> ⚠️ **Nunca commite o arquivo `.env`** — ele já está no `.gitignore`.

### 4. Popule o banco de dados (opcional)
```bash
python backend/popular_base.py
```

### 5. Treine o modelo ML
```bash
python backend/train_model_avaliado.py
```
> Isso gera `model/model.pkl`, `backend/avaliacao_modelo.json` e `backend/classes_labels.json`.

### 6. Inicie o backend Flask
```bash
python backend/app.py
```
O backend estará em [http://127.0.0.1:5000](http://127.0.0.1:5000).

### 7. Inicie o frontend
```bash
cd frontend
python3 -m http.server 8000
```
Abra o navegador em [http://localhost:8000/login.html](http://localhost:8000/login.html).

### 🐳 Alternativa: Rodar com Docker

```bash
cp backend/.env.example backend/.env  # preencha as variáveis
docker compose up --build
```
- Backend em [http://localhost:5000](http://localhost:5000)
- Frontend em [http://localhost:8000](http://localhost:8000)

---

## ☁️ Deploy no Render.com

O projeto inclui um arquivo `render.yaml` pronto para uso via **Render Blueprint**.

### Passo a passo

1. **Crie os serviços no Render**
   - Acesse [render.com](https://render.com) → *New* → *Blueprint*
   - Conecte este repositório; o Render detectará o `render.yaml` automaticamente
   - Dois serviços serão criados: `forense-backend` (Web Service) e `forense-frontend` (Static Site)

2. **Configure as variáveis de ambiente do backend** no painel do Render:

   | Variável       | Valor                                                         |
   |----------------|---------------------------------------------------------------|
   | `MONGO_URI`    | URI do MongoDB Atlas (ex: `mongodb+srv://...`)                |
   | `LOGIN_USER`   | Usuário de acesso ao dashboard                                |
   | `LOGIN_PASS`   | Senha de acesso ao dashboard                                  |
   | `SECRET_KEY`   | Gerado automaticamente pelo Render                            |
   | `EMAIL_ORIGEM` | E-mail para envio de relatórios                               |
   | `SENHA_APP`    | Senha de App do Gmail (16 caracteres)                         |

3. **Aguarde o primeiro deploy do backend** e copie a URL gerada (ex: `https://forense-backend.onrender.com`)

4. **Atualize o frontend** — edite `frontend/config.js` e substitua a URL local pela URL do backend:
   ```js
   const API = window.API_URL || 'https://forense-backend.onrender.com';
   ```

5. **Faça push** para o repositório; o Render fará o redeploy automático do frontend

> ⚠️ **Plano gratuito**: o serviço pode entrar em *sleep* após inatividade. O primeiro acesso após um período ocioso pode levar ~30 segundos.

---

## 🧪 Testes

```bash
pip install -r backend/requirements.txt
pytest --tb=short -q
```

Os testes usam mocks para MongoDB e o modelo ML — nenhuma conexão real necessária.

---

## 📊 Funcionalidades do Dashboard

- **Visualização de Casos:** Gráfico de barras por tipo de crime, com filtro.
- **Importância das Variáveis:** Gráfico horizontal com features mais relevantes no modelo ML.
- **Métricas do Modelo:** Tabela e gráficos de precisão, cobertura e F1-score por classe.
- **Predição:** Previsão do status de uma nova ocorrência com base no modelo.
- **Exportar CSV:** Download dos casos filtrados.
- **Envio de Relatório por E-mail:** Gera PDF e envia para o endereço informado.

---

## 🔗 Endpoints da API (Backend Flask)

| Endpoint              | Método | Descrição                                      |
|-----------------------|--------|------------------------------------------------|
| `/`                   | GET    | Página inicial / verificação de status         |
| `/login`              | POST   | Autenticação (`{usuario, senha}`)              |
| `/casos`              | GET    | Lista todos os casos do banco                  |
| `/casos`              | POST   | Cria um novo caso (JSON)                       |
| `/features`           | GET    | Retorna importância das variáveis (ML)         |
| `/predict`            | POST   | Prediz status para um novo caso                |
| `/avaliar-modelo`     | GET    | Retorna métricas de avaliação do modelo        |
| `/classes`            | GET    | Retorna labels legíveis das classes do modelo  |
| `/enviar-relatorio`   | POST   | Gera PDF e envia por e-mail (`{email}`)        |
| `/teste`              | GET    | Verifica conexão com MongoDB                   |

---

## 🧠 Machine Learning

- **Modelo:** RandomForestClassifier (scikit-learn)
- **Features:** `tipoCrime`, `cidade`, `uf`, `hora_num`
- **Target:** `status` (codificado via LabelEncoder)
- **Arquivo:** `model/model.pkl`

---

## 🛠️ Resolução de Problemas

- **`MONGO_URI não definida`**: Certifique-se de que o arquivo `backend/.env` existe e está preenchido.
- **`model.pkl não encontrado`**: Execute `python backend/train_model_avaliado.py`.
- **`avaliacao_modelo.json / classes_labels.json não encontrado`**: Execute `python backend/train_model_avaliado.py`.
- **CORS**: Já configurado com `flask-cors`. Se acessar de outro IP, ajuste conforme necessário.
- **Erro 401 no login**: Verifique `LOGIN_USER` e `LOGIN_PASS` no `.env`.
