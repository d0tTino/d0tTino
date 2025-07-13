# Telemetry Backend

The CLI tools can emit anonymous usage events when `EVENTS_ENABLED` is truthy or
`--analytics` is passed. Events are sent as JSON to `EVENTS_URL` with optional
authorization via `EVENTS_TOKEN`.

## Opt-in Usage

Telemetry is disabled by default. Set `EVENTS_ENABLED=true` in your environment
or pass `--analytics` to individual commands to opt into sending events.

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

## Upload Aggregated Statistics

Use `nsm_upload.py` to compute weekly totals and send them to `EVENTS_URL`:

```bash
python scripts/nsm_upload.py events.json
```

Provide a path or URL with raw NDJSON events. The script aggregates successful
`ai-do` runs per developer using `nsm_stats.aggregate_successful_runs()` and
posts the resulting JSON to `EVENTS_URL`. Authentication via `EVENTS_TOKEN` is
supported just like `record_event`.

## Tracking the North Star Metric

Each call to `record_event()` writes a JSON payload to `EVENTS_URL`. The
`nsm_stats.aggregate_successful_runs()` helper groups these raw events by
hashed developer ID and ISO week, counting only entries where `exit_code` is
`0`. Summing these weekly totals yields the “successful automated tasks per
active developer per week” metric. `nsm_upload.py` can read NDJSON logs or fetch
them from `EVENTS_URL`, compute the totals, and post the aggregated JSON back to
the server.
