# Email-Assistant

Fetch job-related emails labeled as `Zapped`, extract structured info using a local LLM (Ollama), and add rows to a Notion database.

## What this does
- Watches your Gmail for messages that were newly labeled with `Zapped`.
- Sends each newly labeled email to an LLM to extract:
  - Company Name
  - Application Date (email received date)
  - Role
- Creates a row in your Notion database with those fields.

First run initializes a Gmail history checkpoint and does not process previously labeled emails. After that, only newly labeled emails are processed.

## Prerequisites
- Python 3.11+
- [Poetry](https://python-poetry.org/)
- [Ollama](https://ollama.ai/) running locally (e.g., `ollama serve`)
- A Notion database with properties named exactly:
  - `Company Name` (title)
  - `Application Date` (date)
  - `Role` (rich_text)
- A Gmail API OAuth client `credentials.json` in the project root (first run opens a browser to authorize and creates `token.json`).

## Setup

### 📦 Install dependencies (keep these commands)
```bash
poetry install
```

For tox testing but avoiding conflict with dev dependencies, run the following command:
```bash
 pip install pipx
 pipx ensurepath
 pipx install tox
```

### ✅ Pre-commit hooks (optional but recommended)
```bash
pre-commit install
```

### 🧪 Run checks with Tox (optional)
```bash
tox
```

### 🔑 Configure environment
Create a `.env` file in the project root (or set env vars another way):
```
NOTION_API_KEY=your_notion_integration_secret
NOTION_DATABASE_ID=your_database_id

# Optional, defaults shown
GMAIL_LABEL_TO_POLL=Zapped
POLLING_INTERVAL_SECONDS=300
```

Place your Gmail OAuth client secrets as `credentials.json` in the project root.

### 🤖 Pull a small local model
Choose any local model you have. The code defaults to `qwen2.5:3b` in Ollama. Example:
```bash
ollama pull qwen3:4b
```

## Run the service
```bash
poetry run python -m email_assistant.main
```

You should see logs like:
```
Starting Gmail to Notion Automation Service.
Polling every 300 seconds. Press Ctrl+C to stop.
Polling for newly labeled emails with label: 'Zapped'
```

When you apply the `Zapped` label to an email in Gmail, the service will:
1) detect it via Gmail History API, 2) extract fields via Ollama, 3) add a row to Notion.

## Notes
- The service stores a Gmail checkpoint in `gmail_state.json` to avoid reprocessing.
- If your Notion property names differ, update them in `python/email_assistant/services/notion_service.py`.
- If you want a different model, change it in `python/email_assistant/services/llm_service.py`.
