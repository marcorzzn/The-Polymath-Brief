import os
import datetime
import time
import feedparser
import concurrent.futures
from groq import Groq

# ================= CONFIGURAZIONE =================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MAX_WORKERS = 20
LOOKBACK_HOURS = 30
MAX_SECTION_CONTEXT = 60000

if not GROQ_API_KEY:
    print("ERRORE: GROQ_API_KEY mancante")
    exit(1)

# ================= DATA IN ITALIANO =================
def get_italian_date():
    months = {
        1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile",
        5: "maggio", 6: "giugno", 7: "luglio", 8: "agosto",
        9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre"
    }
    now = datetime.datetime.now()
    return f"{now.day} {months[now.month]} {now.year}"

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

# ================= RACCOLTA FEED =================
def fetch_feed(url):
    try:
        d = feedparser.parse(url)
        items = []

        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(hours=LOOKBACK_HOURS)

        for entry in d.entries:
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_date = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)

            if not pub_date or pub_date > cutoff:
                content = ""
                if hasattr(entry, "summary"):
                    content = entry.summary
                elif hasattr(entry, "content"):
                    content = entry.content[0].value

                content = content.replace("<p>", "").replace("</p>", "").strip()[:3000]
                source = d.feed.get("title", "Fonte")
                link = entry.link

                items.append(
                    f"SRC: {source}\n"
                    f"LINK: {link}\n"
                    f"TITLE: {entry.title}\n"
                    f"TXT: {content}\n"
                )
        return items
    except:
        return []

def get_cluster_data(urls):
    data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(fetch_feed, urls)
        for r in results:
            data.extend(r)
    return data

# ================= ANALISI AI =================
def analyze_cluster(info, raw_text):
    if not raw_text:
        return ""

    system_prompt = f"""
SEI: Il Polimate
SETTORE: {info['name']}

OBIETTIVO:
Produrre una rassegna giornalistica tecnica e strategica di altissima qualità.

TITOLI:
- Italiano corretto
- SOLO la prima parola con iniziale maiuscola
- Nomi propri ammessi
- VIETATO lo stile Title Case inglese

QUANTITÀ:
- Almeno 3 notizie
- Idealmente 4–5 se possibile
- Vietato restituire sezioni quasi vuote

LINK:
- Solo Markdown: [Nome fonte](https://...)
- Vietati URL nudi

FORMATO OBBLIGATORIO:

### Titolo in italiano

Paragrafetto di analisi di 4–6 righe. Qui il testo FINISCE.

Fonte: [Nome della fonte](URL)

Dopo "Fonte:" si va subito a capo e si inizia una nuova notizia.
"""

    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text[:MAX_SECTION_CONTEXT]}
        ],
        temperature=0.25,
        max_tokens=7000
    )

    return completion.choices[0].message.content.strip()

# ================= MAIN =================
print("Avvio generazione rassegna")
start = time.time()

italian_date = get_italian_date()
today_iso = datetime.datetime.now().strftime("%Y-%m-%d")
full_report = ""

for _, info in CLUSTERS.items():
    raw_data = get_cluster_data(info["urls"])
    if raw_data:
        analysis = analyze_cluster(info, "\n---\n".join(raw_data))
        if analysis:
            full_report += f"\n\n## {info['name']}\n\n{analysis}\n"
    time.sleep(25)

# ================= SALVATAGGIO =================
os.makedirs("_posts", exist_ok=True)
filename = f"_posts/{today_iso}-brief.md"

markdown = f"""---
title: "La Rassegna del {italian_date}"
date: {today_iso}
layout: post
---

{full_report}
"""

if len(full_report) > 200:
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"File generato: {filename}")
else:
    print("ATTENZIONE: contenuto insufficiente")

print(f"Tempo totale: {(time.time() - start) / 60:.1f} minuti")
