# GH-emails-mxf

Hybrid Outlook email triage app for Greenhouse. A Windows Python agent reads your Outlook inbox, triages emails by priority, and syncs results to Supabase. A mobile-first Next.js web app (hosted on Vercel) displays the triage and lets you queue actions (archive, open, mark read) that the Windows agent executes through Outlook COM.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Windows Machine                                             │
│                                                              │
│  ┌──────────────────────────────────┐                        │
│  │  /agent  (Python)                │                        │
│  │  - Reads Outlook via COM         │                        │
│  │  - Rule-based triage (rules.py)  │ ──writes──▶  Supabase │
│  │  - Optional AI triage (Claude)   │ ◀──reads───  (bridge) │
│  │  - Executes action_queue items   │                        │
│  │  - Updates heartbeat             │                        │
│  └──────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            │
                       Supabase
                   (emails, action_queue,
                    agent_heartbeat, triage_runs)
                            │
┌─────────────────────────────────────────────────────────────┐
│  Vercel (Next.js)                                            │
│                                                              │
│  /web                                                        │
│  - Mobile-first dashboard                                    │
│  - P0/P1/P2/P3 priority tabs                                 │
│  - Action buttons → action_queue rows                        │
│  - Agent online/offline indicator                            │
└─────────────────────────────────────────────────────────────┘
```

## Supabase Setup

1. Open your Supabase project named **greenhouse** at https://supabase.com.
2. Go to **SQL Editor** and run the migration file:
   ```
   supabase/migrations/001_initial.sql
   ```
3. Collect your project credentials:
   - `SUPABASE_URL` — from Project Settings → API → Project URL
   - `SUPABASE_SERVICE_ROLE_KEY` — from Project Settings → API → service_role key (keep secret)
   - `SUPABASE_ANON_KEY` — from Project Settings → API → anon key (safe for browser)

## Local Windows Agent Setup

### Prerequisites
- Windows 10/11
- Python 3.10+
- Microsoft Outlook installed and signed in
- A Supabase account with the **greenhouse** project

### Install

```bat
cd agent
pip install -r requirements.txt
```

### Configure

```bat
copy .env.example .env
notepad .env
```

Fill in your values:

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (server-side only) |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `TRIAGE_USE_AI` | `false` (rule-based) or `true` (Claude for ambiguous emails) |
| `SYNC_INTERVAL_SECONDS` | How often to poll (default: 30) |

### Run

```bat
run_agent.bat
```

Or directly:

```bat
cd agent
python main.py
```

The agent runs continuously. Press `Ctrl+C` to stop.

## Vercel Deploy Setup

### Prerequisites
- Node.js 18+
- Vercel CLI or GitHub integration

### Local dev

```bash
cd web
npm install
cp .env.example .env.local
# fill in .env.local
npm run dev
```

### Environment Variables (set in Vercel dashboard)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |
| `NEXT_PUBLIC_APP_NAME` | `GH-emails-mxf` |
| `APP_PASSWORD` | Simple access password for the MVP auth gate |

### Deploy

Push to GitHub and connect the repo in the Vercel dashboard. Set the **Root Directory** to `web`.

## Environment Variables Summary

### agent/.env
```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
ANTHROPIC_API_KEY=sk-ant-...
TRIAGE_USE_AI=false
SYNC_INTERVAL_SECONDS=30
```

### web/.env.local
```
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_APP_NAME=GH-emails-mxf
APP_PASSWORD=changeme
```

## How to Run the Agent

1. Make sure Outlook is open and signed in.
2. Run `agent\run_agent.bat`.
3. The agent will immediately scan your inbox, triage emails, and sync to Supabase.
4. It then loops every `SYNC_INTERVAL_SECONDS` seconds.
5. Logs are written to `agent\logs\agent.log`.

## How to Test Archive / Open Actions

1. Open the web app (local dev or Vercel).
2. Find an email in the dashboard.
3. Click **Archive** — this creates a `pending` row in `action_queue`.
4. Within one sync cycle the Windows agent picks it up, archives the email in Outlook, and marks the action `completed`.
5. Click **Open on Work Computer** — the agent opens the email in Outlook on your Windows machine.

## Known Limitations

- The agent must run on a Windows machine with Outlook installed. It is not a cloud service.
- Outlook COM requires Outlook to be running and signed in.
- Archive folder detection may vary by Outlook/Exchange configuration. The agent tries multiple strategies.
- The MVP auth gate (`APP_PASSWORD`) is a simple shared password. For production, replace with Supabase Auth.
- AI triage (`TRIAGE_USE_AI=true`) sends only sender, subject, and a short body preview to Claude — never full email bodies.
- `move_to_folder` action requires a `folder_name` key in the action payload JSON.
- The agent heartbeat is updated every cycle; the web UI considers the agent offline after 90 seconds without a heartbeat.
