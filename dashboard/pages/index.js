import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';

export default function Home() {
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [palette, setPalette] = useState('');
  const [status, setStatus] = useState('');
  const [goal, setGoal] = useState('');
  const [tasks, setTasks] = useState([]);
  const [logs, setLogs] = useState('');
  const [recipes, setRecipes] = useState([]);
  const [selected, setSelected] = useState('');

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then(setHealth)
      .catch(() => setHealth({ status: 'error' }));

    fetch('/api/stats')
      .then((res) => res.json())
      .then(setStats)
      .catch(() => {});

    if (window && window.__TAURI__) {
      invoke('list_recipes').then(setRecipes).catch(() => {});
      listen('prompt-file', (e) => {
        setPrompt(e.payload);
      }).then((unsub) => {
        return () => {
          unsub();
        };
      });
    }
  }, []);

  const sendPrompt = () => {
    fetch('/api/prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    })
      .then((res) => res.json())
      .then((data) => setResponse(data.response))
      .catch(() => setResponse('error'));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => setPrompt(ev.target.result);
      reader.readAsText(file);
    }
  };

  const applyPalette = () => {
    fetch('/api/palette', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: palette })
    })
      .then(() => setStatus('applied'))
      .catch(() => setStatus('error'));
  };

  const getPlan = () => {
    fetch('/api/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal })
    })
      .then((res) => res.json())
      .then((data) => setTasks(data.steps || []));
  };

  const runExec = () => {
    setLogs('');
    const es = new EventSource(`/api/exec?goal=${encodeURIComponent(goal)}`);
    es.onmessage = (e) => {
      setLogs((prev) => prev + e.data + '\n');
    };
    es.onerror = () => {
      es.close();
    };
  };

  const runRecipe = () => {
    if (!selected || !window.__TAURI__) return;
    invoke('run_recipe', { name: selected, goal })
      .then((out) => setLogs(out))
      .catch(() => setLogs('error'));
  };

  return (
    <div>
      <h1>UME Dashboard</h1>
      {health && <p>API status: {health.status}</p>}
      {stats && (
        <p>
          Queries: {stats.queries}, Memory: {stats.memory}
        </p>
      )}
      <div>
        <input value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="prompt" />
        <div onDrop={handleDrop} onDragOver={(e) => e.preventDefault()} style={{ border: '1px dashed #ccc', padding: '0.5em', marginTop: '0.5em' }}>
          Drag prompt file here
        </div>
        <button onClick={sendPrompt}>Send</button>
        {response && <p>{response}</p>}
      </div>
      <div>
        <input value={palette} onChange={(e) => setPalette(e.target.value)} placeholder="palette" />
        <button onClick={applyPalette}>Apply</button>
        {status && <p>{status}</p>}
      </div>
      {recipes.length > 0 && (
        <div>
          <select value={selected} onChange={(e) => setSelected(e.target.value)}>
            <option value="">Select recipe</option>
            {recipes.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
          <button onClick={runRecipe}>Run Recipe</button>
        </div>
      )}
      <div>
        <input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="goal" />
        <button onClick={getPlan}>Plan</button>
        <button onClick={runExec}>Run</button>
        {tasks.length > 0 && (
          <ul>
            {tasks.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        )}
        {logs && (
          <pre>{logs}</pre>
        )}
      </div>
    </div>
  );
}
