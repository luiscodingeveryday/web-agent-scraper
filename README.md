# Web Agent Scraper

AI-powered web scraping agent built with a React frontend and a FastAPI backend, designed for autonomous web navigation and data extraction. The agent is specialized in two primary tasks:
1. **Scraping**: Intelligent extraction of structured data from any provided URL.
2. **Summarization**: Generating concise, context-aware summaries of web content using LLMs.

Core agent logic and decision-making workflows are located in the `backend/` directory.

## Architecture Overview

The system consists of two main services orchestrated by Docker:
* **Frontend**: React application built with Vite and TypeScript.
* **Backend**: FastAPI server running Python 3.12, utilizing asynchronous processing for agentic tasks.
* **Agent**: Integrated with Groq (LLM) for decision-making and Playwright for browser automation.



## Tech Stack

* **Backend**: Python 3.12, FastAPI, Pydantic, Ruff (Linting), Pytest.
* **Frontend**: React, TypeScript, Vite, Tailwind CSS.
* **Infrastructure**: Docker, Docker Compose, Makefile, GitHub Actions (CI/CD).
* **Testing**: Pytest, Playwright (E2E), Pytest-Playwright, Unit and End to end testing.
* **AI/LLM**: Groq Cloud API (Llama 3 models).

## Quick Start

### Prerequisites
* Docker and Docker Compose
* Git

### Setup and Execution
1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd web-agent-scraper
    ```

2.  **Configure environment variables**:
    ```bash
    cp .env.example .env
    # Add your GROQ_API_KEY to the .env file
    ```

3.  **Run the application**:
    Using the provided Makefile:
    ```bash
    make start
    ```
    Alternatively, using Docker Compose directly:
    ```bash
    docker-compose up --build -d
    ```

Access the application at: **http://localhost:3000**

## Testing and Quality Assurance

The project includes a comprehensive test suite managed via Makefile commands.

| Command | Scope | Description |

| `make test` | Full Suite | Executes linting, unit tests, and E2E tests. |
| `make test-unit` | Logic | Runs unit tests for backend and agent logic. |
| `make test-e2e` | Integration | Executes end-to-end tests using Playwright. |
| `make lint` | Quality | Performs static analysis using Ruff. |
| `make format` | Style | Automatically formats code according to project standards. |

## Project Structure

```text
├── backend/            # FastAPI source code
├── frontend/           # React + Vite source code
├── tests/              # Test suites
│   ├── unit/           # Backend and Agent unit tests
│   └── e2e/            # Playwright integration tests
├── docker-compose.yml  # Service orchestration
├── Makefile            # Development task automation
├── pyproject.toml      # Project metadata and tool configuration
└── requirements.txt    # Python dependencies