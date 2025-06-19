
# Dashboard Forense — Análise e Predição de Casos Criminais

Projeto completo de **Data Science Aplicada**, integrando backend em Flask + MongoDB, frontend em HTML/JS (Chart.js) e Machine Learning (XGBoost), para análise e visualização de ocorrências criminais.

---

## 🗂️ Estrutura do Projeto

```
crime-analysis-app-recuperacao/
├── backend/
│   ├── app.py                 # API Flask + Endpoints ML
│   ├── requirements.txt       # Dependências Python
│   ├── train_model.py         # Script de treinamento do modelo ML
│   ├── model.pkl              # Pipeline do modelo treinado
│   └── ...
├── frontend/
│   ├── index.html             # Dashboard visual (HTML + CSS)
│   ├── script.js              # Integração e gráficos (JS)
│   └── ...
└── README.md
```

---

## ⚙️ Pré-requisitos

- **Python 3.9+**
- **MongoDB** (local ou Atlas)
- **Node.js** *(opcional, apenas se quiser usar outro servidor)*
- **pip** (Python package manager)

---

## 🚀 Instalação e Execução

### 1. **Clone o repositório e acesse a pasta:**
```bash
git clone https://github.com/RICLACPER/crime-analysis-app-recuperacao.git
cd crime-analysis-app-recuperacao
```

### 2. **Instale as dependências do backend**
```bash
cd backend
pip install -r requirements.txt
```

### 3. **Configure o MongoDB**

- Certifique-se de que o MongoDB está rodando localmente (`mongodb://localhost:27017/`) ou ajuste o URI em `app.py` para seu cluster Atlas.
- O sistema cria/popula o banco e coleção automaticamente no primeiro uso.

### 4. **Treine o modelo ML (opcional, se quiser gerar um novo model.pkl)**
```bash
python train_model.py
```
> O arquivo `model.pkl` será gerado/atualizado na pasta backend.

### 5. **Inicie o backend Flask**
```bash
python app.py
```
O backend estará em [http://127.0.0.1:5000](http://127.0.0.1:5000).

### 6. **Inicie o frontend**
```bash
cd ../frontend
python3 -m http.server 8000
```
Abra o navegador em [http://localhost:8000/index.html](http://localhost:8000/index.html).

---

## 📊 Funcionalidades do Dashboard

- **Visualização de Casos:** Gráfico de rosca (por tipo, localização, etnia).
- **Distribuição de Idades das Vítimas:** Gráfico de barras.
- **Importância das Variáveis no Modelo ML:** Gráfico horizontal com as features mais relevantes na predição dos tipos de crime.
- **Filtros de data e variável:** Permite análise personalizada.
- **Predição de novos casos (endpoint ML).**

---

## 🔗 Endpoints da API (Backend Flask)

| Endpoint                                | Método | Descrição                                 |
|------------------------------------------|--------|--------------------------------------------|
| `/api/casos`                            | GET    | Lista todos os casos do banco              |
| `/api/casos`                            | POST   | Cria um novo caso (JSON)                   |
| `/api/casos/<data_do_caso>`             | GET    | Busca um caso por data                     |
| `/api/casos/<data_do_caso>`             | DELETE | Remove um caso por data                    |
| `/api/modelo/coficientes`               | GET    | Retorna importância das variáveis (ML)      |
| `/api/predizer`                         | POST   | Retorna predição do modelo para um novo caso|

---

## 🧠 Machine Learning

- **Modelo:** Pipeline XGBoost + OneHotEncoder (sklearn)
- **Treinamento:** Dados lidos do MongoDB
- **Arquivo:** `model.pkl` (mantido no backend)
- **Endpoint:** `/api/modelo/coficientes` para feature importance, `/api/predizer` para predição

---

## 🖥️ Estrutura HTML/CSS (index.html/login.html)

- Responsivo e simples, seguindo padrão dos slides
- Seletor de variável dinâmica para análise (tipo, localização, etnia)
- Inputs de data para filtro
- Gráficos construídos com Chart.js
- Login: admin, senha: 1234

---

## 📈 Gráficos e Visualizações

- **Gráfico Rosca:** Distribuição por variável selecionada (tipo, localização, etnia)
- **Gráfico Barras:** Distribuição de idades das vítimas
- **Gráfico Barras Horizontal:** Importância das features (modelo ML)

---

## 🛠️ Dicas e Resolução de Problemas

- **Erro 404 nos endpoints:** Verifique se o backend está rodando e se os caminhos estão corretos
- **Arquivo model.pkl não encontrado:** Gere via `train_model.py` e mantenha na pasta `/backend`
- **CORS:** Já está ativado no Flask (`CORS(app)`), mas se acessar por outro IP/porta, garanta que está liberado
- **Conexão MongoDB Atlas:** Troque o URI no app.py caso use cloud
- **Front-end não mostra gráficos:** Veja se a URL do backend está igual em `script.js` (`http://127.0.0.1:5000`)
- **Reinstale dependências:**  
  ```bash
  pip install -r requirements.txt
  ```

---

## 📸 Screenshots do Funcionamento

> Coloque prints do dashboard mostrando os 3 gráficos, filtros, tela inicial, etc.

---

## 📝 Possíveis Customizações

- Troque temas/cores do Chart.js conforme seu gosto
- Adicione campos extras para novas análises no backend/ML
- Permita exportação de dados em CSV (botão já no HTML)

## 📝 Arquivos no .gitignore:

# Python
__pycache__/
*.pyc

# VS Code
.vscode/

# Dados/modelos grandes
backend/model.pkl

# Configs/env
.env

# MongoDB dump
*.bson
*.json

# Node.js
node_modules/
