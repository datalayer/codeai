<!--
  ~ Copyright (c) 2025-2026 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

[![Datalayer](https://assets.datalayer.tech/datalayer-25.svg)](https://datalayer.ai)

[![Become a Sponsor](https://img.shields.io/static/v1?label=Become%20a%20Sponsor&message=%E2%9D%A4&logo=GitHub&style=flat&color=1ABC9C)](https://github.com/sponsors/datalayer)

# ✨ CodeAI

[![PyPI - Version](https://img.shields.io/pypi/v/codeai)](https://pypi.org/project/codeai)

> A CLI for data analysis that interacts with the Agent Runtimes via AG-UI and ACP protocols.

Code AI is an AI-powered CLI agent built on [Pydantic AI](https://ai.pydantic.dev/) that helps with code analysis, Jupyter notebooks, and data science workflows.

<img src="https://images.datalayer.io/products/codeai/codeai_short.gif"/>

## Installation

### Via pip

```bash
pip install codeai
```

### From Source

```bash
git clone https://github.com/datalayer/codeai.git
cd codeai
pip install -e .
```

### Quick Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/datalayer/codeai/main/install.sh | bash
```

## Prerequisites

You'll need to set up your OpenAI API key:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Usage

### Interactive Mode

Launch the interactive CLI to chat with Code AI:

```bash
codeai
```

Special commands available in interactive mode:
- `/exit`: Exit the session
- `/markdown`: Show the last response in markdown format
- `/multiline`: Toggle multiline input mode (use Ctrl+D to submit)
- `/cp`: Copy the last response to clipboard

### Single Query Mode

Run a single query from the command line:

```bash
codeai "How do I create a pandas DataFrame?"
```

### Custom Agent

You can customize the agent by importing and modifying it:

```python
from codeai.cli import agent

# Add custom tools or modify behavior
@agent.tool()
def my_custom_tool(data: str) -> str:
    """Custom tool description"""
    return f"Processed: {data}"

# Run the CLI with customizations
agent.to_cli_sync()
```

## Features

- **Data Analysis**: Get help with code review, debugging, and optimization
- **Jupyter Notebooks**: Assistance with notebook workflows and data exploration
- **Data Science**: Support for pandas, numpy, scikit-learn, and other libraries
- **Interactive Chat**: Conversational interface for iterative problem-solving
- **Animated Loading**: Beautiful spinner animation while processing queries
- **Powered by Pydantic AI**: Built on the robust Pydantic AI framework

## Development

Install development dependencies:

```bash
pip install -e ".[test,lint,typing]"
```

Run tests:

```bash
pytest
```

## License

BSD 3-Clause License - see [LICENSE](LICENSE) for details.
