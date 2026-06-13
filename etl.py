import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'database.sqlite')

def calculate_kpis():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM tickets", conn)
    except:
        print("No tickets table yet. Run with sample data on first deploy.")
        conn.close()
        return

    if df.empty:
        print("No tickets to process.")
        conn.close()
        return

    today = datetime.now().date()
    df['created_at'] = pd.to_datetime(df['created_at'])
    last_30d = df[df['created_at'] >= pd.Timestamp(today - timedelta(days=30))]

    kpi = {
        'date': today.isoformat(),
        'total_tickets': len(last_30d),
        'reopening_rate': float(last_30d['reopening'].mean()) if 'reopening' in last_30d.columns else 0,
        'avg_csat': float(last_30d['csat'].mean()) if 'csat' in last_30d.columns else 0,
        'avg_tma': float(last_30d['tma_minutes'].mean()) if 'tma_minutes' in last_30d.columns else 0,
    }

    conn.execute('''
        INSERT INTO kpis (date, total_tickets, reopening_rate, avg_csat, avg_tma)
        VALUES (?, ?, ?, ?, ?)
    ''', (kpi['date'], kpi['total_tickets'], kpi['reopening_rate'],
          kpi['avg_csat'], kpi['avg_tma']))
    conn.commit()
    conn.close()
    print(f"KPIs updated for {today}: {kpi}")

if __name__ == "__main__":
    calculate_kpis()
