import sqlite3
import pandas as pd
import os
import json
from datetime import datetime, timedelta

DATA_PATH = os.environ.get('DATA_PATH', os.path.join(os.path.dirname(__file__), 'data'))
DB_PATH = os.path.join(DATA_PATH, 'database.sqlite')

PATTERN_DATABASE = {
    "feriado": "Aumentar capacidade no pré-feriado. Enviar respostas automáticas com SLA estendido.",
    "reabertura": "Revisar primeira resposta. Garantir que todas as dúvidas foram respondidas antes de fechar.",
    "alta demanda": "Ativar chatbot com perguntas frequentes. Priorizar tickets críticos.",
    "csat baixo": "Revisar script de atendimento. Oferecer treinamento de comunicação empática.",
    "tma alto": "Criar macros de resposta para problemas recorrentes. Revisar processos de escalonamento.",
    "sazonal": "Preparar equipe temporária. Criar FAQs sazonais antecipadamente.",
    "erro sistema": "Notificar TI imediatamente. Criar resposta padrão de incidente.",
    "cancelamento": "Criar fluxo de retenção com ofertas personalizadas."
}

def analyze_pattern(description: str) -> str:
    description_lower = description.lower()
    matches = []
    for keyword, suggestion in PATTERN_DATABASE.items():
        if keyword in description_lower:
            matches.append(suggestion)

    if matches:
        result = " | ".join(matches)

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO sop_suggestions (pattern, suggestion) VALUES (?, ?)",
            (description, result)
        )
        conn.commit()
        conn.close()
        return result

    return ("Analise o padrão manualmente: verifique dados históricos, "
            "identifique a causa raiz e documente o novo procedimento.")

def get_reopening_patterns() -> list:
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM tickets WHERE reopening = 1", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    if df.empty:
        return []
    patterns = []
    if 'category' in df.columns:
        for cat in df['category'].unique():
            count = len(df[df['category'] == cat])
            patterns.append({"pattern": f"Reabertura em {cat}", "count": int(count),
                             "suggestion": PATTERN_DATABASE.get("reabertura", "")})
    return patterns

if __name__ == "__main__":
    test = input("Describe the pattern you observed: ")
    result = analyze_pattern(test)
    print(f"\nSOP Suggestion: {result}")
