import express from 'express';

const app = express();
const PORT = process.env.PORT || 3001;

app.use(express.json());

const sopDatabase: { pattern: string; suggestion: string }[] = [];

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'mcp-reports' });
});

app.get('/kpis', async (_req, res) => {
  try {
    const sqlite3 = await import('sqlite3');
    const db = new sqlite3.Database('../data/database.sqlite');
    db.all('SELECT * FROM kpis ORDER BY date DESC LIMIT 30', (err, rows) => {
      if (err) {
        res.status(500).json({ error: err.message });
        return;
      }
      res.json(rows);
    });
    db.close();
  } catch {
    res.json({ message: 'No data yet', kpis: [] });
  }
});

app.post('/sop/suggest', (req, res) => {
  const { pattern } = req.body;
  if (!pattern) {
    res.status(400).json({ error: 'pattern is required' });
    return;
  }
  const found = sopDatabase.find(s => s.pattern.toLowerCase().includes(pattern.toLowerCase()));
  if (found) {
    res.json({ pattern: found.pattern, suggestion: found.suggestion });
  } else {
    res.json({ message: 'No suggestion found for this pattern', pattern });
  }
});

app.post('/sop/add', (req, res) => {
  const { pattern, suggestion } = req.body;
  if (!pattern || !suggestion) {
    res.status(400).json({ error: 'pattern and suggestion are required' });
    return;
  }
  sopDatabase.push({ pattern, suggestion });
  res.json({ message: 'SOP suggestion added', total: sopDatabase.length });
});

app.post('/etl', async (_req, res) => {
  try {
    const { execSync } = await import('child_process');
    execSync('python ../etl.py', { stdio: 'inherit' });
    res.json({ message: 'ETL triggered successfully' });
  } catch (error) {
    const err = error as Error;
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`MCP Reports Server running on port ${PORT}`);
});
