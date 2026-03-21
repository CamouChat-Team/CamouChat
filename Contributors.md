# Contributors Guide

Welcome to CamouChat! We are excited that you want to contribute. This guide will help you set up your development environment and understand the workflow.

## Project Vision

CamouChat aims to provide a reliable, stealth-aware automation SDK. Our focus is on long-term maintainability and extensible architecture.

## Getting Started

Follow these steps to set up your working directory and install the necessary dependencies.

### 1. Prerequisites
- Python 3.9+
- Git

### 2. Fork and Clone
1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/CamouChat.git
   cd CamouChat
   ```

### 3. Installation

We support both `uv` (recommended for speed and reliability) and standard `pip`.

#### A. Using `uv` (Recommended)
`uv` is an extremely fast Python package and project manager.

```bash
# Initialize the project and virtual environment
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Fetch necessary browser binaries (Camoufox)
python -m camoufox fetch
```

#### B. Using `pip`
If you prefer standard tools:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies and dev-tools
pip install -e .
pip install -r requirements-dev.txt

# Fetch necessary browser binaries (Camoufox)
python -m camoufox fetch
```

### 4. Verified Setup (Checked Installations)
To ensure everything is working correctly, run the tests:

```bash
# If using uv
uv run pytest

# If using pip
pytest
```

## Development Workflow

1. **Synchronize**: Always rebase your branch from the upstream main before starting new work.
2. **Implement**: Write your code.
3. **Lint**: Run mandatory checks (`black`, `ruff`, `mypy`, `deptry`).
4. **Test**: Especially for web selector changes.
5. **PR**: Open a PR with a clear description and mention the issue it closes.

Thank you for helping us build a better automation SDK!
