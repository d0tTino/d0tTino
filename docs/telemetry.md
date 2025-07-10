# Telemetry Backend

The CLI tools can emit anonymous usage events when `EVENTS_ENABLED` is truthy or
`--analytics` is passed. Events are sent as JSON to `EVENTS_URL` with optional
authorization via `EVENTS_TOKEN`.

## Local Supabase Setup

1. Install the Supabase CLI:
   ```bash
   npm install -g supabase
   ```
2. Initialize and start a new project:
   ```bash
   supabase init
   supabase start
   ```
3. Create an `events` table:
   ```bash
   supabase db shell <<'SQL'
   create extension if not exists "uuid-ossp";
   create table if not exists events (
       id uuid primary key default uuid_generate_v4(),
       payload jsonb
   );
   SQL
   ```
4. Copy the anonymous API key from `.env` and point the scripts at the REST
   endpoint:
   ```bash
   export EVENTS_URL=http://localhost:54321/rest/v1/events
   export EVENTS_TOKEN=$(grep ANON_KEY .env | cut -d '=' -f2)
   ```

Events posted to `EVENTS_URL` will be stored in the `events` table.

Hosted Supabase projects work the same way. Use the project's REST URL and anon
or service key for `EVENTS_URL` and `EVENTS_TOKEN`.

With `EVENTS_URL` and `EVENTS_TOKEN` set, enable analytics globally by exporting
`EVENTS_ENABLED=true` or pass `--analytics` to individual commands.
