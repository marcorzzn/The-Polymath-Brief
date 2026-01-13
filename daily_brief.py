import os
import datetime
import time
import feedparser
import concurrent.futures
from groq import Groq

# --- CONFIGURAZIONE ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MAX_WORKERS = 50            
LOOKBACK_HOURS = 24         # TORNATI A 24 ORE (Notizie freschissime)
MAX_SECTION_CONTEXT = 45000 # ALZATO AL MASSIMO (Per leggere decine di notizie)

if not GROQ_API_KEY:
    print("ERRORE CRITICO: Manca la GROQ_API_KEY.")
    exit(1)

# --- FUNZIONE DATA ITALIANA ---
def get_italian_date():
    months = {
        1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile", 5: "maggio", 6: "giugno",
        7: "luglio", 8: "agosto", 9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre"
    }
    now = datetime.datetime.now()
    return f"{now.day} {months[now.month]} {now.year}"

# --- 1. CLUSTER STRATEGICI (160+ FONTI) ---
CLUSTERS = {
    "01_AI_RESEARCH": {
        "name": "MENTE SINTETICA & LABORATORI AI",
        "desc": "MIT CSAIL, Stanford HAI, DeepMind, ArXiv.",
        "urls": [
            "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=30",
            "http://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=30",
            "https://www.csail.mit.edu/news/feed", 
            "https://hai.stanford.edu/news/feed", 
            "https://bair.berkeley.edu/blog/feed.xml", 
            "https://deepmind.google/blog/rss.xml",
            "https://openai.com/blog/rss.xml",
            "https://research.google/blog/rss",
            "https://ai.meta.com/blog/rss.xml",
            "https://huggingface.co/blog/feed.xml"
        ]
    },
    "02_QUANTUM": {
        "name": "FISICA DI FRONTIERA & QUANTUM",
        "desc": "Caltech, ETH Zurich, Nature Physics.",
        "urls": [
            "http://export.arxiv.org/api/query?search_query=cat:quant-ph&sortBy=submittedDate&sortOrder=descending&max_results=20",
            "https://www.nature.com/nphys.rss",
            "https://phys.org/rss-feed/physics-news/quantum-physics/",
            "https://www.caltech.edu/c/news/rss", 
            "https://ethz.ch/en/news-and-events/eth-news/news.rss", 
            "https://qt.eu/feed/", 
            "https://scitechdaily.com/tag/quantum-physics/feed/"
        ]
    },
    "03_CRYPTO_MATH": {
        "name": "CRITTOGRAFIA & MATEMATICA",
        "desc": "IACR, Ethereum Research.",
        "urls": [
            "https://eprint.iacr.org/rss/rss.xml", 
            "https://blog.cryptographyengineering.com/feed/",
            "https://schneier.com/blog/atom.xml",
            "https://blog.ethereum.org/feed.xml", 
            "https://research.chain.link/feed.xml"
        ]
    },
    "04_BIO_SYNTHETIC": {
        "name": "BIOLOGIA SINTETICA & MED-TECH",
        "desc": "Harvard Medicine, Lancet, CRISPR.",
        "urls": [
            "https://connect.biorxiv.org/biorxiv_xml.php?subject=synthetic_biology",
            "https://connect.biorxiv.org/biorxiv_xml.php?subject=genomics",
            "https://www.nature.com/nbt.rss", 
            "https://www.thelancet.com/rssfeed/lancet_current.xml", 
            "https://www.cell.com/cell/current.rss", 
            "https://hms.harvard.edu/news/rss", 
            "https://www.genengnews.com/feed/"
        ]
    },
    "05_CYBER_WARFARE": {
        "name": "CYBER-WARFARE & INTELLIGENCE",
        "desc": "NSA/CISA Alerts, Unit 42, Zero-Day.",
        "urls": [
            "https://googleprojectzero.blogspot.com/feeds/posts/default",
            "https://threatpost.com/feed/",
            "https://krebsonsecurity.com/feed/",
            "https://www.mandiant.com/resources/blog/rss.xml",
            "https://unit42.paloaltonetworks.com/feed/",
            "https://www.cisa.gov/uscert/ncas/alerts.xml", 
            "https://www.crowdstrike.com/blog/feed/",
            "https://www.darkreading.com/rss.xml"
        ]
    },
    "06_CHIP_FAB": {
        "name": "SILICIO & FONDERIE",
        "desc": "TSMC, ASML, Supply Chain.",
        "urls": [
            "https://semiengineering.com/feed/",
            "https://www.imec-int.com/en/rss",
            "https://www.semiconductors.org/feed/",
            "https://www.digitimes.com/rss/daily.xml", 
            "https://semianalysis.com/feed/",
            "https://semiwiki.com/feed/"
        ]
    },
    "07_CHIP_DESIGN": {
        "name": "ARCHITETTURE HARDWARE",
        "desc": "IEEE, GPU Design, HPC.",
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
        "name": "SCIENZA DEI MATERIALI",
        "desc": "Batterie, Argonne Lab.",
        "urls": [
            "https://chemrxiv.org/engage/chemrxiv/rss",
            "https://www.anl.gov/rss/research-news/feed", 
            "https://www.nature.com/nmat.rss",
            "https://cen.acs.org/rss/materials.xml", 
            "https://battery-news.com/feed/"
        ]
    },
    "09_SPACE_FRONTIER": {
        "name": "SPACE ECONOMY",
        "desc": "SpaceNews, ESA, NASA JPL.",
        "urls": [
            "https://spacenews.com/feed/",
            "https://www.esa.int/rssfeed/Our_Activities/Operations",
            "https://www.jpl.nasa.gov/feeds/news/", 
            "https://blogs.nasa.gov/station/feed/",
            "https://spaceflightnow.com/feed/",
            "https://gsp.esa.int/documents/10180/0/rss"
        ]
    },
    "10_GEO_DEFENSE": {
        "name": "IL GRANDE GIOCO (DIFESA)",
        "desc": "RAND Corp, West Point, RUSI.",
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
        "desc": "Foreign Affairs, CSIS, Chatham House.",
        "urls": [
            "https://www.foreignaffairs.com/rss.xml", 
            "https://www.chathamhouse.org/rss/research/all", 
            "https://www.cfr.org/feed/all", 
            "https://www.aspistrategist.org.au/feed/",
            "https://jamestown.org/feed/",
            "https://www.csis.org/rss/analysis",
            "https://thediplomat.com/feed/",
            "https://merics.org/en/rss.xml"
        ]
    },
    "12_CENTRAL_BANKS": {
        "name": "MACROECONOMIA & CAPITALE",
        "desc": "NBER, BIS, FED, World Bank.",
        "urls": [
            "https://www.bis.org/doclist/research.rss",
            "https://www.nber.org/rss/new.xml", 
            "https://www.federalreserve.gov/feeds/feds_rss.xml",
            "https://libertystreeteconomics.newyorkfed.org/feed/",
            "https://www.ecb.europa.eu/rss/wppub.xml",
            "https://www.imf.org/en/Publications/RSS?language=eng&series=IMF%20Working%20Papers",
            "https://www.worldbank.org/en/rss/research",
            "https://www.project-syndicate.org/rss"
        ]
    },
    "13_GLOBAL_ENERGY": {
        "name": "ENERGIA & RISORSE",
        "desc": "IEA, Oxford Energy, OilPrice.",
        "urls": [
            "https://oilprice.com/rss/main",
            "https://www.oxfordenergy.org/feed/",
            "https://iea.org/rss/news",
            "https://www.nrel.gov/news/rss.xml", 
            "https://www.world-nuclear-news.org/RSS/WNN-News.xml",
            "https://gcaptain.com/feed/"
        ]
    }
}

