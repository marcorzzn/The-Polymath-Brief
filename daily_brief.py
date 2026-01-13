import os
import datetime
import time
import feedparser
import concurrent.futures
from groq import Groq
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

# ================== CONFIGURAZIONE ==================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MAX_WORKERS = 50
LOOKBACK_HOURS = 30  # ⬆️⬆️ 3 GIORNI per avere MOLTO materiale
MAX_SECTION_CONTEXT = 60000

if not GROQ_API_KEY:
    raise RuntimeError("ERRORE: GROQ_API_KEY mancante")

# ================== DATA ITALIANA ==================
def get_italian_date():
    mesi = {
        1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile",
        5: "maggio", 6: "giugno", 7: "luglio", 8: "agosto",
        9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre"
    }
    # Use Rome timezone
    now = datetime.datetime.now(ZoneInfo("Europe/Rome"))
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
        d = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) PolymathBot/3.0")
        items = []
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(hours=LOOKBACK_HOURS)
        
        for entry in d.entries:
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)
            
            if not pub_date or pub_date > cutoff:
                content = "No content"
                if hasattr(entry, 'summary'): 
                    content = entry.summary
                elif hasattr(entry, 'content'): 
                    content = entry.content[0].value
                elif hasattr(entry, 'description'): 
                    content = entry.description
                
                # Clean HTML content using BeautifulSoup
                try:
                    soup = BeautifulSoup(content, "html.parser")
                    content = soup.get_text(separator=" ", strip=True)[:5000]
                except Exception:
                    # Fallback to simple cleanup if bs4 fails for some reason
                    content = content.replace("<p>", "").replace("</p>", "").replace("<div>", "").strip()[:5000]

                source = d.feed.get('title', 'Fonte')
                link = entry.link
                items.append(f"SRC: {source}\nLINK: {link}\nTITLE: {entry.title}\nTXT: {content}\n")
        
        return items
    except Exception as e:
        return []

def get_cluster_data(urls):
    data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(fetch_feed, urls)
        for res in results:
            data.extend(res)
    return data

# ================== ANALISTA AI CON RETRY ==================
def analyze_cluster(cluster_key, info, raw_text, attempt=1):
    if not raw_text: 
        return ""
    
    print(f"  > Tentativo {attempt} - Analisi {cluster_key} ({len(raw_text)} chars)...")
    
    # PROMPT ULTRA-SPECIFICO CON ESEMPI
    system_prompt = f"""Sei un analista che deve scrivere da 2 a 4 notizie principali (basate sulla rilevanza) per il settore: {info['name']}

ESEMPIO DI OUTPUT RICHIESTO (copia questo stile):

### Nuova vulnerabilità scoperta nei sistemi di machine learning
Ricercatori di Stanford hanno identificato una falla critica che permette di manipolare output di modelli linguistici. Il problema riguarda il layer di attenzione in architetture transformer. Patch disponibile entro febbraio.

Fonte: [https://hai.stanford.edu/news/security-flaw](https://hai.stanford.edu/news/security-flaw)

### Google presenta framework per training distribuito
Il nuovo sistema riduce i tempi di addestramento del 40% su cluster GPU. Utilizza tecniche di parallelizzazione dinamica e ottimizzazione della memoria. Release pubblica prevista Q2 2026.

Fonte: [https://research.google/blog/distributed-training](https://research.google/blog/distributed-training)

### Microsoft investe in startup europea di AI etica
Accordo da 50 milioni per sviluppare sistemi di auditing automatico. Focus su bias detection e trasparenza algoritmica. Primo prodotto atteso entro 6 mesi.

Fonte: [https://microsoft.com/news/ai-ethics-investment](https://microsoft.com/news/ai-ethics-investment)

---

REGOLE CAPITALIZZAZIONE ITALIANA:
- "Nuova vulnerabilità" (NON "Nuova Vulnerabilità")
- "Google presenta" (NON "Google Presenta")  
- "Microsoft investe" (NON "Microsoft Investe")
- Ma: Google, Microsoft, AI, GPU, Bill Gates (nomi propri e sigle sempre maiuscoli)

FORMATO:
### [REGOLE CAPITALIZZAZIONE ITALIANA]
[2-3 righe analisi]

Fonte: [URL](URL)

IMPORTANTE: Devi produrre DA 2 A 4 blocchi come sopra. Seleziona le notizie più rilevanti. Se ci sono notizie eccezionali, fanne fino a 4.

MATERIALE DA ANALIZZARE:
{raw_text[:MAX_SECTION_CONTEXT]}

RISPONDI ORA CON LE NOTIZIE:"""
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": system_prompt}
            ],
            temperature=0.5,
            max_tokens=8000
        )
        
        result = completion.choices[0].message.content
        
        # ✅ CONTA NOTIZIE
        news_count = result.count("###")
        print(f"  📊 Notizie generate: {news_count}")
        
        # 🔄 RETRY SE TROPPO POCHE
        if news_count < 2 and attempt < 2:
            print(f"  ⚠️ Insufficiente, ritento...")
            time.sleep(5)
            return analyze_cluster(cluster_key, info, raw_text, attempt + 1)
        
        # 📝 MOSTRA PRIME 500 CHAR per debug
        print(f"  📄 Preview: {result[:500]}...")
        
        return result
        
    except Exception as e:
        print(f"  ❌ Errore: {e}")
        return ""

