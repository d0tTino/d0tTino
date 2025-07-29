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
   The API accepts objects with a `payload` field containing the event JSON.
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

Example environment configuration:

```bash
export EVENTS_URL=https://example.supabase.co/rest/v1/events
export EVENTS_TOKEN=your-anon-key
export EVENTS_ENABLED=true
export NSM_URL=https://example.supabase.co/rest/v1/nsm
```

### Environment Variables

- `EVENTS_URL` – Supabase REST endpoint to insert rows into the `events` table.
- `EVENTS_TOKEN` – API key (anon or service role) used for authentication.
- `EVENTS_ENABLED` – when set to a truthy value, enables event recording.
- `NSM_URL` – endpoint used by `nsm_upload.py` to store weekly aggregates.

## Upload Aggregated Statistics

Use `nsm_upload.py` to compute weekly totals and send them to `NSM_URL`:

```bash
python scripts/nsm_upload.py events.json
```

Provide a path or URL with raw NDJSON events. The script aggregates successful
`ai-do` runs per developer using `nsm_stats.aggregate_successful_runs()` and
posts the resulting JSON to `NSM_URL`. Authentication via `EVENTS_TOKEN` is
supported just like `record_event`.

## Tracking the North Star Metric

Each call to `record_event()` writes a JSON payload to `EVENTS_URL`. The
`nsm_stats.aggregate_successful_runs()` helper groups these raw events by
hashed developer ID and ISO week, counting only entries where `exit_code` is
`0`. Summing these weekly totals yields the “successful automated tasks per
active developer per week” metric. `nsm_upload.py` can read NDJSON logs or fetch
them from `EVENTS_URL`, compute the totals, and post the aggregated JSON back to
the server.

## Viewing Basic Stats

Run `ai-cli stats` to retrieve events from `EVENTS_URL` and print a short
summary:

```bash
EVENTS_URL=https://example.com ai-cli stats
```

The command displays the total number of recorded runs, the overall success
rate, and the average latency in milliseconds.

## Viewing Aggregated Metrics

Run `ai-cli metrics` to fetch weekly totals of successful `ai-do` runs.
Use `--aggregates-url` (or set `NSM_URL`) to read precomputed totals:

```bash
NSM_URL=https://example.com/nsm ai-cli metrics --aggregates-url https://example.com/nsm
```

The output mirrors `nsm_stats.py` and prints `developer,week,count` CSV rows.

## Streaming Events with NATS

Set `NATS_URL` to the address of your NATS server and choose a subject with `NATS_SUBJECT`. Export `EVENTS_ENABLED=true` or pass `--analytics` to send events.

```bash
export NATS_URL=nats://127.0.0.1:4222
export NATS_SUBJECT=telemetry.events
export EVENTS_ENABLED=true
ai-cli do "task" --analytics --nats-url "$NATS_URL"
```

