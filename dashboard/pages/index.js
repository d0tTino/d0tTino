import { useEffect, useState } from 'react';

export default function Home() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/health')
      .then((res) => res.json())
      .then(setHealth)
      .catch(() => setHealth({ status: 'error' }));
  }, []);

  return (
    <div>
      <h1>UME Dashboard</h1>
      {health && <p>API status: {health.status}</p>}
    </div>
  );
}
