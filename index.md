---
layout: default
title: Home
---

<style>
    /* HEADER SPECIFICO HOME */
    .masthead {
        text-align: center;
        border-bottom: 4px double #000;
        padding-bottom: 30px;
        margin-bottom: 50px;
        margin-top: 20px;
    }
    .masthead-top {
        font-family: 'Inter', sans-serif; font-size: 0.75rem; letter-spacing: 2px;
        text-transform: uppercase; color: #555; margin-bottom: 10px;
    }
    .masthead-title {
        font-family: 'Playfair Display', serif; font-size: 5rem; font-weight: 900;
        letter-spacing: -2px; margin: 0; line-height: 0.9;
    }
    .masthead-sub {
        font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.4rem;
        color: #444; margin-top: 10px;
    }

    /* ARTICOLO IN EVIDENZA */
    .feature-title {
        font-family: 'Playfair Display', serif; font-size: 3rem; font-weight: 700;
        line-height: 1.1; color: #000; text-decoration: none; display: block; margin-bottom: 15px;
    }
    .read-btn {
        display: inline-block; background: #000; color: #fff; padding: 10px 20px;
        font-weight: 600; text-decoration: none; border-radius: 4px; margin-top: 10px;
    }
    
    /* DARK MODE OVERRIDES */
    body.dark-mode .masthead { border-bottom-color: #fff; }
    body.dark-mode .masthead-title, body.dark-mode .feature-title { color: #fff; }
    body.dark-mode .read-btn { background: #fff; color: #000; }
</style>

<div class="masthead">
    <div class="masthead-top">Est. 2026 &mdash; Daily Strategic Intelligence</div>
    <h1 class="masthead-title">IL POLIMATE</h1>
    <div class="masthead-sub">L'essenziale strategico, ogni mattina.</div>
</div>

{% assign latest = site.posts.first %}
<div style="margin-bottom: 60px;">
    <div style="font-weight: 700; text-transform: uppercase; border-bottom: 2px solid #000; display: inline-block; margin-bottom: 10px;">
        {{ latest.date | date: "%d %B %Y" }}
    </div>
    
    <a href="{{ latest.url | relative_url }}" class="feature-title">
        {{ latest.title }}
    </a>
    
    <!-- Sottotitolo rimosso come richiesto -->
    
    <a href="{{ latest.url | relative_url }}" class="read-btn">
        LEGGI IL DOSSIER &rarr;
    </a>
</div>

<div style="border-top: 1px solid #ddd; padding-top: 30px;">
    <h4 style="text-transform: uppercase; letter-spacing: 1px; color: #666;">Archivio</h4>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px;">
        {% for post in site.posts offset:1 %}
        <div>
            <small style="color: #888;">{{ post.date | date: "%d/%m" }}</small><br>
            <a href="{{ post.url | relative_url }}" style="font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.2rem; color: #000; text-decoration: none;">
                {{ post.title }}
            </a>
        </div>
        {% endfor %}
    </div>
</div>
