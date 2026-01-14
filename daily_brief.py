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
MAX_WORKERS = 3  # Ridotto per maggiore stabilità
LOOKBACK_HOURS = 24
MAX_SECTION_CONTEXT = 35000

if not GROQ_API_KEY:
    print("⚠️ ATTENZIONE: GROQ_API_KEY non trovata.")

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

# ================== ENGINE DI RACCOLTA ==================
def fetch_feed(url):
    try:
        d = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        items = []
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(hours=LOOKBACK_HOURS)
        
        if not d.entries: return []

        for entry in d.entries:
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)
            
            if not pub_date or pub_date > cutoff:
                content = "No content"
                if hasattr(entry, 'summary'): content = entry.summary
                elif hasattr(entry, 'content'): content = entry.content[0].value
                elif hasattr(entry, 'description'): content = entry.description
                
                try:
                    soup = BeautifulSoup(content, "html.parser")
                    content = soup.get_text(separator=" ", strip=True)[:4000]
                except:
                    content = str(content)[:4000]

                source = d.feed.get('title', 'Fonte')
                link = entry.link
                items.append(f"SRC: {source}\nLINK: {link}\nTITLE: {entry.title}\nTXT: {content}\n")
        return items
    except Exception as e:
        print(f"  ⚠️ Errore nel fetch di {url[:50]}...: {e}")
        return []

def get_cluster_data(urls):
    data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(fetch_feed, urls)
        for res in results:
            data.extend(res)
    return data

# ================== ANALISTA AI ==================
def analyze_cluster(cluster_key, info, raw_text):
    if not raw_text: 
        print(f"  ⚠️ Nessun dato per {info['name']}")
        return ""
    
    print(f"  > Analisi {info['name']}...")
    
    # PROMPT MIGLIORATO: più notizie + link cliccabili
    system_prompt = f"""Sei un analista esperto del settore {info['name']}.

COMPITO:
1. Identifica le 4-6 notizie PIÙ RILEVANTI dalle fonti fornite
2. Per ogni notizia scrivi:
   - Titolo chiaro in italiano (sentence case)
   - Riassunto di 2-4 frasi che spiega il significato e l'impatto
   - Link alla fonte originale in formato cliccabile

FORMATO OBBLIGATORIO:
### [Titolo della notizia]
[Riassunto in 2-4 frasi...]

**Fonte:** [Vedi Fonte](URL_COMPLETO)

REGOLE CRITICHE:
- Il link DEVE essere in formato Markdown: [Vedi Fonte](URL)
- NON scrivere mai l'URL nudo (senza parentesi)
- NON usare <hr> o linee di separazione
- Titoli in italiano, chiari e informativi
- Almeno 4 notizie se i dati lo permettono

ESEMPIO CORRETTO:
### Nuovo algoritmo quantistico supera i classici
Ricercatori del MIT hanno sviluppato un algoritmo che...

**Fonte:** [Vedi Fonte](https://arxiv.org/abs/2601.12345)
"""
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"{system_prompt}\n\nDATI:\n{raw_text[:MAX_SECTION_CONTEXT]}"}],
            temperature=0.3, 
            max_tokens=6000  # Aumentato per più notizie
        )
        result = completion.choices[0].message.content
        
        # Verifica che ci siano notizie
        if "###" not in result:
            print(f"  ⚠️ Nessuna notizia generata per {info['name']}")
            return ""
            
        return result
    except Exception as e:
        print(f"  ❌ Errore AI su {cluster_key}: {e}")
        return ""

# ================== MAIN ==================
print("🚀 AVVIO POLIMATE...")
italian_date = get_italian_date()
try:
    tz = pytz.timezone("Europe/Rome")
    today_iso = datetime.datetime.now(tz).strftime("%Y-%m-%d")
except:
    today_iso = datetime.datetime.now().strftime("%Y-%m-%d")

report_parts = []
all_titles = []
clusters_with_content = 0

# PROCESSA TUTTI I CLUSTER
for key, info in CLUSTERS.items():
    print(f"\n{'='*60}")
    print(f"CLUSTER: {info['name']}")
    print(f"{'='*60}")
    
    try:
        raw_data = get_cluster_data(info['urls'])
        
        if raw_data:
            print(f"  ✓ Raccolti {len(raw_data)} articoli")
            raw_text = "\n---\n".join(raw_data)
            analysis = analyze_cluster(key, info, raw_text)
            
            if analysis and "###" in analysis:
                report_parts.append(f"\n## {info['name']}\n\n{analysis}\n")
                clusters_with_content += 1
                
                # Estrazione titoli per marquee
                lines = analysis.split('\n')
                for line in lines:
                    if line.strip().startswith("### "):
                        clean_title = line.replace("### ", "").strip()
                        all_titles.append(f"{info['name']}: {clean_title}")
                        
                print(f"  ✓ Analisi completata con successo")
            else:
                print(f"  ⚠️ Nessuna notizia rilevante trovata")
        else:
            print(f"  ⚠️ Nessun dato recente trovato")
            
    except Exception as e:
        print(f"  ❌ Errore nel cluster {key}: {e}")
        continue
        
    time.sleep(2)  # Pausa tra cluster

# REPORT FINALE
print(f"\n{'='*60}")
print(f"REPORT FINALE: {clusters_with_content}/{len(CLUSTERS)} cluster con contenuti")
print(f"{'='*60}")

# Creazione stringa scorrevole (primi 20 titoli)
marquee_text = " • ".join(all_titles[:20]) if all_titles else "Nessuna notizia rilevante oggi"

# SALVATAGGIO
if not os.path.exists("_posts"): 
    os.makedirs("_posts")
    
filename = f"_posts/{today_iso}-brief.md"
full_report = "".join(report_parts)

markdown_file = f"""---
title: "La rassegna del {italian_date}"
date: {today_iso}
layout: post
excerpt: "{marquee_text}"
---

{full_report if full_report else "Nessuna notizia rilevante trovata oggi."}
"""

with open(filename, "w", encoding='utf-8') as f:
    f.write(markdown_file)

print(f"\n✅ SALVATO: {filename}")
print(f"📊 Cluster elaborati: {clusters_with_content}/{len(CLUSTERS)}")
print(f"📰 Titoli nel marquee: {len(all_titles)}")
