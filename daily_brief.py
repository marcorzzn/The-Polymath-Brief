import os
import datetime
import time
import feedparser
import concurrent.futures
from groq import Groq
from bs4 import BeautifulSoup
import pytz

# ================== CONFIGURAZIONE ==================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# RIDOTTO DRASTICAMENTE PER EVITARE BLOCCHI IP (ArXiv banna sopra i 15)
MAX_WORKERS = 10 
LOOKBACK_HOURS = 48  # Finestra temporale ampia
MAX_SECTION_CONTEXT = 60000

if not GROQ_API_KEY:
    print("⚠️ ATTENZIONE: GROQ_API_KEY non trovata. L'analisi AI fallirà.")

# ================== DATA ITALIANA ==================
def get_italian_date():
    mesi = {
        1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile",
        5: "maggio", 6: "giugno", 7: "luglio", 8: "agosto",
        9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre"
    }
    try:
        now = datetime.datetime.now(pytz.timezone("Europe/Rome"))
    except:
        now = datetime.datetime.now()
    return f"{now.day} {mesi[now.month]} {now.year}"

# ================== CLUSTER COMPLETI ==================
CLUSTERS = {
    "01_AI_RESEARCH": {
        "name": "INTELLIGENZA ARTIFICIALE",
        "desc": "Breakthroughs tecnici.",
        "urls": [
            "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=50",
            "http://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=50",
            "https://deepmind.google/blog/rss.xml",
            "https://openai.com/blog/rss.xml",
            "https://research.google/blog/rss",
            "https://ai.meta.com/blog/rss.xml",
            "https://huggingface.co/blog/feed.xml",
            "https://www.microsoft.com/en-us/research/feed/"
        ]
    },
    "02_QUANTUM": {
        "name": "FISICA DI FRONTIERA",
        "desc": "Calcolo quantistico e fisica.",
        "urls": [
            "http://export.arxiv.org/api/query?search_query=cat:quant-ph&sortBy=submittedDate&sortOrder=descending&max_results=40",
            "https://www.nature.com/nphys.rss",
            "https://phys.org/rss-feed/physics-news/quantum-physics/",
            "https://scitechdaily.com/tag/quantum-physics/feed/",
            "https://www.quantamagazine.org/feed/"
        ]
    },
    "03_MATH_FRONTIER": {
        "name": "MATEMATICA",
        "desc": "Lista Custom Utente.",
        "urls": [
            "https://eprint.iacr.org/rss/rss.xml",
            "https://blog.cryptographyengineering.com/feed/",
            "https://news.mit.edu/rss/topic/mathematics",
            "https://sinews.siam.org/rss/sn_rss.aspx",
            "http://export.arxiv.org/api/query?search_query=cat:math.OC&sortBy=submittedDate&sortOrder=descending&max_results=20",
            "https://www.santafe.edu/news/rss"
        ]
    },
    "04_BIO_SYNTHETIC": {
        "name": "BIOLOGIA E BIOTECNOLOGIE",
        "desc": "Genomica, CRISPR.",
        "urls": [
            "https://connect.biorxiv.org/biorxiv_xml.php?subject=synthetic_biology",
            "https://www.nature.com/nbt.rss",
            "https://www.genengnews.com/feed/",
            "https://www.fiercebiotech.com/rss/xml"
        ]
    },
    "05_CYBER_WARFARE": {
        "name": "CYBER-WARFARE E INTELLIGENCE",
        "desc": "InfoSec, Zero-Day.",
        "urls": [
            "https://googleprojectzero.blogspot.com/feeds/posts/default",
            "https://krebsonsecurity.com/feed/",
            "https://unit42.paloaltonetworks.com/feed/",
            "https://www.cisa.gov/uscert/ncas/alerts.xml",
            "https://www.darkreading.com/rss.xml"
        ]
    },
    "06_CHIP_FAB": {
        "name": "SILICIO E FONDERIE",
        "desc": "TSMC, ASML.",
        "urls": [
            "https://semiengineering.com/feed/",
            "https://www.semiconductors.org/feed/",
            "https://www.digitimes.com/rss/daily.xml",
            "https://semianalysis.com/feed/"
        ]
    },
    "07_CHIP_DESIGN": {
        "name": "HARDWARE",
        "desc": "GPU Design, HPC.",
        "urls": [
            "https://www.anandtech.com/rss/",
            "https://www.tomshardware.com/feeds/all",
            "https://www.servethehome.com/feed/",
            "https://www.nextplatform.com/feed/"
        ]
    },
    "08_MATERIALS": {
        "name": "MATERIALI",
        "desc": "Batterie, Chimica.",
        "urls": [
            "https://www.nature.com/nmat.rss",
            "https://cen.acs.org/rss/materials.xml",
            "https://battery-news.com/feed/"
        ]
    },
    "09_SPACE_FRONTIER": {
        "name": "SPACE ECONOMY",
        "desc": "ESA, NASA.",
        "urls": [
            "https://spacenews.com/feed/",
            "https://spaceflightnow.com/feed/",
            "https://gsp.esa.int/documents/10180/0/rss"
        ]
    },
    "10_GEO_DEFENSE": {
        "name": "DIFESA",
        "desc": "Strategie militari.",
        "urls": [
            "https://rusi.org/rss.xml",
            "https://warontherocks.com/feed/",
            "https://www.defensenews.com/arc/outboundfeeds/rss/",
            "https://www.janes.com/feeds/news"
        ]
    },
    "11_GEO_STRATEGY": {
        "name": "GEOPOLITICA E DIPLOMAZIA",
        "desc": "Analisi globale.",
        "urls": [
            "https://www.foreignaffairs.com/rss.xml",
            "https://www.csis.org/rss/analysis",
            "https://thediplomat.com/feed/",
            "https://merics.org/en/rss.xml"
        ]
    },
    "12_CENTRAL_BANKS": {
        "name": "MACROECONOMIA",
        "desc": "Banche Centrali.",
        "urls": [
            "https://www.bis.org/doclist/research.rss",
            "https://www.nber.org/rss/new.xml",
            "https://www.imf.org/en/Publications/RSS?language=eng&series=IMF%20Working%20Papers",
            "https://www.project-syndicate.org/rss"
        ]
    },
    "13_GLOBAL_ENERGY": {
        "name": "ENERGIA E RISORSE",
        "desc": "Mercati energetici.",
        "urls": [
            "https://oilprice.com/rss/main",
            "https://iea.org/rss/news",
            "https://gcaptain.com/feed/"
        ]
    }
}