# --- 2. ENGINE DI RACCOLTA ---
def fetch_feed(url):
    try:
        d = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) PolymathBot/3.0")
        items = []
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(hours=LOOKBACK_HOURS)
        
        for entry in d.entries:
            # Parsing data rigoroso
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)
            
            # FILTRO 24H: Se non ha data, lo prendiamo (per sicurezza), se ce l'ha deve essere > cutoff
            if not pub_date or pub_date > cutoff:
                content = "No content"
                if hasattr(entry, 'summary'): content = entry.summary
                elif hasattr(entry, 'content'): content = entry.content[0].value
                elif hasattr(entry, 'description'): content = entry.description
                
                # Pulizia HTML per risparmiare token
                content = content.replace("<p>", "").replace("</p>", "").replace("<div>", "").strip()[:3000]
                source = d.feed.get('title', 'Fonte')
                link = entry.link
                items.append(f"SRC: {source}\nLINK: {link}\nTITLE: {entry.title}\nTXT: {content}\n")
        return items
    except:
        return []

def get_cluster_data(urls):
    data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(fetch_feed, urls)
        for res in results:
            data.extend(res)
    return data

# --- 3. ANALISTA AI (VOLUME MASSIMO) ---
def analyze_cluster(cluster_key, info, raw_text):
    if not raw_text: return ""
    
    print(f"  > Analisi {cluster_key} ({len(raw_text)} chars)...")
    
    # PROMPT AGGRESSIVO PER QUANTITÀ
    system_prompt = f"""
    SEI: "Il Polimate". 
    SETTORE: {info['name']}
    
    OBIETTIVO: Elencare IL MAGGIOR NUMERO POSSIBILE di notizie valide.
    NON FILTRARE TROPPO. Se una notizia è recente e tecnica, INCLUDILA.
    Voglio densità. Se ci sono 20 notizie, scrivine 20.
    
    REGOLE FORMATTAZIONE:
    1. Titoli in ITALIANO CORRETTO (Sentence case). 
       Esempio: "Nuova scoperta sui superconduttori"
    
    2. LINK: Usa ESATTAMENTE questo formato a fine paragrafo:
       **Fonte:** [Link](URL_ORIGINALE)
    
    3. VIETATO:
       - NON usare <hr>.
       - NON usare frasi introduttive.
       - NON scartare notizie solo perché sono brevi.
    
    FORMATO OUTPUT:
    ### [Titolo notizia]
    [Analisi tecnica e sintetica.]
    
    **Fonte:** [Link](URL)
    
    (Riga vuota)
    """
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"INPUT MASSIVO:\n{raw_text[:MAX_SECTION_CONTEXT]}"}
            ],
            temperature=0.3, # Alzato leggermente per essere meno restrittivo
            max_tokens=7000 
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error {cluster_key}: {e}")
        return ""

