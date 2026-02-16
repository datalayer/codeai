<!--
  ~ Copyright (c) 2025-2026 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

[![Datalayer](https://assets.datalayer.tech/datalayer-25.svg)](https://datalayer.ai)

[![Become a Sponsor](https://img.shields.io/static/v1?label=Become%20a%20Sponsor&message=%E2%9D%A4&logo=GitHub&style=flat&color=1ABC9C)](https://github.com/sponsors/datalayer)

# ✨ Code AI

[![PyPI - Version](https://img.shields.io/pypi/v/codeai)](https://pypi.org/project/codeai)

> A CLI for data analysis that interacts with the Agent Runtimes via AG-UI and ACP protocols.

Code AI is an AI-powered CLI agent built on [Pydantic AI](https://ai.pydantic.dev) that helps with code analysis, Jupyter notebooks, and data science workflows.

<img src="https://images.datalayer.io/products/codeai/codeai_short_cut.gif"/>

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


## Usage

Special commands available in interactive mode:
- `/exit`: Exit the session
- `/markdown`: Show the last response in markdown format
- `/multiline`: Toggle multiline input mode (use Ctrl+D to submit)
- `/cp`: Copy the last response to clipboard

### Launch with Preconfigured Agent

You can launch CodeAI with a specific agent configuration using the `--agent-id` parameter:

```bash
codeai --agent-id codemode-paper/financial-viz
```

Available agent IDs can be found in the [agentspecs repository](https://github.com/datalayer/agentspecs/tree/main/agentspecs/agents). Each agent is optimized for specific tasks and comes with pre-configured tools and capabilities.

**Important:** Before launching an agent, make sure to set the required environment variables for its MCP servers and skills. Check the agent's configuration in the agentspecs repository to see which MCP servers and skills it uses, then refer to:
- [MCP Servers environment variables](https://github.com/datalayer/agentspecs/tree/main/agentspecs/mcp-servers)
- [Skills environment variables](https://github.com/datalayer/agentspecs/tree/main/agentspecs/skills)
- [Environment variables documentation](https://github.com/datalayer/agentspecs/tree/main/agentspecs/envvars)

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
