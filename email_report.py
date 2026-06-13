import smtplib
import sqlite3
import os
import csv
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta

DATA_PATH = os.environ.get('DATA_PATH', os.path.join(os.path.dirname(__file__), 'data'))
DB_PATH = os.path.join(DATA_PATH, 'database.sqlite')

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def generate_report_text() -> str:
    conn = sqlite3.connect(DB_PATH)
    try:
        import pandas as pd
        df = pd.read_sql("SELECT * FROM kpis ORDER BY date DESC LIMIT 7", conn)
    except:
        df = None
    conn.close()

    lines = []
    lines.append("=" * 50)
    lines.append("REPORT SEMANAL DE KPIs - REPORTS KPI + SOP OPTIMIZER")
    lines.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append("=" * 50)
    lines.append("")

    if df is not None and not df.empty:
        last = df.iloc[0]
        lines.append(f"📊 KPIs da Semana:")
        lines.append(f"   Total Tickets: {last['total_tickets']}")
        lines.append(f"   Reopening Rate: {last['reopening_rate']:.1%}")
        lines.append(f"   CSAT Médio: {last['avg_csat']:.1f}")
        lines.append(f"   TMA Médio: {last['avg_tma']:.0f} min")
    else:
        lines.append("Nenhum KPI registrado ainda.")
    lines.append("")
    lines.append("💡 Dica: Faça upload de dados no dashboard para gerar análises.")
    lines.append("=" * 50)
    return "\n".join(lines)

def generate_csv_attachment() -> bytes:
    conn = sqlite3.connect(DB_PATH)
    try:
        import pandas as pd
        df = pd.read_sql("SELECT * FROM kpis ORDER BY date DESC", conn)
    except:
        df = None
    conn.close()

    output = io.BytesIO()
    if df is not None and not df.empty:
        df.to_csv(output, index=False, encoding='utf-8')
    else:
        output.write(b"date,total_tickets,reopening_rate,avg_csat,avg_tma\n")
    output.seek(0)
    return output.read()

def send_weekly_report(to_email: str, smtp_user: str = None, smtp_pass: str = None):
    if not to_email:
        print("No recipient email configured.")
        return

    msg = MIMEMultipart()
    msg['Subject'] = f"📊 Report Semanal KPIs - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = smtp_user or "reports@maitedasilva.com.br"
    msg['To'] = to_email

    body = generate_report_text()
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    csv_data = generate_csv_attachment()
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(csv_data)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment',
                          filename=f"kpis_{datetime.now().strftime('%Y%m%d')}.csv")
    msg.attach(attachment)

    if smtp_user and smtp_pass:
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            print(f"Report sent to {to_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")
    else:
        print(f"[DRY RUN] Email would be sent to {to_email}")
        print(body)

if __name__ == "__main__":
    import sys
    recipient = sys.argv[1] if len(sys.argv) > 1 else "ola@maitedasilva.com.br"
    send_weekly_report(recipient)
