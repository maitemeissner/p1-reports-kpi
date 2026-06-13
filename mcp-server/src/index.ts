import express from 'express';
import Database from 'better-sqlite3';
import path from 'path';
import { execSync } from 'child_process';

const app = express();
const PORT = process.env.PORT || 3001;
const DATA_PATH = process.env.DATA_PATH || path.join(__dirname, '..', 'data');

app.use(express.json());

function getDb() {
  const dbPath = path.join(DATA_PATH, 'database.sqlite');
  return new Database(dbPath);
}

const sopDatabase: { pattern: string; suggestion: string }[] = [];

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'mcp-reports' });
});

app.get('/kpis', (_req, res) => {
  try {
    const db = getDb();
    const rows = db.prepare('SELECT * FROM kpis ORDER BY date DESC LIMIT 30').all();
    db.close();
    res.json(rows);
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

app.post('/etl', (_req, res) => {
  try {
    execSync('python etl.py', { cwd: path.join(__dirname, '..'), stdio: 'inherit' });
    res.json({ message: 'ETL triggered successfully' });
  } catch (error) {
    const err = error as Error;
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`MCP Reports Server running on port ${PORT}`);
});
