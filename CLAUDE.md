# 🧠 Agente RAG – Certidão Imobiliária (PBH)

Este projeto implementa um **Agente de Migração Assistida por IA**, baseado em **LangGraph**, **LangChain**, **RAG com ChromaDB**, integrado a ferramentas personalizadas capazes de:

- Navegar pelos diretórios do projeto
- Ler e escrever arquivos
- Consultar toda a documentação indexada via RAG
- Planejar e replanejar etapas de migração
- Auxiliar na modernização da Certidão Imobiliária da PBH

O agente funciona como um **assistente interativo**, capaz de responder perguntas, gerar código, sugerir mudanças arquiteturais e registrar automaticamente todas as alterações realizadas.

---

## 🔧 Tecnologias Utilizadas

- **Python 3.11+**
- **LangChain Classic**
- **LangGraph**
- **ChromaDB (persistente)**
- **OpenAI GPT-4o / GPT-4o-mini / GPT-4.1**
- **Ferramentas customizadas (tools.py)**
- **RAG com histórico conversacional**
- **Callback para terminal (debug)**

---

## 📂 Estrutura do Projeto

```
agente-rag/
│
├── core/
│   ├── rag_agent.py         # Construção do agente LangGraph + RAG
│   ├── tools.py             # Tools customizadas utilizadas pelo agente
│   ├── config.py            # Configurações gerais e paths
│   ├── cli.py               # CLI interativa para rodar o agente no terminal
│   └── utils.py             # Funções auxiliares e logs
│
├── ingest.py                # Indexação da documentação no ChromaDB
├── system_prompt.md         # System prompt principal do agente
└── README.md                # Este arquivo
```

---

## 🧩 Como o Agente Funciona

O agente é composto por 3 camadas:

### **1. RAG (Retrieval Augmented Generation)**

- Usa `ChromaDB`, alimentado pelo `ingest.py`
- Embeddings OpenAI (`text-embedding-3-large`)
- Histórico de conversa incluído no contexto
- Recupera fontes e cita documentos usados na resposta

### **2. ReAct Agent (LangGraph)**

- Recebe system prompt enriquecido pelo contexto do projeto
- Tem ferramentas externas “tools” para manipulação de arquivos e consultas
- Capaz de executar loops de raciocínio (criticar, planejar, executar)

### **3. Tools (Ferramentas externas)**

Atualmente disponíveis:

| Tool                        | Descrição                                            |
| --------------------------- | ---------------------------------------------------- |
| `consultar_documentacao`    | Consulta o banco RAG e retorna resposta + fontes     |
| `buscar_arquivos`           | Busca arquivos por nome no projeto                   |
| `ler_arquivo`               | Lê qualquer arquivo                                  |
| `escrever_arquivo`          | Escreve conteúdo e registra alteração                |
| `planejar_etapas` _(nova)_  | Gera planejamento por etapas (T1…T6…)                |
| `replanejar` _(nova)_       | Recalcula planejamento considerando problemas        |
| `resumir_arquivo` _(nova)_  | Gera resumo de qualquer arquivo fonte                |
| `explicar_codigo` _(nova)_  | Explica trechos complexos de código                  |
| `mapear_endpoints` _(nova)_ | Lista endpoints detectados no backend                |
| `diagnosticar_bug` _(nova)_ | Identifica possíveis causas de erro a partir de logs |

> Essas novas ferramentas permitem que o agente seja usado em **qualquer projeto**, não apenas no da PBH.

---

## 🚀 Como Operar o Agente

### **1. Ingerir toda a base da documentação**

Antes de rodar o agente pela primeira vez:

```bash
python ingest.py
```

Isso irá:

- varrer `docs/`, `backend/`, `frontend/`
- gerar embeddings
- salvar no banco persistent ChromaDB (`/db`)

---

### **2. Rodar o agente**

Execute:

```bash
python agent.py
```

O terminal abrirá:

```
Agente RAG Certidão Imobiliária – digite 'sair' para encerrar.
Você:
```

---

## 🧭 Fluxo Ideal de Uso

### 🔹 **1. Iniciar sessão**

```
iniciar migração
```

### 🔹 **2. Ver ferramentas disponíveis**

```
quais as tools disponíveis
```

### 🔹 **3. Consultar documentação**

```
consultar_documentacao USC_04_142
```

### 🔹 **4. Gerar planejamento**

```
planejar migração T6
```

### 🔹 **5. Buscar arquivos relevantes**

```
buscar_arquivos backend_atual protocolo
```

### 🔹 **6. Ler arquivo**

```
ler_arquivo src/modules/protocolos/protocolos.controller.ts
```

### 🔹 **7. Gerar nova versão (com tool)**

```
escrever_arquivo src/modules/protocolos/protocolos.controller.ts
<novo código aqui>
```

### 🔹 **8. Replanejar caso encontre problemas**

```
replanejar migração considerando erro na etapa de autenticação
```

### 🔹 **9. Revisões finais**

```
resumir_arquivo docs/migracao/analise_geral.md
```

---

## 🧪 Comportamento do Agente

Durante cada ação, o terminal exibe:

```
[Agente] Consultando LLM...
[Agente] LLM respondeu.
[Agente] Executando tool 'ler_arquivo'...
[Agente] Tool concluída.
```

Útil para depuração e entender o fluxo de execução.

---

## 🧭 Onde Ficam Registradas as Alterações?

O agente registra automaticamente:

- **arquivos alterados**
- **timestamp**
- **resumo das mudanças**

Logs ficam em:

```
/logs/alters_YYYYMMDD.json
```

---

## 🛠️ Variáveis de Ambiente

| Variável               | Descrição                                   |
| ---------------------- | ------------------------------------------- |
| `OPENAI_API_KEY`       | chave principal                             |
| `OPENAI_MODEL`         | modelo a ser usado (gpt-4o-mini por padrão) |
| `AGENT_MAX_ITERATIONS` | limite de passos ReAct                      |

---

## 👤 Autor

**Rafael Campagnoli Bueno**
Engenheiro de Software – Codesis Sistemas
Especialista em modernização de sistemas, RAGs e agentes autônomos

---

## 📜 Licença

MIT – Uso livre inclusive para outros projetos.