# ================== MAIN SEQUENCER ==================
print("🚀 IL POLIMATE - Versione DEBUG\n")
start_time = time.time()
italian_date = get_italian_date()
today_iso = datetime.datetime.now(ZoneInfo("Europe/Rome")).strftime("%Y-%m-%d")

full_report = ""
total_news = 0
stats = {}

for key, info in CLUSTERS.items():
    print(f"\n{'='*70}")
    print(f"📂 [{key}] {info['name']}")
    print(f"{'='*70}")
    
    # RACCOGLI DATI
    raw_data = get_cluster_data(info['urls'])
    print(f"  📥 Feed raccolti: {len(raw_data)} items")
    
    if len(raw_data) == 0:
        print(f"  ⚠️ NESSUN DATO - Possibile problema feed RSS")
        stats[key] = 0
        continue
    
    # MOSTRA PRIMI 3 TITOLI per verifica
    for i, item in enumerate(raw_data[:3]):
        title_line = [line for line in item.split('\n') if line.startswith('TITLE:')]
        if title_line:
            print(f"    - {title_line[0][:80]}...")
    
    # ANALIZZA
    raw_text = "\n---\n".join(raw_data)
    analysis = analyze_cluster(key, info, raw_text)
    
    if analysis and len(analysis) > 100:
        news_count = analysis.count("###")
        total_news += news_count
        stats[key] = news_count
        full_report += f"\n\n## {info['name']}\n\n{analysis}\n"
        print(f"  ✅ Sezione completata: {news_count} notizie")
    else:
        print(f"  ❌ Analisi fallita o vuota")
        stats[key] = 0
    
    print("  ⏳ Pausa 25s...")
    time.sleep(25)

# ================== REPORT FINALE ==================
print(f"\n{'='*70}")
print("📊 STATISTICHE FINALI")
print(f"{'='*70}")
for key, count in stats.items():
    status = "✅" if count >= 2 else "⚠️" if count == 1 else "❌"
    print(f"{status} {key}: {count} notizie")
print(f"\n🎯 TOTALE: {total_news} notizie generate")

# ================== SALVATAGGIO ==================
if not os.path.exists("_posts"):
    os.makedirs("_posts")

filename = f"_posts/{today_iso}-brief.md"

excerpt = f"Panoramica giornaliera su AI, quantum computing, cybersecurity, semiconduttori, biotech, difesa ed energia."

markdown_file = f"""---
title: "La rassegna del {italian_date}"
date: {today_iso}
layout: post
excerpt: "{excerpt}"
---

{full_report}
"""

with open(filename, "w", encoding='utf-8') as f:
    f.write(markdown_file)

print(f"\n💾 File salvato: {filename}")
print(f"⏱️ Tempo: {(time.time() - start_time) / 60:.1f} min\n")