# ================== ENGINE DI RACCOLTA ==================
def fetch_feed(url):
    print(f"📡 Scaricando: {url}...")
    try:
        # User Agent Standard per evitare blocchi (simula un browser reale)
        d = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        items = []
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(hours=LOOKBACK_HOURS)
        
        if not d.entries:
            print(f"   ⚠️ Nessuna voce in {url} (Possibile blocco IP o feed vuoto)")
            return []

        for entry in d.entries:
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)
            
            # LOGICA BOCCA LARGA: Se non c'è data, la prendiamo per sicurezza.
            if not pub_date or pub_date > cutoff:
                content = "No content"
                if hasattr(entry, 'summary'): 
                    content = entry.summary
                elif hasattr(entry, 'content'): 
                    content = entry.content[0].value
                elif hasattr(entry, 'description'): 
                    content = entry.description
                
                # Clean HTML
                try:
                    soup = BeautifulSoup(content, "html.parser")
                    content = soup.get_text(separator=" ", strip=True)[:5000]
                except Exception:
                    content = str(content).replace("<p>", "").replace("</p>", "").strip()[:5000]

                source = d.feed.get('title', 'Fonte')
                link = entry.link
                items.append(f"SRC: {source}\nLINK: {link}\nTITLE: {entry.title}\nTXT: {content}\n")
        
        print(f"   ✅ Trovati {len(items)} articoli in {url}")
        return items
    except Exception as e:
        print(f"   ❌ ERRORE su {url}: {e}")
        return []

def get_cluster_data(urls):
    data = []
    # Usiamo il ThreadPoolExecutor ma con meno worker per non farci bannare
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(fetch_feed, urls)
        for res in results:
            data.extend(res)
    return data

# ================== ANALISTA AI ==================
def analyze_cluster(cluster_key, info, raw_text, attempt=1):
    if not raw_text: 
        return ""
    
    print(f"  > Tentativo {attempt} - Analisi AI su {cluster_key} ({len(raw_text)} chars)...")
    
    system_prompt = f"""Sei un analista che deve scrivere da 2 a 4 notizie principali per il settore: {info['name']}
    
    REGOLE OBBLIGATORIE:
    1. Scrivi titoli in ITALIANO (Sentence case).
    2. Inserisci la fonte cliccabile alla fine di ogni notizia.
    3. Seleziona SOLO notizie rilevanti.
    
    FORMATO OUTPUT:
    ### [Titolo in Italiano]
    [Analisi di 2-3 righe]
    
    Fonte: [Link](URL)
    """
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": f"{system_prompt}\n\nMATERIALE:\n{raw_text[:MAX_SECTION_CONTEXT]}"}
            ],
            temperature=0.3, # Abbassata per essere più precisi
            max_tokens=6000
        )
        
        result = completion.choices[0].message.content
        news_count = result.count("###")
        
        # Retry logic leggera
        if news_count < 2 and attempt < 2:
            print(f"  ⚠️ Poche notizie ({news_count}), ritento...")
            time.sleep(2)
            return analyze_cluster(cluster_key, info, raw_text, attempt + 1)
            
        return result
        
    except Exception as e:
        print(f"  ❌ Errore AI: {e}")
        return ""

# ================== MAIN ==================
print("🚀 AVVIO POLIMATE (Fixed Version)...")
start_time = time.time()
italian_date = get_italian_date()
# Imposta timezone per il nome file
try:
    tz = pytz.timezone("Europe/Rome")
    today_iso = datetime.datetime.now(tz).strftime("%Y-%m-%d")
except:
    today_iso = datetime.datetime.now().strftime("%Y-%m-%d")

report_parts = []
total_news = 0

for key, info in CLUSTERS.items():
    print(f"\n--- {info['name']} ---")
    raw_data = get_cluster_data(info['urls'])
    
    if raw_data:
        raw_text = "\n---\n".join(raw_data)
        analysis = analyze_cluster(key, info, raw_text)
        
        if analysis and "###" in analysis:
            report_parts.append(f"\n\n## {info['name']}\n\n{analysis}\n")
            total_news += analysis.count("###")
    else:
        print(f"  ❌ Nessun dato raccolto per questo cluster.")
    
    # Pausa di cortesia tra i cluster per non sovraccaricare le API
    time.sleep(5)

# ================== SALVATAGGIO ==================
if not os.path.exists("_posts"):
    os.makedirs("_posts")

filename = f"_posts/{today_iso}-brief.md"
full_report = "".join(report_parts)

markdown_file = f"""---
title: "La rassegna del {italian_date}"
date: {today_iso}
layout: post
excerpt: "Intelligence strategica su {total_news} aggiornamenti globali."
---

{full_report if full_report else "Nessuna notizia rilevante trovata oggi (Controllare Logs)."}
"""

with open(filename, "w", encoding='utf-8') as f:
    f.write(markdown_file)

print(f"\n✅ SALVATO: {filename} ({total_news} notizie totali)")
