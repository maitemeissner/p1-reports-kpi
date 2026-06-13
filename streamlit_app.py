import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import os
import json

DATA_PATH = os.environ.get('DATA_PATH', os.path.join(os.path.dirname(__file__), 'data'))
DB_PATH = os.path.join(DATA_PATH, 'database.sqlite')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT,
            category TEXT,
            status TEXT,
            csat REAL,
            tma_minutes INTEGER,
            reopening INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS kpis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            total_tickets INTEGER,
            reopening_rate REAL,
            avg_csat REAL,
            avg_tma REAL
        );
        CREATE TABLE IF NOT EXISTS sop_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern TEXT,
            suggestion TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(
    page_title="Reports KPI + SOP Optimizer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Reports KPI + SOP Optimizer")
st.markdown("Dashboard de KPIs de atendimento e otimização de SOPs")

with st.sidebar:
    st.header("📁 Upload de Dados")
    uploaded_file = st.file_uploader("Upload CSV de Tickets", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        conn = get_db()
        df.to_sql('tickets', conn, if_exists='replace', index=False)
        conn.close()
        st.success(f"{len(df)} tickets carregados!")

    st.header("📧 Configurações de Email")
    email_to = st.text_input("Email para relatório semanal")
    if st.button("Enviar Relatório Agora"):
        from email_report import send_weekly_report
        send_weekly_report(email_to)
        st.success("Relatório enviado!")

col1, col2, col3, col4 = st.columns(4)

conn = get_db()
try:
    df_tickets = pd.read_sql("SELECT * FROM tickets ORDER BY created_at DESC LIMIT 1000", conn)
except:
    df_tickets = pd.DataFrame()

if not df_tickets.empty():
    reopening_rate = round(df_tickets['reopening'].mean() * 100, 1) if 'reopening' in df_tickets.columns else 0
    avg_csat = round(df_tickets['csat'].mean(), 1) if 'csat' in df_tickets.columns else 0
    avg_tma = round(df_tickets['tma_minutes'].mean(), 1) if 'tma_minutes' in df_tickets.columns else 0
    tickets_count = len(df_tickets)
else:
    reopening_rate = 0
    avg_csat = 0
    avg_tma = 0
    tickets_count = 0

col1.metric("🎫 Total Tickets", tickets_count)
col2.metric("🔄 Reopening Rate", f"{reopening_rate}%")
col3.metric("⭐ CSAT Médio", avg_csat)
col4.metric("⏱️ TMA Médio (min)", avg_tma)

st.subheader("📈 Tickets por Canal")
if not df_tickets.empty and 'channel' in df_tickets.columns:
    channel_counts = df_tickets['channel'].value_counts().reset_index()
    channel_counts.columns = ['channel', 'count']
    fig = px.bar(channel_counts, x='channel', y='count', color='channel')
    st.plotly_chart(fig, use_container_width=True)

st.subheader("📊 KPIs ao Longo do Tempo")
if not df_tickets.empty and 'created_at' in df_tickets.columns:
    df_tickets['created_at'] = pd.to_datetime(df_tickets['created_at'])
    df_tickets['date'] = df_tickets['created_at'].dt.date
    daily_kpis = df_tickets.groupby('date').agg(
        total_tickets=('id', 'count'),
        avg_csat=('csat', 'mean'),
        avg_tma=('tma_minutes', 'mean'),
        reopening_rate=('reopening', 'mean')
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily_kpis['date'], y=daily_kpis['total_tickets'],
                             mode='lines+markers', name='Total Tickets'))
    fig.add_trace(go.Scatter(x=daily_kpis['date'], y=daily_kpis['avg_csat'],
                             mode='lines+markers', name='CSAT Médio', yaxis='y2'))
    fig.update_layout(
        yaxis=dict(title='Total Tickets'),
        yaxis2=dict(title='CSAT', overlaying='y', side='right')
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("🤖 Gerar Sugestão de SOP")
col_pattern, col_btn = st.columns([3, 1])
with col_pattern:
    pattern_input = st.text_input("Descreva o padrão observado",
                                   placeholder="Ex: alto volume de reabertura após feriados")
with col_btn:
    if st.button("Gerar SOP"):
        from sop_optimizer import analyze_pattern
        suggestion = analyze_pattern(pattern_input)
        st.success(f"Sugestão: {suggestion}")

conn.close()
