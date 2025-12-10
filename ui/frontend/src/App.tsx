import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

type Telemetry = {
  enabled: boolean;
  endpoint?: string | null;
};

type WhoAmI = {
  endpoints?: Record<string, string>;
  log_path?: string;
  telemetry?: Telemetry;
};

type CliOutput = {
  stdout: string;
  stderr: string;
  status: number;
  json?: unknown;
};

type LogLinePayload = {
  line: string;
  stream: string;
};

const parseMaybeJson = (value: unknown): string => {
  if (value === undefined || value === null) return "No output yet";
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return JSON.stringify(parsed, null, 2);
    } catch (error) {
      return value;
    }
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch (error) {
    return String(value);
  }
};

const telemetryBadge = (telemetry: Telemetry | undefined): JSX.Element | null => {
  if (!telemetry) return null;
  return (
    <span className={`telemetry-indicator ${telemetry.enabled ? "" : "off"}`}>
      {telemetry.enabled ? "Telemetry active" : "Telemetry disabled"}
      {telemetry.endpoint ? ` · ${telemetry.endpoint}` : null}
    </span>
  );
};

const App = (): JSX.Element => {
  const [confirm, setConfirm] = useState(false);
  const [dryRun, setDryRun] = useState(false);
  const [service, setService] = useState("");
  const [taskId, setTaskId] = useState("");
  const [taskPayload, setTaskPayload] = useState("");
  const [taskSignalName, setTaskSignalName] = useState("");
  const [taskLink, setTaskLink] = useState("");
  const [taskNote, setTaskNote] = useState("");
  const [researchSource, setResearchSource] = useState("");
  const [researchTopic, setResearchTopic] = useState("");
  const [draftTopic, setDraftTopic] = useState("");
  const [draftHint, setDraftHint] = useState("");
  const [draftDoc, setDraftDoc] = useState("");
  const [draftAnchor, setDraftAnchor] = useState("");
  const [draftPrompt, setDraftPrompt] = useState("");
  const [wishlistUrl, setWishlistUrl] = useState("");
  const [wishlistTags, setWishlistTags] = useState("");
  const [financePeriod, setFinancePeriod] = useState("month");
  const [financeMonth, setFinanceMonth] = useState("");
  const [docsTarget, setDocsTarget] = useState("");
  const [docsSite, setDocsSite] = useState("");
  const [docsVersion, setDocsVersion] = useState("");
  const [logService, setLogService] = useState("ume");

  const [status, setStatus] = useState("Ready");
  const [lastCommand, setLastCommand] = useState("-");
  const [cliOutput, setCliOutput] = useState<CliOutput | null>(null);
  const [whoami, setWhoami] = useState<WhoAmI | null>(null);
  const [streamLines, setStreamLines] = useState<string[]>([]);
  const [streaming, setStreaming] = useState(false);

  useEffect(() => {
    invoke<CliOutput>("tino_whoami", { confirm: false, dryRun: false })
      .then((result) => {
        setCliOutput(result);
        if (result.json && typeof result.json === "object") {
          setWhoami(result.json as WhoAmI);
        } else if (result.stdout) {
          try {
            setWhoami(JSON.parse(result.stdout) as WhoAmI);
          } catch (error) {
            setWhoami(null);
          }
        }
      })
      .catch((error) => setStatus(`whoami failed: ${error}`));
  }, []);

  useEffect(() => {
    const unlistenLine = listen<LogLinePayload>("tino-log-line", (event) => {
      setStreamLines((existing) => {
        const next = [...existing, `${event.payload.stream}: ${event.payload.line}`];
        return next.slice(-400);
      });
    });
    const unlistenExit = listen<number>("tino-log-exit", (event) => {
      setStreaming(false);
      setStatus(`Log stream exited with code ${event.payload}`);
    });
    return () => {
      unlistenLine.then((f) => f());
      unlistenExit.then((f) => f());
    };
  }, []);

  const renderCliOutput = useMemo(() => {
    if (!cliOutput) return "No CLI output yet";
    if (cliOutput.json) {
      return parseMaybeJson(cliOutput.json);
    }
    if (cliOutput.stdout.trim().length > 0) {
      return parseMaybeJson(cliOutput.stdout);
    }
    if (cliOutput.stderr.trim().length > 0) {
      return cliOutput.stderr;
    }
    return `Exit code ${cliOutput.status}`;
  }, [cliOutput]);

  const runCommand = async (
    command: string,
    payload: Record<string, unknown>,
    label: string,
  ): Promise<void> => {
    setStatus(`Running ${label}…`);
    setLastCommand(command);
    try {
      const response = await invoke<CliOutput>(command, {
        confirm,
        dryRun,
        ...payload,
      });
      setCliOutput(response);
      setStatus(`Finished ${label} (code ${response.status})`);
      if (command === "tino_whoami" && response.json && typeof response.json === "object") {
        setWhoami(response.json as WhoAmI);
      }
    } catch (error) {
      setStatus(`Error while running ${label}: ${error}`);
    }
  };

  const startLogs = async () => {
    setStreamLines([]);
    setStreaming(true);
    await runCommand("start_log_stream", { service: logService }, "log stream");
  };

  const stopLogs = async () => {
    await runCommand("stop_log_stream", {}, "stop log stream");
    setStreaming(false);
  };

  return (
    <main>
      <header>
        <h1>d0tTino Cockpit</h1>
        <p>Drive the Typer-based tino CLI directly from the desktop shell.</p>
        {telemetryBadge(whoami?.telemetry)}
        {whoami?.endpoints ? (
          <div className="endpoints">
            {Object.entries(whoami.endpoints).map(([key, value]) => (
              <span key={key} className="endpoint-pill">
                {key}: {value}
              </span>
            ))}
          </div>
        ) : null}
      </header>

      <section className="toggles">
        <label>
          <input type="checkbox" checked={confirm} onChange={(e) => setConfirm(e.target.checked)} />
          Require confirmation
        </label>
        <label>
          <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} />
          Dry-run mode
        </label>
        <button onClick={() => runCommand("tino_whoami", {}, "whoami")}>Reload endpoints</button>
      </section>

      <section className="grid">
        <div className="card">
          <h2>Stack controls</h2>
          <label className="field">
            <span>Service (optional)</span>
            <input
              placeholder="api"
              value={service}
              onChange={(e) => setService(e.target.value)}
            />
          </label>
          <div className="button-row">
            <button onClick={() => runCommand("tino_start", { service }, "start stack")}>
              Start
            </button>
            <button
              className="danger"
              onClick={() => runCommand("tino_stop", { service }, "stop stack")}
            >
              Stop
            </button>
          </div>
        </div>

        <div className="card">
          <h2>Tasks</h2>
          <label className="field">
            <span>Task ID</span>
            <input value={taskId} onChange={(e) => setTaskId(e.target.value)} />
          </label>
          <label className="field">
            <span>Payload (JSON)</span>
            <input
              placeholder='{"priority": "high"}'
              value={taskPayload}
              onChange={(e) => setTaskPayload(e.target.value)}
            />
          </label>
          <button
            onClick={() => runCommand("tino_task_run", { task: taskId, payload: taskPayload || null }, "task run")}
          >
            Run task
          </button>
          <div className="field two-column">
            <label>
              <span>Signal</span>
              <input value={taskSignalName} onChange={(e) => setTaskSignalName(e.target.value)} />
            </label>
            <label>
              <span>Link</span>
              <input value={taskLink} onChange={(e) => setTaskLink(e.target.value)} />
            </label>
          </div>
          <label className="field">
            <span>Note</span>
            <input value={taskNote} onChange={(e) => setTaskNote(e.target.value)} />
          </label>
          <button
            className="danger"
            onClick={() =>
              runCommand(
                "tino_task_signal",
                {
                  taskId,
                  signal: taskSignalName || null,
                  link: taskLink || null,
                  note: taskNote || null,
                },
                "task signal",
              )
            }
          >
            Send signal
          </button>
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <h2>Research ingest</h2>
          <label className="field">
            <span>Source</span>
            <input
              placeholder="https://example.com"
              value={researchSource}
              onChange={(e) => setResearchSource(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Topic (optional)</span>
            <input value={researchTopic} onChange={(e) => setResearchTopic(e.target.value)} />
          </label>
          <button
            onClick={() =>
              runCommand(
                "tino_research_ingest",
                { source: researchSource, topic: researchTopic || null },
                "research ingest",
              )
            }
          >
            Ingest
          </button>
        </div>

        <div className="card">
          <h2>Research draft</h2>
          <div className="field two-column">
            <label>
              <span>Topic</span>
              <input value={draftTopic} onChange={(e) => setDraftTopic(e.target.value)} />
            </label>
            <label>
              <span>Doc</span>
              <input value={draftDoc} onChange={(e) => setDraftDoc(e.target.value)} />
            </label>
          </div>
          <div className="field two-column">
            <label>
              <span>Anchor</span>
              <input value={draftAnchor} onChange={(e) => setDraftAnchor(e.target.value)} />
            </label>
            <label>
              <span>Prompt override</span>
              <input value={draftPrompt} onChange={(e) => setDraftPrompt(e.target.value)} />
            </label>
          </div>
          <label className="field">
            <span>Hints (JSON)</span>
            <input value={draftHint} onChange={(e) => setDraftHint(e.target.value)} />
          </label>
          <button
            onClick={() =>
              runCommand(
                "tino_research_draft",
                {
                  topic: draftTopic || null,
                  hint: draftHint || null,
                  doc: draftDoc || null,
                  anchor: draftAnchor || null,
                  prompt: draftPrompt || null,
                },
                "research draft",
              )
            }
          >
            Draft
          </button>
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <h2>Wishlist</h2>
          <label className="field">
            <span>URL</span>
            <input value={wishlistUrl} onChange={(e) => setWishlistUrl(e.target.value)} />
          </label>
          <label className="field">
            <span>Tags (comma separated)</span>
            <input value={wishlistTags} onChange={(e) => setWishlistTags(e.target.value)} />
          </label>
          <button
            onClick={() =>
              runCommand(
                "tino_wishlist_add",
                { url: wishlistUrl, tags: wishlistTags || null },
                "wishlist add",
              )
            }
          >
            Add entry
          </button>
        </div>

        <div className="card">
          <h2>Finance snapshot</h2>
          <div className="field two-column">
            <label>
              <span>Period</span>
              <select value={financePeriod} onChange={(e) => setFinancePeriod(e.target.value)}>
                <option value="month">month</option>
                <option value="quarter">quarter</option>
                <option value="year">year</option>
              </select>
            </label>
            <label>
              <span>Month (optional)</span>
              <input
                placeholder="2024-03"
                value={financeMonth}
                onChange={(e) => setFinanceMonth(e.target.value)}
              />
            </label>
          </div>
          <button
            onClick={() =>
              runCommand(
                "tino_finance_snapshot",
                { period: financePeriod, month: financeMonth || null },
                "finance snapshot",
              )
            }
          >
            Snapshot
          </button>
        </div>

        <div className="card">
          <h2>Docs publish</h2>
          <label className="field">
            <span>Target</span>
            <input value={docsTarget} onChange={(e) => setDocsTarget(e.target.value)} />
          </label>
          <div className="field two-column">
            <label>
              <span>Site</span>
              <input value={docsSite} onChange={(e) => setDocsSite(e.target.value)} />
            </label>
            <label>
              <span>Version</span>
              <input value={docsVersion} onChange={(e) => setDocsVersion(e.target.value)} />
            </label>
          </div>
          <button
            className="danger"
            onClick={() =>
              runCommand(
                "tino_docs_publish",
                { target: docsTarget || null, site: docsSite || null, version: docsVersion || null },
                "docs publish",
              )
            }
          >
            Publish
          </button>
        </div>
      </section>

      <section className="status-card">
        <h2>Status</h2>
        <div>Mode: {confirm ? "confirm" : "preview"}{dryRun ? " · dry-run" : ""}</div>
        <div>Last command: {lastCommand}</div>
        <div>Message: {status}</div>
        <pre>{renderCliOutput}</pre>
      </section>

      <section>
        <h2>Streaming logs</h2>
        <div className="field two-column">
          <label>
            <span>Service</span>
            <input value={logService} onChange={(e) => setLogService(e.target.value)} />
          </label>
          <div className="button-row">
            <button onClick={startLogs} disabled={streaming}>
              Start
            </button>
            <button onClick={stopLogs} className="danger" disabled={!streaming}>
              Stop
            </button>
          </div>
        </div>
        <div className="log-stream">
          {streamLines.length === 0 ? (
            <div className="log-entry">No stream output yet.</div>
          ) : (
            streamLines.slice(-200).map((line, index) => (
              <div className="log-entry" key={`${line}-${index}`}>
                {line}
              </div>
            ))
          )}
        </div>
      </section>
    </main>
  );
};

export default App;
