import { useCallback, useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";

type TelemetryStatus = {
  enabled: boolean;
  endpoint: string | null;
};

type ActionDetails = {
  message: string;
  telemetry?: TelemetryStatus | null;
  details?: unknown;
};

type LogEntry = {
  timestamp: number;
  action: string;
  payload?: string | null;
  exit_code: number;
};

type LogSnapshot = {
  entries: LogEntry[];
  path: string;
};

type ActionDescriptor = {
  key: string;
  label: string;
  command: string;
  prompt?: string;
  confirm?: boolean;
  danger?: boolean;
};

const ACTIONS: ActionDescriptor[] = [
  { key: "up", label: "Up", command: "cockpit_up" },
  { key: "down", label: "Down", command: "cockpit_down", confirm: true, danger: true },
  {
    key: "new-task",
    label: "New Task",
    command: "cockpit_new_task",
    prompt: "Describe the task to queue",
  },
  {
    key: "inject-context",
    label: "Inject Context",
    command: "cockpit_inject_context",
  },
  {
    key: "research-ingest",
    label: "Research Ingest",
    command: "cockpit_research_ingest",
    prompt: "Provide a source path or URL",
  },
  {
    key: "wishlist-add",
    label: "Wishlist Add",
    command: "cockpit_wishlist_add",
    prompt: "Wishlist entry",
  },
  {
    key: "publish-docs",
    label: "Publish Docs",
    command: "cockpit_publish_docs",
    confirm: true,
    danger: true,
  },
];

const formatTimestamp = (value: number): string => {
  const date = new Date(value * 1000);
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
};

const telemetryBadge = (telemetry: TelemetryStatus | null) => {
  if (!telemetry) {
    return <span className="telemetry-indicator off">Telemetry disabled</span>;
  }
  return (
    <span className={`telemetry-indicator ${telemetry.enabled ? "" : "off"}`}>
      {telemetry.enabled ? "Telemetry active" : "Telemetry disabled"}
      {telemetry.endpoint ? ` · ${telemetry.endpoint}` : null}
    </span>
  );
};

const App = (): JSX.Element => {
  const [status, setStatus] = useState<string>("Ready");
  const [telemetry, setTelemetry] = useState<TelemetryStatus | null>(null);
  const [details, setDetails] = useState<unknown>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logPath, setLogPath] = useState<string>("");
  const [busyKey, setBusyKey] = useState<string | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      const snapshot = await invoke<LogSnapshot>("cockpit_log_snapshot", { limit: 200 });
      setLogs(snapshot.entries);
      setLogPath(snapshot.path);
    } catch (error) {
      setStatus(`Log refresh failed: ${error}`);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
    const handle = setInterval(fetchLogs, 4000);
    return () => clearInterval(handle);
  }, [fetchLogs]);

  const handleAction = useCallback(
    async (action: ActionDescriptor) => {
      const args: Record<string, unknown> = {};
      if (action.command === "cockpit_inject_context") {
        const jobId = window.prompt("Job identifier") ?? null;
        if (!jobId) {
          return;
        }
        const context = window.prompt(action.prompt ?? "Context payload") ?? null;
        if (!context) {
          return;
        }
        args.jobId = jobId;
        args.context = context;
      } else {
        let payload: string | null = null;
        if (action.prompt) {
          payload = window.prompt(action.prompt) ?? null;
          if (!payload) {
            return;
          }
        }
        if (payload) {
          args[
            action.command === "cockpit_new_task"
              ? "task"
              : action.command === "cockpit_research_ingest"
              ? "path"
              : action.command === "cockpit_wishlist_add"
              ? "item"
              : "payload"
          ] = payload;
        }
      }
      if (action.confirm) {
        const confirmed = window.confirm(`Confirm ${action.label}? This may be disruptive.`);
        if (!confirmed) {
          return;
        }
      }

      try {
        setBusyKey(action.key);
        setStatus(`Running ${action.label}…`);
        if (action.confirm) {
          args.confirm = true;
        }
        const response = await invoke<ActionDetails>(action.command, args);
        setStatus(response.message);
        setTelemetry(response.telemetry ?? null);
        setDetails(response.details ?? null);
        fetchLogs();
      } catch (error) {
        setStatus(`Error: ${error}`);
      } finally {
        setBusyKey(null);
      }
    },
    [fetchLogs],
  );

  const renderedDetails = useMemo(() => {
    if (!details) {
      return "No additional details";
    }
    try {
      return JSON.stringify(details, null, 2);
    } catch (error) {
      return String(details);
    }
  }, [details]);

  return (
    <main>
      <header>
        <h1>d0tTino Cockpit</h1>
        <p>Trigger automation flows and review live telemetry from the canonical CLI handlers.</p>
        {telemetryBadge(telemetry)}
      </header>

      <section>
        <h2>Actions</h2>
        <div className="button-grid">
          {ACTIONS.map((action) => (
            <button
              key={action.key}
              className={action.danger ? "danger" : ""}
              onClick={() => handleAction(action)}
              disabled={busyKey !== null}
            >
              {action.label}
            </button>
          ))}
        </div>
      </section>

      <section className="status-card">
        <h2>Status</h2>
        <div>{status}</div>
        <pre>{renderedDetails}</pre>
      </section>

      <section>
        <h2>Live Cockpit Log</h2>
        <p>{logPath ? `Streaming from ${logPath}` : "No log file detected"}</p>
        <div className="log-stream">
          {logs.length === 0 ? (
            <div className="log-entry">No log entries yet.</div>
          ) : (
            logs
              .slice()
              .reverse()
              .map((entry, index) => (
                <div className="log-entry" key={`${entry.timestamp}-${index}`}>
                  <div className="meta">
                    <span>{entry.action}</span>
                    <span>{formatTimestamp(entry.timestamp)}</span>
                  </div>
                  <div className="payload">
                    Exit code: {entry.exit_code}
                    {entry.payload ? ` · Payload: ${entry.payload}` : ""}
                  </div>
                </div>
              ))
          )}
        </div>
      </section>
    </main>
  );
};

export default App;
