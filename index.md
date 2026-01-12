---
layout: default
title: Home
---

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<style>
    /* NASCONDE L'HEADER DI DEFAULT DEL TEMA JEKYLL */
    header { display: none !important; }
    
    /* RESET BASE */
    body {
        background-color: #f9f9f9;
        color: #111;
        transition: background 0.3s, color 0.3s;
    }

    /* CONTROLLI IN ALTO A DESTRA */
    .top-controls {
        position: absolute;
        top: 20px;
        right: 20px;
        display: flex;
        gap: 15px;
        z-index: 1000;
        font-family: 'Inter', sans-serif;
    }

    .control-btn {
        background: transparent;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 5px 12px;
        cursor: pointer;
        font-size: 0.8em;
        font-weight: 600;
        text-transform: uppercase;
        color: #555;
        transition: all 0.2s;
    }

    .control-btn:hover {
        background: #000;
        color: #fff;
        border-color: #000;
    }

    /* HEADER GIORNALE */
    .paper-header {
        text-align: center; 
        margin-bottom: 50px; 
        padding-top: 40px; /* Spazio extra perché abbiamo tolto l'header default */
        padding-bottom: 20px; 
        border-bottom: 4px double #111;
    }

    .kicker {
        font-family: 'Inter', sans-serif; 
        font-size: 0.75em; 
        letter-spacing: 3px; 
        text-transform: uppercase; 
        color: #666; 
        margin-bottom: 5px;
    }

    .brand-title {
        font-family: 'Playfair Display', serif; 
        font-size: 4.5em; 
        font-weight: 900; 
        letter-spacing: -2px; 
        margin: 0; 
        line-height: 0.9; 
        color: #111;
    }

    .payoff {
        font-family: 'Playfair Display', serif; 
        font-style: italic; 
        font-size: 1.3em; 
        color: #444; 
        margin-top: 10px;
    }

    /* LISTA ARTICOLI */
    .post-item {
        margin-bottom: 35px; 
        padding-bottom: 25px; 
        border-bottom: 1px solid #ddd;
    }

    .date-badge {
        background-color: #111; 
        color: #fff; 
        padding: 4px 8px; 
        font-family: 'Inter', sans-serif;
        font-size: 0.7em; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 1px;
    }

    .post-link {
        display: block; 
        margin-top: 15px; 
        font-family: 'Playfair Display', serif; 
        font-size: 2em; 
        font-weight: 700; 
        color: #111; 
        text-decoration: none; 
        line-height: 1.1;
        transition: color 0.2s;
    }

    .post-link:hover {
        color: #555;
    }

    .post-desc {
        margin-top: 10px; 
        font-family: 'Inter', sans-serif;
        font-size: 1.05em; 
        color: #444; 
        line-height: 1.6;
    }

    .read-more {
        color: #c00; /* Rosso editoriale */
        font-weight: 600;
        font-size: 0.9em;
        text-decoration: none;
        margin-left: 5px;
        border-bottom: 1px solid transparent;
        transition: border-bottom 0.2s;
    }
    
    .read-more:hover {
        border-bottom: 1px solid #c00;
    }

    /* DARK MODE STYLES */
    body.dark-mode {
        background-color: #1a1a1a;
        color: #e0e0e0;
    }
    body.dark-mode .brand-title { color: #f0f0f0; }
    body.dark-mode .paper-header { border-bottom-color: #444; }
    body.dark-mode .post-link { color: #f0f0f0; }
    body.dark-mode .post-link:hover { color: #bbb; }
    body.dark-mode .post-desc { color: #aaa; }
    body.dark-mode .date-badge { background-color: #f0f0f0; color: #000; }
    body.dark-mode .kicker, body.dark-mode .payoff { color: #888; }
    body.dark-mode .control-btn { border-color: #444; color: #aaa; }
    body.dark-mode .control-btn:hover { background: #fff; color: #000; }
    
    /* OVERRIDE GOOGLE TRANSLATE STYLE (Per nasconderlo parzialmente) */
    .goog-te-gadget-simple {
        background-color: transparent !important;
        border: none !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* MOBILE RESPONSIVE */
    @media (max-width: 600px) {
        .brand-title { font-size: 3em; }
        .top-controls { position: static; justify-content: center; margin-bottom: 20px; }
        .paper-header { padding-top: 10px; }
    }
</style>

<div class="top-controls">
    <button class="control-btn" onclick="toggleDarkMode()" id="darkBtn">Moon / Dark</button>
    <div id="google_translate_element"></div>
</div>

<div class="paper-header">
    <div class="kicker">EST. 2026 &mdash; STRATEGIC INTELLIGENCE</div>
    <h1 class="brand-title">IL POLIMATE</h1>
    <div class="payoff">L'essenziale strategico, ogni mattina.</div>
</div>

<div style="max-width: 800px; margin: 0 auto;">
    <h3 style="font-family: 'Inter', sans-serif; border-left: 4px solid #c00; padding-left: 10px; margin-bottom: 30px; text-transform: uppercase; font-size: 0.9em; letter-spacing: 1px; color: #333;">
        Ultime Edizioni
    </h3>

    <ul style="list-style: none; padding: 0;">
      {% for post in site.posts %}
        <li class="post-item">
            
            <span class="date-badge">
                {{ post.date | date: "%d %b %Y" }}
            </span>

            <a href="{{ post.url | relative_url }}" class="post-link">
                {{ post.title }}
            </a>

            <div class="post-desc">
                Analisi profonda su Frontiera Scientifica, Hardware e Geopolitica.
                <a href="{{ post.url | relative_url }}" class="read-more">
                    Leggi il dossier &rarr;
                </a>
            </div>

        </li>
      {% endfor %}
    </ul>
</div>

<div style="text-align: center; margin-top: 60px; font-size: 0.8em; color: #888; border-top: 1px solid #eee; padding-top: 20px; font-family: 'Inter', sans-serif;">
    IL POLIMATE &copy; 2026 &bull; REDAZIONE ALGORITMICA
</div>

<script>
    // --- DARK MODE LOGIC ---
    function toggleDarkMode() {
        document.body.classList.toggle("dark-mode");
        const btn = document.getElementById("darkBtn");
        
        // Salva preferenza
        if (document.body.classList.contains("dark-mode")) {
            localStorage.setItem("theme", "dark");
            btn.innerText = "Sun / Light";
        } else {
            localStorage.setItem("theme", "light");
            btn.innerText = "Moon / Dark";
        }
    }

    // Carica preferenza all'avvio
    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark-mode");
        document.getElementById("darkBtn").innerText = "Sun / Light";
    }

    // --- GOOGLE TRANSLATE ---
    function googleTranslateElementInit() {
        new google.translate.TranslateElement({
            pageLanguage: 'it', 
            layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
            autoDisplay: false
        }, 'google_translate_element');
    }
</script>
<script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