# --- 4. MAIN SEQUENCER ---
print("Avvio IL POLIMATE TITAN (High Volume Mode)...")
start_time = time.time()
italian_date = get_italian_date()
today_iso = datetime.datetime.now().strftime("%Y-%m-%d")

full_report = "" 

for key, info in CLUSTERS.items():
    print(f"\n--- Cluster: {info['name']} ---")
    raw_data = get_cluster_data(info['urls'])
    
    if raw_data:
        raw_text = "\n---\n".join(raw_data)
        analysis = analyze_cluster(key, info, raw_text)
        
        if analysis and len(analysis) > 50:
            full_report += f"\n\n## {info['name']}\n\n{analysis}\n"
        else:
            print("  > Nessun contenuto generato.")
    else:
        print("  > Nessun dato grezzo.")
    
    # Mantengo pausa alta perché stiamo inviando MOLTO testo
    print("  > Cooling down (35s)...")
    time.sleep(35)

# SALVATAGGIO
if not os.path.exists("_posts"):
    os.makedirs("_posts")

filename = f"_posts/{today_iso}-brief.md"

# RIMOSSO IL SOTTOTITOLO "Edizione Titan..."
markdown_file = f"""---
title: "La Rassegna del {italian_date}"
date: {today_iso}
layout: post
excerpt: "Analisi strategica quotidiana."
---

{full_report}
"""

if len(full_report) > 100:
    with open(filename, "w", encoding='utf-8') as f:
        f.write(markdown_file)
    print(f"\nDossier salvato: {filename}")
else:
    print("\nATTENZIONE: Report vuoto.")

duration = (time.time() - start_time) / 60
print(f"Tempo totale: {duration:.1f} minuti.")
