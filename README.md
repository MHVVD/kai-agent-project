# KAI: Multi-Agent Personal Assistant

KAI is a hackathon prototype of a personal assistant built from four cooperating
[Fetch.ai uAgents](https://fetch.ai/docs). Each agent owns one area of the user's life
and they share a symbolic knowledge base written in [MeTTa](https://metta-lang.dev/)
(OpenCog Hyperon). A coordinating agent takes chat commands and sends periodic
summaries by email.

## Agents

| Agent | Responsibility |
|-------|----------------|
| `kai_mind` | Coordinator. Handles user chat, routes commands to the other agents, logs activity and emails a holistic progress report (with a matplotlib chart). |
| `kai_health` | Builds a weekly wellness plan with an LLM from the user's goals and preferences in the knowledge base, and schedules mindfulness sessions in Google Calendar. |
| `kai_career` | Tracks learning goals, drafts a tailored CV and cover letter for job leads, and schedules study blocks. |
| `kai_finance` | Logs expenses, watches budgets and a savings goal, and checks market data for investment ideas. |

The agents run together in a single uAgents `Bureau` (`main.py`) and talk to each other
with typed messages defined in `models.py`. `bureau_app.py` is a single-file version of
the same system for hosted deployment.

## Tech stack

Python · uAgents · MeTTa / Hyperon · ASI:One LLM API · Google Calendar API · SMTP · yfinance · matplotlib

## Project layout

```
agents/        one module per agent
services/      LLM, email, calendar and finance integrations
knowledge/     MeTTa user model shared by the agents
protocols/     chat protocol used by kai_mind
models.py      inter-agent message schemas
main.py        starts all agents in one Bureau
```

## Running locally

```bash
pip install -r requirements.txt

export ASI_ONE_API_KEY=...        # ASI:One LLM API key
export EMAIL_ADDRESS=...          # sender address (Gmail)
export EMAIL_PASSWORD=...         # Gmail app password
export KAI_USER_EMAIL=...         # where reports are sent

python main.py
```

Google Calendar access needs an OAuth `credentials.json` in the project root. A
`token.json` is created on first run. Both files are git-ignored.

## Status

This was built in a hackathon and is a prototype. The agent wiring, knowledge base,
chat routing, budget tracking and email reports work. Some handlers are still stubs
and are marked `TODO` in the code: turning the wellness plan into calendar events,
annual check-up reminders, and job-board scraping.
