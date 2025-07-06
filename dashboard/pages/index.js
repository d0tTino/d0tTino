import { useEffect, useState } from 'react';

export default function Home() {
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [palette, setPalette] = useState('');
  const [status, setStatus] = useState('');
  const [goal, setGoal] = useState('');
  const [steps, setSteps] = useState([]);
  const [logs, setLogs] = useState('');

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then(setHealth)
      .catch(() => setHealth({ status: 'error' }));

    fetch('/api/stats')
      .then((res) => res.json())
      .then(setStats)
      .catch(() => {});
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
      .then((data) => setSteps(data.steps || []));
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
        <button onClick={sendPrompt}>Send</button>
        {response && <p>{response}</p>}
      </div>
      <div>
        <input value={palette} onChange={(e) => setPalette(e.target.value)} placeholder="palette" />
        <button onClick={applyPalette}>Apply</button>
        {status && <p>{status}</p>}
      </div>
      <div>
        <input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="goal" />
        <button onClick={getPlan}>Plan</button>
        <button onClick={runExec}>Run</button>
        {steps.length > 0 && (
          <pre>{steps.join('\n')}</pre>
        )}
        {logs && (
          <pre>{logs}</pre>
        )}
      </div>
    </div>
  );
}
