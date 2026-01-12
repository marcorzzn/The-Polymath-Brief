import os
import datetime
import time
import feedparser
import concurrent.futures
from groq import Groq

# --- CONFIGURAZIONE ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MAX_WORKERS = 20           # Numero di download paralleli
LOOKBACK_HOURS = 26        # Finestra temporale (ultime 26 ore)
MAX_SECTION_CONTEXT = 22000 # Limite caratteri inviati all'AI per capitolo (Safe Mode)

if not GROQ_API_KEY:
    print("ERRORE CRITICO: Manca la GROQ_API_KEY nei Secrets.")
    exit(1)

# --- 1. DEFINIZIONE DEI 4 PILASTRI (CLUSTER DI FONTI) ---
DOMAINS = {
    "1_SCIENZA": {
        "title": "FRONTIERA SCIENTIFICA (CODE & BIO)",
        "desc": "Crittografia Post-Quantum, Biologia Sintetica, AI Architectures, Fisica Teorica.",
        "urls": [
            "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=10",
            "http://export.arxiv.org/api/query?search_query=cat:quant-ph&sortBy=submittedDate&sortOrder=descending&max_results=5",
            "https://eprint.iacr.org/rss/rss.xml", # Crittografia avanzata
            "https://connect.biorxiv.org/biorxiv_xml.php?subject=synthetic_biology",
            "https://connect.biorxiv.org/biorxiv_xml.php?subject=genomics",
            "https://www.nature.com/nphys.rss",
            "https://googleprojectzero.blogspot.com/feeds/posts/default", # Cyber-Security Offensiva
            "https://www.usenix.org/rss/conference/all-proceedings"
        ]
    },
    "2_HARDWARE": {
        "title": "HARDWARE & SUPPLY CHAIN (ATOMS)",
        "desc": "Litografia, Semiconduttori, Chimica delle Batterie, Materiali Strategici.",
        "urls": [
            "https://semiengineering.com/feed/", # Fonte primaria Chip
            "https://spectrum.ieee.org/feeds/topic/semiconductors/rss",
            "https://www.semiconductors.org/feed/",
            "https://chemrxiv.org/engage/chemrxiv/rss", # Chimica Materiali
            "https://www.anl.gov/rss/research-news/feed", # Argonne Lab
            "https://www.imec-int.com/en/rss", # IMEC
            "https://www.nist.gov/news-events/news/rss.xml"
        ]
    },
    "3_GEOPOLITICA": {
        "title": "GEOPOLITICA & DOTTRINA (POWER)",
        "desc": "Intelligence Militare, Cavi Sottomarini, Alleanze, Dottrina Nucleare.",
        "urls": [
            "https://rusi.org/rss.xml", # Royal United Services Institute
            "https://www.csis.org/rss/analysis",
            "https://jamestown.org/feed/", # Eurasia Monitor
            "https://www.aspistrategist.org.au/feed/", # ASPI (Pacifico)
            "https://warontherocks.com/feed/",
            "https://carnegieendowment.org/rss/solr/get/all-content",
            "https://www.defensenews.com/arc/outboundfeeds/rss/"
        ]
    },
    "4_MACRO": {
        "title": "MACROECONOMIA & RISCHIO (MONEY)",
        "desc": "Banche Centrali, Shadow Banking, Liquidità Globale, Energia.",
        "urls": [
            "https://www.bis.org/doclist/research.rss", # Bank for International Settlements
            "https://www.federalreserve.gov/feeds/feds_rss.xml", # FED Research Papers
            "https://libertystreeteconomics.newyorkfed.org/feed/", # NY Fed (Repo Market)
            "https://www.ecb.europa.eu/rss/wppub.xml",
            "https://www.imf.org/en/Publications/RSS?language=eng&series=IMF%20Working%20Papers",
            "https://oilprice.com/rss/main"
        ]
    }
}

# --- 2. ENGINE DI RACCOLTA (HYDRA THREADING) ---
def fetch_url(url):
    """Scarica un singolo feed filtrando per data"""
    try:
        # User agent per evitare blocchi 403
        d = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) PolymathBot/2.0")
        items = []
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(hours=LOOKBACK_HOURS)
        
        for entry in d.entries:
            # Parsing robusto della data
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)
            
            # Filtro temporale (accettiamo se recente o se data mancante per non perdere Tier-0)
            if not pub_date or pub_date > cutoff:
                content = "No content"
                if hasattr(entry, 'summary'): content = entry.summary
                elif hasattr(entry, 'content'): content = entry.content[0].value
                elif hasattr(entry, 'description'): content = entry.description
                
                # Pulizia stringhe HTML per risparmiare token
                content = content.replace("<p>", "").replace("</p>", "").replace("<div>", "").strip()[:1200]
                
                source_name = d.feed.get('title', 'Unknown Source')
                items.append(f"SOURCE: {source_name}\nTITLE: {entry.title}\nTXT: {content}\nLINK: {entry.link}\n")
        return items
    except Exception as e:
        # print(f"Errore download {url}: {e}") # Silenziato per pulizia log
        return []

