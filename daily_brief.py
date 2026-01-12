import os
import datetime
import time
from duckduckgo_search import DDGS
from groq import Groq

# --- CONFIGURAZIONE ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Verifica preliminare chiave
if not GROQ_API_KEY:
    report_content = "ERRORE FATALE: Manca la GROQ_API_KEY nei Secrets."
else:
    # --- 1. GATHERING (DUCKDUCKGO) ---
    ddgs = DDGS()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    queries = [
        "arxiv physics breakthrough new discovery last 24 hours",
        "semiconductor advanced packaging news tsmc intel last 24 hours",
        "undersea internet cables geopolitics news last 24 hours",
        "central bank digital currency cbdc latest pilot news last 24 hours"
    ]

    print(f"Scansione per il {today}...")
    raw_context = ""

    for query in queries:
        try:
            results = ddgs.text(query, max_results=3)
            if results:
                for r in results:
                    raw_context += f"\nTITOLO: {r['title']}\nSNIPPET: {r['body']}\nURL: {r['href']}\n"
            time.sleep(1)
        except Exception as e:
            print(f"Errore ricerca '{query}': {e}")

    if not raw_context:
        raw_context = "NESSUNA NOTIZIA TROVATA. Il motore di ricerca non ha restituito dati."

    # --- 2. ANALYSIS (GROQ) ---
    system_prompt = """
    SEI: "The Polymath", analista di intelligence.
    OBIETTIVO: Scrivere "THE POLYMATH BRIEF".
    DATA: {date}
    
    REGOLE:
    1. Fonte dati: Usa SOLO il testo fornito.
    2. Stile: Asettico, tecnico, italiano.
    3. Formato: 4 Sezioni (Frontiera Tech, Hardware, Geopolitica, Macro).
    Per ogni notizia usa questo format:
    - **Il Segnale:** [Titolo]
    - **I Fatti:** [Dettagli]
    - **Il Meccanismo:** [Spiegazione tecnica]
    - **Fonti:** [URL]
    """

    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            # AGGIORNAMENTO MODELLO: Usiamo la versione 3.3 Versatile (più stabile)
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt.format(date=today)},
                {"role": "user", "content": f"NOTIZIE GREZZE:\n{raw_context}"}
            ],
            temperature=0.3
        )
        report_content = completion.choices[0].message.content

    except Exception as e:
        # QUI CATTURIAMO L'ERRORE VERO E LO SCRIVIAMO NEL FILE
        report_content = f"## ERRORE DI SISTEMA\n\nIl motore AI ha fallito. Ecco il log tecnico:\n\n`{str(e)}`"

# --- 3. PUBLISHING ---
markdown_file = f"""---
title: "Polymath Brief: {today}"
date: {today}
layout: post
---

{report_content}
"""

if not os.path.exists("_posts"):
    os.makedirs("_posts")

filename = f"_posts/{today}-brief.md"
with open(filename, "w", encoding='utf-8') as f:
    f.write(markdown_file)
