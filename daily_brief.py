import os
import datetime
import time
import feedparser
import concurrent.futures
from groq import Groq

# --- CONFIGURAZIONE ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MAX_WORKERS = 5
LOOKBACK_HOURS = 28  # Finestra ampia per non perdere nulla
MAX_SECTION_CONTEXT = 15000  # Ridotto per gestire meglio il contesto

if not GROQ_API_KEY:
    print("ERRORE: Manca GROQ_API_KEY.")
    exit(1)

# ================= FONTI =================
CLUSTERS = {
    "01_AI_RESEARCH": {
        "name": "INTELLIGENZA ARTIFICIALE",
        "desc": "Breakthroughs tecnici.",
        "urls": [
            "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=50",
            "http://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=50",
            "https://www.csail.mit.edu/news/feed",
            "https://hai.stanford.edu/news/feed", 
            "https://bair.berkeley.edu/blog/feed.xml", 
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
            "https://www.caltech.edu/c/news/rss", 
            "https://ethz.ch/en/news-and-events/eth-news/news.rss", 
            "https://qt.eu/feed/", 
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
            "https://research.chain.link/feed.xml",
            "https://news.mit.edu/rss/topic/mathematics",
            "https://sinews.siam.org/rss/sn_rss.aspx",
            "https://rss.ams.org/math-in-the-media.xml",
            "http://export.arxiv.org/api/query?search_query=cat:math.NA&sortBy=submittedDate&sortOrder=descending&max_results=20",
            "http://export.arxiv.org/api/query?search_query=cat:math.OC&sortBy=submittedDate&sortOrder=descending&max_results=20",
            "http://export.arxiv.org/api/query?search_query=cat:math.DS&sortBy=submittedDate&sortOrder=descending&max_results=15",
            "http://export.arxiv.org/api/query?search_query=cat:math.ST&sortBy=submittedDate&sortOrder=descending&max_results=15",
            "https://www.quantamagazine.org/feed/",
            "https://www.santafe.edu/news/rss",
            "http://export.arxiv.org/api/query?search_query=cat:cs.GT&sortBy=submittedDate&sortOrder=descending&max_results=15"
        ]
    },
    "04_BIO_SYNTHETIC": {
        "name": "BIOLOGIA & BIOTECNOLOGIE",
        "desc": "Genomica, CRISPR.",
        "urls": [
            "https://connect.biorxiv.org/biorxiv_xml.php?subject=synthetic_biology",
            "https://connect.biorxiv.org/biorxiv_xml.php?subject=genomics",
            "https://www.nature.com/nbt.rss", 
            "https://www.thelancet.com/rssfeed/lancet_current.xml", 
            "https://www.cell.com/cell/current.rss", 
            "https://hms.harvard.edu/news/rss", 
            "https://www.genengnews.com/feed/",
            "https://www.fiercebiotech.com/rss/xml"
        ]
    },
    "05_CYBER_WARFARE": {
        "name": "CYBER-WARFARE & INTELLIGENCE",
        "desc": "InfoSec, Zero-Day.",
        "urls": [
            "https://googleprojectzero.blogspot.com/feeds/posts/default",
            "https://threatpost.com/feed/",
            "https://krebsonsecurity.com/feed/",
            "https://www.mandiant.com/resources/blog/rss.xml",
            "https://unit42.paloaltonetworks.com/feed/",
            "https://www.cisa.gov/uscert/ncas/alerts.xml", 
            "https://www.crowdstrike.com/blog/feed/",
            "https://www.darkreading.com/rss.xml",
            "https://www.sentinelone.com/blog/feed/"
        ]
    },
    "06_CHIP_FAB": {
        "name": "SILICIO & FONDERIE",
        "desc": "TSMC, ASML.",
        "urls": [
            "https://semiengineering.com/feed/",
            "https://www.imec-int.com/en/rss",
            "https://www.semiconductors.org/feed/",
            "https://www.digitimes.com/rss/daily.xml", 
            "https://semianalysis.com/feed/",
            "https://semiwiki.com/feed/",
            "https://news.mit.edu/rss/topic/engineering"
        ]
    },
    "07_CHIP_DESIGN": {
        "name": "HARDWARE",
        "desc": "GPU Design, HPC.",
        "urls": [
            "https://spectrum.ieee.org/feeds/topic/semiconductors/rss",
            "https://www.anandtech.com/rss/",
            "https://www.tomshardware.com/feeds/all",
            "https://www.servethehome.com/feed/", 
            "https://chipsandcheese.com/feed/", 
            "https://www.nextplatform.com/feed/"
        ]
    },
    "08_MATERIALS": {
        "name": "MATERIALI",
        "desc": "Batterie, Chimica.",
        "urls": [
            "https://chemrxiv.org/engage/chemrxiv/rss",
            "https://www.anl.gov/rss/research-news/feed", 
            "https://www.nature.com/nmat.rss",
            "https://cen.acs.org/rss/materials.xml", 
            "https://battery-news.com/feed/",
            "https://onlinelibrary.wiley.com/feed/15214095/most-recent"
        ]
    },
    "09_SPACE_FRONTIER": {
        "name": "SPACE ECONOMY",
        "desc": "ESA, NASA.",
        "urls": [
            "https://spacenews.com/feed/",
            "https://www.esa.int/rssfeed/Our_Activities/Operations",
            "https://www.jpl.nasa.gov/feeds/news/",
            "https://blogs.nasa.gov/station/feed/",
            "https://spaceflightnow.com/feed/",
            "https://gsp.esa.int/documents/10180/0/rss",
            "https://www.cfa.harvard.edu/news/rss.xml"
        ]
    },
    "10_GEO_DEFENSE": {
        "name": "DIFESA",
        "desc": "Strategie militari.",
        "urls": [
            "https://rusi.org/rss.xml",
            "https://warontherocks.com/feed/",
            "https://www.rand.org/news/politics-and-government.xml", 
            "https://mwi.westpoint.edu/feed/", 
            "https://www.defensenews.com/arc/outboundfeeds/rss/",
            "https://news.usni.org/feed",
            "https://www.understandingwar.org/feeds.xml", 
            "https://www.janes.com/feeds/news",
            "https://www.darpa.mil/rss/news" 
        ]
    },
    "11_GEO_STRATEGY": {
        "name": "GEOPOLITICA & DIPLOMAZIA",
        "desc": "Analisi globale.",
        "urls": [
            "https://www.foreignaffairs.com/rss.xml", 
            "https://www.chathamhouse.org/rss/research/all", 
            "https://www.cfr.org/feed/all", 
            "https://www.aspistrategist.org.au/feed/",
            "https://jamestown.org/feed/",
            "https://www.csis.org/rss/analysis",
            "https://thediplomat.com/feed/",
            "https://merics.org/en/rss.xml",
            "https://legrandcontinent.eu/fr/feed/"
        ]
    },
    "12_CENTRAL_BANKS": {
        "name": "MACROECONOMIA & CAPITALE",
        "desc": "Banche Centrali.",
        "urls": [
            "https://www.bis.org/doclist/research.rss",
            "https://www.nber.org/rss/new.xml", 
            "https://www.federalreserve.gov/feeds/feds_rss.xml",
            "https://libertystreeteconomics.newyorkfed.org/feed/",
            "https://www.ecb.europa.eu/rss/wppub.xml",
            "https://www.imf.org/en/Publications/RSS?language=eng&series=IMF%20Working%20Papers",
            "https://www.worldbank.org/en/rss/research",
            "https://www.project-syndicate.org/rss",
            "https://www.bruegel.org/rss"
        ]
    },
    "13_GLOBAL_ENERGY": {
        "name": "ENERGIA & RISORSE",
        "desc": "Mercati energetici.",
        "urls": [
            "https://oilprice.com/rss/main",
            "https://www.oxfordenergy.org/feed/",
            "https://iea.org/rss/news",
            "https://www.nrel.gov/news/rss.xml", 
            "https://www.world-nuclear-news.org/RSS/WNN-News.xml",
            "https://gcaptain.com/feed/",
            "https://news.mit.edu/rss/topic/energy"
        ]
    }
}