def get_domain_data(urls):
    """Orchestra il download parallelo per un dominio"""
    data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(fetch_url, urls)
        for res in results:
            data.extend(res)
    return data

# --- 3. AGENTE AI (IL GIORNALISTA) ---
def generate_chapter_safe(key, info, raw_text):
    """Genera un capitolo del report gestendo errori e limiti"""
    
    if not raw_text:
        return f"## {info['title']}\n*Nessun segnale rilevante intercettato nelle ultime 24 ore.*\n"
    
    # Taglio preventivo del contesto
    context = raw_text[:MAX_SECTION_CONTEXT]
    
    print(f"  > Generazione Analisi: {info['title']} (Input: {len(context)} chars)...")
    
    system_prompt = f"""
    SEI: "Il Polimate". Non sei un robot, sei un osservatore onnisciente di intelligence strategica.
    SETTORE: {info['title']}
    
    OBIETTIVO: Scrivere un capitolo del Dossier Quotidiano.
    
    INPUT: Notizie grezze (spesso in inglese).
    
    COMPITO:
    1. Seleziona i 3 SEGNALI DEBOLI più critici (ignora il rumore mainstream).
    2. Analizzali scrivendo in ITALIANO COLTO E IMPECCABILE.
       - Stile: "Il Foglio", "Limes", "The Economist".
       - NO traduzioni letterali (evita "translationese").
    
    STRUTTURA PER OGNI NOTIZIA:
    - **TITOLO:** [Serio e incisivo]
    - **I FATTI:** [Cosa è successo esattamente]
    - **IL MECCANISMO:** [Spiegazione tecnica profonda. Perché è importante? Come funziona?]
    - **IMPATTO:** [Conseguenze a medio termine sugli scenari globali]
    - **FONTE:** [Link]

    3. GLOSSARIO TATTICO (Obbligatorio alla fine):
       Definisci in modo semplice 3 termini tecnici complessi usati nel testo.

    VIETATO:
    - Usare frasi fatte come "In conclusione", "È interessante notare".
    - Essere superficiale.
    """
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"INTELLIGENCE DUMP:\n{context}"}
            ],
            temperature=0.3, # Leggermente più creativo per favorire la prosa italiana
            max_tokens=4000
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"  !!! ERRORE AI nel capitolo {key}: {str(e)}")
        return f"## {info['title']}\n\n*Errore nella generazione: {str(e)}*\n"

# --- 4. MAIN SEQUENCER ---
print("Avvio IL POLIMATE ENGINE...")
start_time = time.time()
full_dossier = ""
today = datetime.datetime.now().strftime("%Y-%m-%d")
display_date = datetime.datetime.now().strftime("%d %B %Y")

# Header del Markdown
full_dossier += f"# IL POLIMATE: Dossier del {today}\n"
full_dossier += f"**Classificazione:** STRATEGIC / EYES ONLY\n\n"
full_dossier += f"> Report generato dall'analisi di fonti primarie (Pre-print, Intelligence, Banche Centrali).\n\n---\n\n"

# Ciclo sui 4 Domini
for key, info in DOMAINS.items():
    print(f"\n--- Processando Settore: {info['title']} ---")
    
    # A. Raccolta Dati
    raw_data = get_domain_data(info['urls'])
    raw_text = "\n---\n".join(raw_data)
    print(f"  > Segnali acquisiti: {len(raw_data)}")
    
    # B. Generazione Capitolo
    chapter = generate_chapter_safe(key, info, raw_text)
    full_dossier += chapter + "\n\n<br>\n\n"
    
    # C. Pausa Tattica (Cool-down API)
    print("  > Pausa di sicurezza API (15s)...")
    time.sleep(15)

# Footer
full_dossier += "\n---\n*End of Transmission. Generated by Polymath Hydra Core.*"

# --- 5. PUBBLICAZIONE ---
if not os.path.exists("_posts"):
    os.makedirs("_posts")

filename = f"_posts/{today}-brief.md"
markdown_file = f"""---
title: "Il Dossier del {today}"
date: {today}
layout: post
---

{full_dossier}
"""

with open(filename, "w", encoding='utf-8') as f:
    f.write(markdown_file)

duration = time.time() - start_time
print(f"\nDossier completato in {duration:.2f} secondi. File: {filename}")
