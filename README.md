<div align="center">

[![PT-BR](https://img.shields.io/badge/lang-pt--BR-green)](#pt-br)
[![EN](https://img.shields.io/badge/lang-en-blue)](#en)

</div>

---

<a name="en"></a>

# Prompt Pull, Optimization, and Evaluation with LangChain and LangSmith

Project focused on prompt engineering that converts bug reports into agile user stories, evaluated by automatic metrics via LangSmith.

---

## Techniques Applied (Phase 2)

### 1. Role Prompting
**What it is:** Assign a specific and detailed persona to the model before the instructions.

**Why I chose it:** A model without a persona tends to produce generic responses. By defining "You are a senior Product Manager with 10 years of experience in agile methodologies", the model calibrates its vocabulary, level of detail, and tone to the product management context. This directly impacts **Clarity** (more assertive language) and **Precision** (no hallucinated information).

**How I applied it:**
```
You are a senior Product Manager with 10 years of experience in agile methodologies (Scrum and Kanban).
Your specialty is transforming bugs and technical issues into clear, value-oriented user stories
that development teams can implement with precision.
```

---

### 2. Few-shot Learning (required)
**What it is:** Provide concrete input/output examples within the prompt itself.

**Why I chose it:** It has the highest direct impact on F1-Score, as it "anchors" the model to the exact desired output format. Without examples, the model produces user stories in varying formats; with examples, it reproduces the Given-When-Then structure and technical context sections consistently.

**How I applied it:** 3 examples with increasing complexity:
- **Example 1 (simple):** UI bug with a direct user story + basic acceptance criteria
- **Example 2 (medium):** bug with steps to reproduce + technical context section
- **Example 3 (complex):** security bug + multiple criteria sets + severity context

---

### 3. Chain of Thought (CoT)
**What it is:** Instruct the model to reason step by step before generating the final output.

**Why I chose it:** Complex bugs (with multiple issues, stack traces, business impact) require analysis before writing. Without CoT, the model jumps to the user story without considering all aspects. With CoT, it evaluates persona, action, value, criteria, and complexity — improving **Correctness** (F1 + Precision).

**How I applied it:**
```
## REASONING PROCESS (Chain of Thought)
Before writing the user story, think step by step:
1. Who is affected by this bug? (user persona)
2. What does the user need to accomplish? (desired action)
3. What is the business value of fixing this? (benefit)
4. What are the verifiable criteria that the bug has been fixed?
5. Is the bug simple, medium, or complex? (determines level of detail)
```

---

## Final Results

### v1 vs v2 Comparison

| Metric       | v1 (low quality) | v2 (optimized)       | Target |
|--------------|------------------|----------------------|--------|
| Helpfulness  | ~0.45            | run `evaluate.py`    | 0.80   |
| Correctness  | ~0.52            | run `evaluate.py`    | 0.80   |
| F1-Score     | ~0.48            | run `evaluate.py`    | 0.80   |
| Clarity      | ~0.50            | run `evaluate.py`    | 0.80   |
| Precision    | ~0.46            | run `evaluate.py`    | 0.80   |

> **Note:** Run `python src/evaluate.py` after pushing to see the real scores for your environment.

### LangSmith Dashboard
After running `python src/push_prompts.py` and `python src/evaluate.py`, access:
- Prompts: `https://smith.langchain.com/hub/{your_username}`
- Evaluations: `https://smith.langchain.com/projects/prompt-optimization-challenge-resolved`

---

## How to Run

### Prerequisites
- Python 3.9+
- [LangSmith](https://smith.langchain.com) account with API Key
- [OpenAI](https://platform.openai.com/api-keys) account

### Setup

```bash
# 1. Create and activate the virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### `.env` Configuration

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...          # Your LangSmith key
LANGSMITH_PROJECT=prompt-optimization-challenge-resolved
USERNAME_LANGSMITH_HUB=your_username   # Your LangSmith Hub username

OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
EVAL_MODEL=gpt-4o
```

> **Tip:** To find your `USERNAME_LANGSMITH_HUB`, publish any prompt on LangSmith Hub, open it, and click the lock icon 🔒 to see your username.

### Execution

```bash
# Phase 1 — Pull the initial prompt (low quality)
python src/pull_prompts.py

# Phase 2 — The optimized prompt is already at prompts/bug_to_user_story_v2.yml
#            Edit it if you want to iterate further

# Phase 3 — Push the optimized prompt to LangSmith Hub
python src/push_prompts.py

# Phase 4 — Run the evaluation
python src/evaluate.py

# Phase 5 — Run structural validation tests
pytest tests/test_prompts.py -v
```

### Project Structure

```
prompt-optimization-with-lang-smith/
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── README.md                 # This documentation
│
├── prompts/
│   ├── bug_to_user_story_v1.yml  # Initial prompt (generated by pull)
│   └── bug_to_user_story_v2.yml  # Optimized prompt
│
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 examples (5 simple, 7 medium, 3 complex)
│
├── src/
│   ├── pull_prompts.py       # Pull from LangSmith Hub
│   ├── push_prompts.py       # Push to LangSmith Hub
│   ├── evaluate.py           # Automatic evaluation (do not modify)
│   ├── metrics.py            # F1, Clarity, Precision metrics (do not modify)
│   └── utils.py              # Shared helpers (do not modify)
│
└── tests/
    └── test_prompts.py       # 6 structural validation tests
```

### Iterating to improve metrics

If a metric falls below 0.8:

1. Identify which metric failed:
   - **Low F1** → few-shot examples don't represent the dataset well enough
   - **Low Clarity** → format instructions are ambiguous
   - **Low Precision** → the prompt is allowing the model to hallucinate information

2. Edit `prompts/bug_to_user_story_v2.yml`

3. Push and evaluate again:
   ```bash
   python src/push_prompts.py && python src/evaluate.py
   ```

Expect to need 3–5 iterations to reach ≥ 0.8 on all metrics.

---

---

<a name="pt-br"></a>

# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Projeto de prompt engineering que converte bug reports em user stories ágeis, avaliado por métricas automáticas via LangSmith.

---

## Técnicas Aplicadas (Fase 2)

### 1. Role Prompting
**O que é:** Atribuir uma persona específica e detalhada ao modelo antes das instruções.

**Por que escolhi:** O modelo sem persona tende a produzir respostas genéricas. Ao definir "You are a senior Product Manager with 10 years of experience in agile methodologies", o modelo calibra o vocabulário, o nível de detalhe e o tom para o contexto de product management. Isso impacta diretamente a **Clarity** (linguagem mais assertiva) e a **Precision** (sem informações inventadas).

**Como apliquei:**
```
You are a senior Product Manager with 10 years of experience in agile methodologies (Scrum and Kanban).
Your specialty is transforming bugs and technical issues into clear, value-oriented user stories
that development teams can implement with precision.
```

---

### 2. Few-shot Learning (obrigatório)
**O que é:** Fornecer exemplos concretos de entrada e saída esperada dentro do próprio prompt.

**Por que escolhi:** É a técnica com maior impacto direto no F1-Score, pois "ancora" o modelo no formato exato de saída desejado. Sem exemplos, o modelo produz user stories em formatos variados; com exemplos, ele reproduz a estrutura Given-When-Then e as seções de contexto técnico de forma consistente.

**Como apliquei:** 3 exemplos com complexidade crescente:
- **Exemplo 1 (simples):** bug de UI com user story direta + critérios básicos de aceitação
- **Exemplo 2 (médio):** bug com steps to reproduce + seção de contexto técnico
- **Exemplo 3 (complexo):** bug de segurança + múltiplos conjuntos de critérios + contexto de severidade

---

### 3. Chain of Thought (CoT)
**O que é:** Instruir o modelo a raciocinar passo a passo antes de gerar a saída final.

**Por que escolhi:** Bugs complexos (com múltiplos problemas, stack traces, impacto de negócio) exigem análise antes da escrita. Sem CoT, o modelo "pula" para a user story sem considerar todos os aspectos. Com CoT, ele avalia persona, ação, valor, critérios e complexidade — melhorando a **Correctness** (F1 + Precision).

**Como apliquei:**
```
## REASONING PROCESS (Chain of Thought)
Before writing the user story, think step by step:
1. Who is affected by this bug? (user persona)
2. What does the user need to accomplish? (desired action)
3. What is the business value of fixing this? (benefit)
4. What are the verifiable criteria that the bug has been fixed?
5. Is the bug simple, medium, or complex? (determines level of detail)
```

---

## Resultados Finais

### Comparativo v1 vs v2

| Métrica      | v1 (baixa qualidade) | v2 (otimizado)          | Meta |
|--------------|----------------------|-------------------------|------|
| Helpfulness  | ~0.45                | execute `evaluate.py`   | 0.80 |
| Correctness  | ~0.52                | execute `evaluate.py`   | 0.80 |
| F1-Score     | ~0.48                | execute `evaluate.py`   | 0.80 |
| Clarity      | ~0.50                | execute `evaluate.py`   | 0.80 |
| Precision    | ~0.46                | execute `evaluate.py`   | 0.80 |

> **Nota:** Execute `python src/evaluate.py` após o push para ver os scores reais do seu ambiente.

### Dashboard LangSmith
Após executar `python src/push_prompts.py` e `python src/evaluate.py`, acesse:
- Prompts: `https://smith.langchain.com/hub/{seu_username}`
- Avaliações: `https://smith.langchain.com/projects/prompt-optimization-challenge-resolved`

---

## Como Executar

### Pré-requisitos
- Python 3.9+
- Conta no [LangSmith](https://smith.langchain.com) com API Key
- Conta na [OpenAI](https://platform.openai.com/api-keys)

### Setup

```bash
# 1. Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves de API
```

### Configuração do `.env`

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...          # Sua chave do LangSmith
LANGSMITH_PROJECT=prompt-optimization-challenge-resolved
USERNAME_LANGSMITH_HUB=seu_username    # Seu username no LangSmith Hub

OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
EVAL_MODEL=gpt-4o
```

> **Dica:** Para descobrir seu `USERNAME_LANGSMITH_HUB`, publique qualquer prompt no LangSmith Hub, abra-o e clique no ícone de cadeado 🔒 para ver seu username.

### Execução

```bash
# Fase 1 — Pull do prompt inicial (baixa qualidade)
python src/pull_prompts.py

# Fase 2 — O prompt otimizado já está em prompts/bug_to_user_story_v2.yml
#           Edite-o se quiser iterar mais

# Fase 3 — Push do prompt otimizado para o LangSmith Hub
python src/push_prompts.py

# Fase 4 — Execute a avaliação
python src/evaluate.py

# Fase 5 — Execute os testes de validação estrutural
pytest tests/test_prompts.py -v
```

### Estrutura do Projeto

```
prompt-optimization-with-lang-smith/
├── .env.example              # Template de variáveis de ambiente
├── requirements.txt          # Dependências Python
├── README.md                 # Esta documentação
│
├── prompts/
│   ├── bug_to_user_story_v1.yml  # Prompt inicial (gerado pelo pull)
│   └── bug_to_user_story_v2.yml  # Prompt otimizado
│
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 exemplos (5 simples, 7 médios, 3 complexos)
│
├── src/
│   ├── pull_prompts.py       # Pull do LangSmith Hub
│   ├── push_prompts.py       # Push ao LangSmith Hub
│   ├── evaluate.py           # Avaliação automática (não modificar)
│   ├── metrics.py            # Métricas F1, Clarity, Precision (não modificar)
│   └── utils.py              # Funções auxiliares compartilhadas (não modificar)
│
└── tests/
    └── test_prompts.py       # 6 testes de validação estrutural
```

### Iterando para melhorar as métricas

Se alguma métrica ficar abaixo de 0.8:

1. Identifique qual métrica falhou:
   - **F1 baixo** → os exemplos few-shot não representam bem o dataset
   - **Clarity baixo** → as instruções de formato estão ambíguas
   - **Precision baixo** → o prompt está permitindo que o modelo invente informações

2. Edite `prompts/bug_to_user_story_v2.yml`

3. Faça push e avalie novamente:
   ```bash
   python src/push_prompts.py && python src/evaluate.py
   ```

Espere precisar de 3–5 iterações para atingir ≥ 0.8 em todas as métricas.
