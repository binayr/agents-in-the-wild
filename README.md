# 🤖 Agents in the Wild

A sophisticated AI agent orchestration platform built with LangChain and Azure OpenAI, featuring multiple specialized agents with distinct capabilities and human-in-the-loop workflows.

## ✨ Features

- **Multiple Specialized Agents**: Modular agent architecture with distinct personalities and capabilities
- **Azure OpenAI Integration**: Powered by GPT-4o models for intelligent responses and actions
- **Human-in-the-Loop (HITL)**: Built-in approval workflows for sensitive actions
- **Structured Outputs**: Type-safe responses using Pydantic models
- **Tool Calling**: Extensible tool framework for agent capabilities
- **LangGraph Workflows**: Advanced agent orchestration with state management
- **Memory & Checkpointing**: In-memory state persistence for conversation continuity

## 📋 Table of Contents

- [Agents](#agents)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Development](#development)
- [License](#license)

## 🤖 Agents

### Sheldon - The Knowledge Agent

A helpful question-answering agent with deep knowledge across various domains.

**Capabilities:**
- Answers questions on any topic
- Provides structured responses with justifications
- Uses GPT-4o for intelligent reasoning

**Use Cases:**
- General knowledge queries
- Research assistance
- Information retrieval

### Tony - The Action Agent

An autonomous agent capable of taking actions on your behalf with optional human oversight.

**Capabilities:**
- Executes actions based on user intent
- Tool calling with extensible framework
- Human-in-the-loop approval workflows
- State management with checkpointing

**Use Cases:**
- Task automation
- Workflow execution
- Controlled autonomous operations

## 🏗️ Architecture

```
agents-in-the-wild
├── core/
│   ├── model.py          # Azure OpenAI model factory
│   └── config.py         # Configuration management
├── agents/
│   ├── sheldon/
│   │   └── agent.py      # Question-answering agent
│   └── tony/
│       └── agent.py      # Action-taking agent with HITL
└── main.py               # Application entry point
```

### Tech Stack

- **LangChain**: Agent orchestration and chain composition
- **LangGraph**: State machine workflows with interrupts
- **Azure OpenAI**: GPT-4o language models
- **Pydantic**: Data validation and structured outputs
- **Python 3.11+**: Modern Python features

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- Azure OpenAI API access
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

1. **Clone the repository:**

```bash
git clone https://github.com/binayr/agents-in-the-wild.git
cd agents-in-the-wild
```

2. **Install dependencies:**

Using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**

Create a `.env` file in the project root:

```bash
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_VERSION=2024-02-01
EMBEDDING_OPENAI_API_BASE=your_embedding_endpoint
EMBEDDING_OPENAI_API_KEY=your_embedding_key
EMBEDDING_OPENAI_API_VERSION=2024-02-01
```

## ⚙️ Configuration

The project uses environment variables for configuration. All settings are managed in `core/config.py`.

### Required Variables

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI service endpoint |
| `AZURE_OPENAI_VERSION` | API version (e.g., 2024-02-01) |
| `EMBEDDING_OPENAI_API_BASE` | Embedding service endpoint |
| `EMBEDDING_OPENAI_API_KEY` | Embedding service API key |
| `EMBEDDING_OPENAI_API_VERSION` | Embedding API version |

## 💻 Usage

### Running the Application

```bash
python main.py
```

### Using Sheldon (Q&A Agent)

```python
from agents.sheldon.agent import answer_agent

state = {"input": "What is quantum computing?"}
result = answer_agent(state)

print(f"Answer: {result['output']}")
print(f"Justification: {result['justification']}")
```

### Using Tony (Action Agent)

**Standard Mode:**
```python
from agents.tony.agent import action_agent

state = {"question": "Send a report to the team"}
result = action_agent(state)

print(f"Output: {result['output']}")
print(f"Tool Called: {result['tool_call']}")
print(f"Status: {result['tool_output']}")
```

**With Human-in-the-Loop:**
```python
from agents.tony.agent import action_agent_hitl

state = {"question": "Delete all temporary files"}
result = action_agent_hitl(state)
# Agent will pause and request approval before executing
```

### Available Models

```python
from core.model import AzureOpenAIModel

# Chat models
model = AzureOpenAIModel.get_model("gpt-4o")
mini_model = AzureOpenAIModel.get_model("gpt-4o-mini")

# Embedding models
embeddings = AzureOpenAIModel.get_embedding_model("text-embedding-ada-002")
```

## 📁 Project Structure

```
agents-in-the-wild/
├── .gitignore              # Git ignore rules
├── .python-version         # Python version specification
├── README.md               # Project documentation
├── pyproject.toml          # Project metadata and dependencies
├── uv.lock                 # Dependency lock file
├── main.py                 # Application entry point
│
├── core/                   # Core functionality
│   ├── config.py          # Configuration and environment variables
│   └── model.py           # Azure OpenAI model factory
│
└── agents/                 # Agent implementations
    ├── sheldon/
    │   └── agent.py       # Question-answering agent
    └── tony/
        └── agent.py       # Action-taking agent with HITL
```

## 🛠️ Development

### Adding a New Agent

1. Create a new directory under `agents/`:
```bash
mkdir -p agents/your_agent
```

2. Create `agent.py` with your agent implementation:
```python
from core.model import AzureOpenAIModel
from pydantic import BaseModel, Field

model = AzureOpenAIModel.get_model("gpt-4o")

class YourAgentOut(BaseModel):
    output: str = Field(description="agent output")

def your_agent(state) -> dict:
    # Your agent logic here
    pass
```

3. Import and use your agent in `main.py`

### Code Quality

The project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check code
ruff check .

# Format code
ruff format .
```

## 📊 Agent Comparison

| Agent | Type | Tools | HITL | Structured Output | Use Case |
|-------|------|-------|------|-------------------|----------|
| **Sheldon** | Q&A | ❌ | ❌ | ✅ | Knowledge retrieval, information lookup |
| **Tony** | Action | ✅ | ✅ | ✅ | Task automation, controlled actions |
| **Jarvis** | Action | ✅ | ✅ | ✅ | Writes code |
| **Element** | action | ❌ | ❌ | ✅ | Converts legacy code to modern code |
| **Sparky** | action | ❌ | ❌ | ✅ | Converts legacy spark code to databricks code |
| **Monica** | action | ❌ | ❌ | ✅ | Planner agent that plans execution of available agents |


## 🔒 Security Considerations

- **API Keys**: Never commit API keys to version control
- **HITL Workflows**: Use human-in-the-loop for sensitive operations
- **Tool Permissions**: Carefully review tool capabilities before approval
- **Input Validation**: All inputs are validated using Pydantic models

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write docstrings for classes and methods
- Test new agents thoroughly before submitting
- Update documentation for new features

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Powered by [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- Orchestrated with [LangGraph](https://github.com/langchain-ai/langgraph)

---

**Made with ❤️ by Binay Kumar Ray**
