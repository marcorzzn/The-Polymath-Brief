import os
import datetime
from tavily import TavilyClient
from openai import OpenAI

# --- CONFIGURAZIONE ---
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not TAVILY_API_KEY or not OPENAI_API_KEY:
    raise ValueError("Le API Keys mancano! Controlla i Secrets di GitHub.")

tavily = TavilyClient(api_key=TAVILY_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

# Data di oggi
today = datetime.datetime.now().strftime("%Y-%m-%d")

# --- 1. GATHERING (RACCOLTA INTELLIGENCE) ---
# Queste query sono ottimizzate per filtrare il rumore
queries = [
    "latest breakthrough physics nature science arxiv last 24h",
    "new semiconductor technology manufacturing tsmc intel nvidia last 24h",
    "geopolitics submarine cables critical minerals supply chain last 24h",
    "macroeconomics central bank digital currency social impact last 24h"
]

print(f"Inizio scansione intelligence per il {today}...")
raw_context = ""

for query in queries:
    print(f"Searching: {query}")
    try:
        response = tavily.search(query=query, search_depth="advanced", time_range="day")
        # Estraiamo solo i contenuti rilevanti per risparmiare token
        for result in response.get('results', []):
            raw_context += f"\nSOURCE: {result['title']} - {result['content']}\nURL: {result['url']}\n"
    except Exception as e:
        print(f"Errore nella ricerca {query}: {e}")

# --- 2. ANALYSIS (IL PROMPT POLYMATH) ---
system_prompt = """
SEI: "The Polymath", un analista di intelligence strategica.
IL TUO COMPITO: Scrivere la rassegna quotidiana "THE POLYMATH BRIEF".
DATA DI OGGI: {date}

INPUT:
Riceverai una lista di notizie grezze ("raw_context").

REGOLE ASSOLUTE:
1. SELEZIONE RIGIDA: Ignora gossip, politica partitica, sport. Cerca SOLO: Segnali Deboli, Hard Tech, Geopolitica Infrastrutturale.
2. STILE: Asettico, denso, italiano professionale. Niente frasi come "Incredibile scoperta!". Solo fatti e meccanismi.
3. FORMATO: Usa Markdown rigoroso. Devi produrre ESATTAMENTE 4 sezioni:
   - FRONTIERA HARD-TECH & MATEMATICA
   - HARDWARE & MACCHINE
   - GEOPOLITICA DEI FLUSSI
   - RADAR SOCIALE & MACROECONOMIA
4. STRUTTURA PER OGNI NOTIZIA:
   - **Il Segnale:** [Titolo]
   - **I Fatti:** [Cosa è successo]
   - **Il Meccanismo:** [Spiegazione tecnica/fisica/economica del PERCHÉ è rilevante]
   - **Fonti:** [Link]

IMPORTANTE: Se per una sezione non ci sono notizie rilevanti nel contesto fornito, scrivi: "NESSUN SEGNALE RILEVATO NELLE ULTIME 24H". Non inventare.
"""

print("Analisi in corso con GPT-4o...")
completion = client.chat.completions.create(
    model="gpt-4o", # Puoi usare gpt-4o-mini per risparmiare, ma gpt-4o è più intelligente
    messages=[
        {"role": "system", "content": system_prompt.format(date=today)},
        {"role": "user", "content": f"Ecco le notizie grezze raccolte: {raw_context}"}
    ],
    temperature=0.3 # Bassa temperatura per evitare allucinazioni
)

report_content = completion.choices[0].message.content

# --- 3. PUBLISHING (CREAZIONE FILE) ---
# Aggiunge l'header YAML per Jekyll/GitHub Pages
markdown_file = f"""---
title: "Polymath Brief: {today}"
date: {today}
layout: post
---

{report_content}
"""

# Crea la cartella _posts se non esiste
if not os.path.exists("_posts"):
    os.makedirs("_posts")

filename = f"_posts/{today}-brief.md"
with open(filename, "w", encoding='utf-8') as f:
    f.write(markdown_file)

print(f"Report generato: {filename}")
