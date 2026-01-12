import os
import datetime
import time
import feedparser
import concurrent.futures
from groq import Groq

# --- CONFIGURAZIONE ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MAX_WORKERS = 20
LOOKBACK_HOURS = 26 
# Riduciamo leggermente il contesto per stare nei limiti del Tier Free
MAX_SECTION_CONTEXT = 25000 

if not GROQ_API_KEY:
    print("ERRORE CRITICO: Manca la GROQ_API_KEY.")
    exit(1)

# --- 1. DEFINIZIONE DOMINI ---
DOMAINS = {
    "1_SCIENZA": {
        "title": "FRONTIERA SCIENTIFICA (CODE & BIO)",
        "desc": "Crittografia, Bio-Syn, AI Theory, Quantum.",
        "urls": [
            "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=10",
            "http://export.arxiv.org/api/query?search_query=cat:quant-ph&sortBy=submittedDate&sortOrder=descending&max_results=5",
            "https://eprint.iacr.org/rss/rss.xml",
            "https://connect.biorxiv.org/biorxiv_xml.php?subject=synthetic_biology",
            "https://www.nature.com/nphys.rss",
            "https://googleprojectzero.blogspot.com/feeds/posts/default"
        ]
    },
    "2_HARDWARE": {
        "title": "HARDWARE & SUPPLY CHAIN (ATOMS)",
        "desc": "Litografia, Materiali, Supply Chain Critica.",
        "urls": [
            "https://semiengineering.com/feed/",
            "https://spectrum.ieee.org/feeds/topic/semiconductors/rss",
            "https://www.semiconductors.org/feed/",
            "https://chemrxiv.org/engage/chemrxiv/rss",
            "https://www.anl.gov/rss/research-news/feed",
            "https://www.imec-int.com/en/rss"
        ]
    },
    "3_GEOPOLITICA": {
        "title": "GEOPOLITICA & DOTTRINA (POWER)",
        "desc": "Difesa, Intelligence, Cavi sottomarini.",
        "urls": [
            "https://rusi.org/rss.xml",
            "https://www.csis.org/rss/analysis",
            "https://jamestown.org/feed/",
            "https://www.aspistrategist.org.au/feed/",
            "https://warontherocks.com/feed/",
            "https://www.defensenews.com/arc/outboundfeeds/rss/"
        ]
    },
    "4_MACRO": {
        "title": "MACROECONOMIA & RISCHIO (MONEY)",
        "desc": "Banche Centrali, Liquidità, Energia.",
        "urls": [
            "https://www.bis.org/doclist/research.rss",
            "https://www.federalreserve.gov/feeds/feds_rss.xml",
            "https://libertystreeteconomics.newyorkfed.org/feed/",
            "https://www.imf.org/en/Publications/RSS?language=eng&series=IMF%20Working%20Papers",
            "https://oilprice.com/rss/main"
        ]
    }
}

# --- 2. ENGINE DI RACCOLTA (HYDRA) ---
def fetch_url(url):
    try:
        # User agent fake per evitare blocchi
        d = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        items = []
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(hours=LOOKBACK_HOURS)
        
        for entry in d.entries:
            # Rilevamento data
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)
            
            # Se la data manca, la prendiamo per buona per evitare di perdere dati Tier-0
            if not pub_date or pub_date > cutoff:
                content = "No content"
                if hasattr(entry, 'summary'): content = entry.summary
                elif hasattr(entry, 'content'): content = entry.content[0].value
                elif hasattr(entry, 'description'): content = entry.description
                
                # Pulizia per risparmiare token
                content = content.replace("<p>", "").replace("</p>", "").replace("<div>", "")[:1000]
                items.append(f"SOURCE: {d.feed.get('title', 'Unknown')}\nTITLE: {entry.title}\nTXT: {content}\nLINK: {entry.link}\n")
        return items
    except Exception as e:
        print(f"Errore download {url}: {e}")
        return []

def get_domain_data(urls):
    data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_url, urls)
        for res in results:
            data.extend(res)
    return data

# --- 3. AGENTE AI (CON GESTIONE ERRORI) ---
def generate_chapter_safe(key, info, raw_text):
    if not raw_text:
        return f"## {info['title']}\n*Nessun dato rilevante acquisito nelle ultime 24h.*\n"
    
    # Taglio del contesto per evitare Rate Limit error
    context = raw_text[:MAX_SECTION_CONTEXT]
    
    print(f"  > Generazione capitolo {key} (Input: {len(context)} chars)...")
    
    system_prompt = f"""
    SEI: "The Polymath", analista intelligence.
    SETTORE: {info['title']}
    OBIETTIVO: Scrivere un capitolo di DOSSIER PROFONDO.
    
    INPUT: Notizie grezze.
    COMPITO:
    1. Scegli le 3 notizie più critiche.
    2. Per ognuna scrivi un'analisi dettagliata (Titolo, Fatti, Meccanismo Tecnico, Impatto Strategico).
    3. Aggiungi un Glossario Tecnico alla fine.
    
    TONO: Accademico, Asettico.
    """
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"DATI:\n{context}"}
            ],
            temperature=0.2,
            max_tokens=3000 # Un po' meno token per stare sicuri
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"  !!! ERRORE AI nel capitolo {key}: {str(e)}")
        return f"## {info['title']}\n\n*Errore nella generazione di questa sezione: {str(e)}*\n"

# --- 4. MAIN SEQUENCE ---
print("Avvio POLYMATH V2 (Safe Mode)...")
full_dossier = ""
today = datetime.datetime.now().strftime("%Y-%m-%d")

full_dossier += f"# POLYMATH DEEP DOSSIER\n**Data:** {today}\n\n---\n\n"

for key, info in DOMAINS.items():
    print(f"\n--- Processando: {info['title']} ---")
    
    # 1. Download
    raw_data = get_domain_data(info['urls'])
    raw_text = "\n---\n".join(raw_data)
    print(f"  > Segnali grezzi: {len(raw_data)}")
    
    # 2. AI Generation
    chapter = generate_chapter_safe(key, info, raw_text)
    full_dossier += chapter + "\n\n<br>\n\n"
    
    # 3. PAUSA DI SICUREZZA (Cool-down)
    print("  > Cooling down API (10s)...")
    time.sleep(10)

# --- 5. PUBLISHING ---
if not os.path.exists("_posts"):
    os.makedirs("_posts")

filename = f"_posts/{today}-brief.md"
markdown_file = f"""---
title: "Polymath Deep-Dive: {today}"
date: {today}
layout: post
---

{full_dossier}
"""

with open(filename, "w", encoding='utf-8') as f:
    f.write(markdown_file)

print(f"Dossier salvato: {filename}")