# --- 2. ENGINE DI RACCOLTA ---
def fetch_feed(url):
    try:
        d = feedparser.parse(url, agent="Mozilla/5.0 (PolymathBot/3.0)")
        items = []
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(hours=LOOKBACK_HOURS)
        
        for entry in d.entries:
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)
            
            # Accettiamo tutto ciò che è recente O che non ha data (per sicurezza)
            if not pub_date or pub_date > cutoff:
                content = "No content"
                if hasattr(entry, 'summary'): content = entry.summary
                elif hasattr(entry, 'content'): content = entry.content[0].value
                elif hasattr(entry, 'description'): content = entry.description
                
                content = content.replace("<p>", "").replace("</p>", "").replace("<div>", "").strip()[:1500]
                source = d.feed.get('title', 'Unknown Source')
                link = entry.link
                items.append(f"SRC: {source}\nLINK: {link}\nTITLE: {entry.title}\nTXT: {content}\n")
        return items
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return []

def get_cluster_data(urls):
    data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(fetch_feed, urls)
        for res in results:
            data.extend(res)
    return data

# --- 3. AGENTE ANALISTA (PROMPT MASSIVO) ---
def analyze_cluster(cluster_key, info, raw_text):
    if not raw_text: return ""
    
    print(f"  > Analisi {cluster_key} ({len(raw_text)} chars)...")
    
    # Prompt modificato per generare TANTI contenuti con link cliccabili
    system_prompt = f"""
SEI: "Il Polimate", analista di intelligence.
SETTORE: {info['name']}

OBIETTIVO: Creare un report dettagliatissimo ed esteso.
DEVI ANALIZZARE I FLUSSI DI NOTIZIE DAI 13 CLUSTER SELEZIONATI E SCEGLIERE LE 3-4 NOTIZIE PIÙ RILEVANTI PER OGNI CLUSTER.

INPUT: Lista di news/paper.

OUTPUT RICHIESTO:
- Scorri tutte le notizie fornite per un cluster
- Seleziona 3 o 4 notizie tecnicamente rilevanti per il relativo cluster
- Scrivi dei paragrafi per i 3/4 articoli selezionati
- Fai le 3 azioni precedenti per i restanti cluster, fino a farlo per ogni cluster

FORMATO PER OGNI NOTIZIA (Usa Markdown):
### [Titolo con capitalizzazione italiana]
[Analisi tecnica dettagliata di 4-5 righe. Spiega il 'cosa', il 'come' e il 'perché'. Usa termini tecnici.] [con capitalizzazione italiana]
[inserire riga di spazio]
**Fonte:** [Inserisci il LINK originale fornito] (DEVE ESSERE CLICCABILE COME MARKDOWN)

STILE:
- Densità informativa massima.
- Italiano professionale.
- NESSUNA INTRODUZIONE, NESSUNA CONCLUSIONE. Solo la lista delle analisi.
- NON UTILIZZARE <hr> O LINEE ORIZZONTALI
"""
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"INPUT DATI:\n{raw_text[:MAX_SECTION_CONTEXT]}"}
            ],
            temperature=0.2,
            max_tokens=6000 # Massimo spazio per scrivere tantissimo
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error {cluster_key}: {e}")
        return ""

