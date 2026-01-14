---
layout: default
title: Home
---

<div style="text-align: center; margin-bottom: 40px;">
  <h1 style="font-family: 'Playfair Display', serif; font-size: 3em; margin-bottom: 5px;">IL POLIMATE</h1>
  <p style="font-size: 1.1em; color: #666; font-style: italic;">Fondato nel 2026 - Intelligence Strategica Quotidiana</p>
</div>

---

<h2 style="font-family: 'Inter', sans-serif; font-size: 1.2em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 20px;">
  ARCHIVIO RASSEGNE
</h2>

<ul style="list-style: none; padding: 0;">
  {% for post in site.posts %}
    <li style="margin-bottom: 25px; border-bottom: 1px solid #eee; padding-bottom: 20px;">
      
      {% assign months = "gennaio,febbraio,marzo,aprile,maggio,giugno,luglio,agosto,settembre,ottobre,novembre,dicembre" | split: "," %}
      {% assign m = post.date | date: "%-m" | minus: 1 %}
      
      <a href="{{ post.url | relative_url }}" style="font-size: 1.5em; font-weight: 700; text-decoration: none; color: #000; display: block; margin-bottom: 8px;">
        La rassegna del {{ post.date | date: "%-d" }} {{ months[m] }} {{ post.date | date: "%Y" }}
      </a>

      <div style="background: #f0f8ff; color: #0056b3; padding: 5px 10px; font-size: 0.9em; border-radius: 4px; border: 1px solid #d0e4f5;">
        <marquee behavior="scroll" direction="left" scrollamount="6">
          {{ post.excerpt | strip_html }}
        </marquee>
      </div>

    </li>
  {% endfor %}
</ul>
