# Supabase Setup

1. Open the **greenhouse** Supabase project at https://supabase.com.
2. Go to **SQL Editor** and paste + run `migrations/001_initial.sql`.
3. Verify tables `emails`, `action_queue`, `agent_heartbeat`, and `triage_runs` were created.

## Credentials

| Key | Where to find it |
|---|---|
| Project URL | Settings → API → Project URL |
| `anon` key | Settings → API → Project API keys → anon public |
| `service_role` key | Settings → API → Project API keys → service_role (secret — never expose in browser) |

## Notes

- The `service_role` key bypasses RLS. Only the Windows agent uses it (server-side, never shipped to the browser).
- The `anon` key is safe for the Next.js browser client because RLS policies restrict writes on `emails` and reads on heartbeat.
- For production, replace the permissive `anon` policies with Supabase Auth user-scoped policies.
