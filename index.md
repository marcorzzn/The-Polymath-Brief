---
layout: default
title: Home
---

<div class="masthead">
    <div class="masthead-top">EST. 2026</div>
    <h1 class="masthead-title">IL POLIMATE</h1>
    <div class="masthead-sub">L'essenziale strategico, ogni mattina.</div>
</div>

{% assign latest = site.posts.first %}
<div style="margin-bottom: 60px;">
    <div style="font-weight: 700; text-transform: uppercase; border-bottom: 2px solid #000; display: inline-block; margin-bottom: 10px;">
        La rassegna del {{ latest.date | date: "%-d" }} 
        {% assign month = latest.date | date: "%B" %}
        {% case month %}
        {% when 'January' %}gennaio
        {% when 'February' %}febbraio
        {% when 'March' %}marzo
        {% when 'April' %}aprile
        {% when 'May' %}maggio
        {% when 'June' %}giugno
        {% when 'July' %}luglio
        {% when 'August' %}agosto
        {% when 'September' %}settembre
        {% when 'October' %}ottobre
        {% when 'November' %}novembre
        {% when 'December' %}dicembre
        {% endcase %}
        {{ latest.date | date: "%Y" }}
    </div>
    
    <a href="{{ latest.url | relative_url }}" class="feature-title">
        {{ latest.title }}
    </a>
    
    <div class="scrolling-summary">
        <marquee behavior="scroll" direction="left" scrollamount="3">
            {{ latest.content | strip_html | truncate: 150 }}
        </marquee>
    </div>
    
    <a href="{{ latest.url | relative_url }}" class="read-btn">
        LEGGI LA RASSEGNA &rarr;
    </a>
</div>

<div style="border-top: 1px solid #ddd; padding-top: 30px;">
    <h4 class="archive-title">Archivio</h4>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px;">
        {% for post in site.posts offset:1 %}
        <div>
            <small style="color: #888;">
                {% assign day = post.date | date: "%-d" %}
                {% assign month = post.date | date: "%m" %}
                {{ day }}/{{ month }}
            </small><br>
            <a href="{{ post.url | relative_url }}" style="font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.2rem; color: #000; text-decoration: none;">
                {{ post.title }}
            </a>
        </div>
        {% endfor %}
    </div>
</div>