# --- 4. SEQUENCER ---
print("Avvio MOTORE EPOCHALE...")
today = datetime.datetime.now().strftime("%Y-%m-%d")

# Data in italiano
today_date = datetime.datetime.now()
month_name = today_date.strftime("%B")
month_italian = {
    "January": "gennaio",
    "February": "febbraio",
    "March": "marzo",
    "April": "aprile",
    "May": "maggio",
    "June": "giugno",
    "July": "luglio",
    "August": "agosto",
    "September": "settembre",
    "October": "ottobre",
    "November": "novembre",
    "December": "dicembre"
}.get(month_name, month_name)
display_date = f"{today_date.day} {month_italian} {today_date.year}"

full_report = f"""---
title: "La rassegna del {display_date}"
date: {today}
layout: post
excerpt: "Analisi granulare di oltre 12 settori strategici con centinaia di fonti primarie."
---

> Questo documento contiene un'analisi granulare di tutti i segnali rilevanti intercettati nelle ultime 24 ore. Ogni sezione approfondisce decine di paper, report e comunicati.

---
"""

for key, info in CLUSTERS.items():
    print(f"\n--- Processando Cluster: {info['name']} ---")
    
    # Pulisci gli URL rimuovendo spazi e ritorni a capo
    clean_urls = [url.strip() for url in info['urls']]
    
    raw_data = get_cluster_data(clean_urls)
    
    if raw_data:
        print(f"  > Trovati {len(raw_data)} articoli per {info['name']}")
        # Limita a 50 articoli per evitare di sovraccaricare il modello
        limited_raw_data = raw_data[:50]
        raw_text = "\n---\n".join(limited_raw_data)
        analysis = analyze_cluster(key, info, raw_text)
        
        if analysis and len(analysis) > 50:
            full_report += f"\n\n## {info['name']}\n\n{analysis}\n\n"
        else:
            print("  > Nessun output rilevante dall'AI.")
    else:
        print("  > Nessun dato grezzo trovato.")
    
    # Aumenta il tempo di attesa
    time.sleep(20)

# --- 5. SALVATAGGIO ---
if not os.path.exists("_posts"): os.makedirs("_posts")
filename = f"_posts/{today}-brief.md"

with open(filename, "w", encoding='utf-8') as f:
    f.write(full_report)

print("Dossier Epochale Generato.")
