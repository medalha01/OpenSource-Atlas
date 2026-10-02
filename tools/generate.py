#!/usr/bin/env python3
"""Generate the OpenSource Atlas README from the canonical dataset (data/projects.yaml).

This is the single source of truth -> Markdown renderer for the awesome list.
Run `make build` (or `python tools/generate.py`) after editing the dataset.
"""
import re, sys, pathlib
try:
    import yaml
except ImportError:
    yaml = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "projects.yaml"
OUT = ROOT / "README.md"

# --------------------------------------------------------------------- taxonomy
# Ordered category -> (emoji, one-line blurb, [ordered subcategories]).
TAXONOMY = [
 ("AI, Machine Learning & LLMs", "🤖", "Local model runtimes, agent frameworks, LLMOps, RAG, evaluation, serving, and the core ML/DL stack.",
  ["LLM Chat Interfaces & Local Runtimes","Agents & LLM App Frameworks","AI Coding Assistants & Agent Orchestrators",
   "Low-Code AI App Builders & Chatbots","LLMOps, Gateways & Inference","LLM Observability, Evaluation & Prompt Management",
   "AI Guardrails & Safety","Model Serving & Inference","GPU & AI Infrastructure","RAG, Crawling & Document AI",
   "ML, Deep Learning & Computer Vision Libraries","Image, Speech & Audio Generation","Data Labeling","MLOps"]),
 ("Analytics, Monitoring & Observability", "📊", "Product analytics, metrics, tracing, logs, errors, profiling, alerting, and incident response.",
  ["Web & Product Analytics","Observability Platforms & Tracing","OpenTelemetry & Instrumentation",
   "Frontend & RUM Monitoring","Continuous Profiling","eBPF Observability","Database Observability","API & Service Observability",
   "Metrics Storage","Log Management & Telemetry Pipelines","Error Tracking","Synthetic Monitoring",
   "Alert Management & Routing","Incident Management & On-Call","Monitoring Dashboards",
   "Uptime, Status Pages & Server Health","Homelab Dashboards"]),
 ("Authentication, Identity & Passwords", "🔐", "SSO, OAuth2/OIDC/SAML, authorization, identity governance, directories, passwords, and 2FA.",
  ["Identity Providers & SSO","Auth Services & Libraries","Authorization & Policy Engines","Identity Governance & Provisioning",
   "Directory Services (LDAP)","Password Managers & 2FA"]),
 ("Automation, Workflows & Orchestration", "⚙️", "No-/low-code automation, orchestration engines, job queues, schedulers, BPM, and internal tools.",
  ["Workflow Automation (No-/Low-Code)","Workflow Orchestration & Durable Execution","Background Jobs & Task Queues",
   "Job & Workflow Monitoring","Business Process & BPMN","Rules Engines","Distributed Scheduling",
   "Browser Automation","Internal Tools & Low-Code App Builders","Marketing & Social Media Automation"]),
 ("Backend Development", "🐍", "Server-side frameworks, API layers, and Backend-as-a-Service.",
  ["Web Frameworks","API & GraphQL","Backend as a Service"]),
 ("CLI Tools & Terminal", "🧰", "Command-line tools, shells, terminals, and system utilities.",
  ["Developer CLI Tools","File Management & Navigation","Package Managers & Version Managers",
   "Productivity & Workflow","Shells, Prompts & Terminal Environments","System Monitoring & Utilities"]),
 ("CMS, Blogging & Static Sites", "📚", "Content management systems, static site generators, and documentation sites.",
  ["Content Management Systems","Static Site Generators & Documentation Sites"]),
 ("Notes, Wikis & Knowledge Management", "📝", "Note-taking, PKM, wikis, collaborative editors, RSS, and bookmarks.",
  ["Note-Taking & Personal Knowledge Management","Wikis & Team Documentation","Collaborative Editors","RSS, Read-It-Later & Bookmarks"]),
 ("Databases", "🗄️", "Operational and analytical databases, search, vector stores, ORMs, migrations, pooling, and HA tooling.",
  ["Relational Databases","Distributed SQL","Key-Value & Cache Stores","In-Memory SQL Databases",
   "Document & NoSQL Databases","Multi-Model Databases","Graph Databases","Distributed Key-Value Stores",
   "Wide-Column Stores","Embedded Key-Value Stores","Search Engines","Streaming Databases",
   "Time-Series Databases","Columnar OLAP Databases","Real-Time OLAP Engines","In-Process OLAP Engines",
   "PostgreSQL OLAP Extensions","Vector Databases","ORMs & SQL Toolkits","Database Migrations & Schema Management",
   "Database Proxies & Connection Pooling","Database HA & Failover","No-Code & Spreadsheet Databases",
   "Database Clients, Admin & DevOps Tools"]),
 ("Storage, Backup & File Sync", "💾", "Object storage, distributed file systems, backup, disaster recovery, file transfer, sync, and media libraries.",
  ["Object Storage","Distributed File Systems","Backup & Transfer","Backup Orchestration & Disaster Recovery",
   "Database Backup & PITR","File Transfer Gateways","File Sync & Self-Hosted Cloud","File Managers & Photo Libraries"]),
 ("Data Lakehouse & File Formats", "🏞️", "Columnar/row formats, open table formats, and lakehouse interoperability.",
  ["Serialisation & File Formats","Open Table Formats","Native Open Table Format Libraries","Universal Lakehouse & Interoperability"]),
 ("Data Integration & Streaming", "🔄", "ETL/ELT, CDC, migrations, customer data routing, brokers, webhooks, and reverse ETL.",
  ["Data Integration Platforms","Change Data Capture (CDC)","Data Migration","Log & Event Collection",
   "Customer Data Platforms & Event Routing","Event Streaming & Message Brokers","Messaging Frameworks & Event Buses",
   "Event Streaming UIs & Broker Tooling","Webhook Infrastructure","Reverse ETL"]),
 ("Data Processing & Query Engines", "⚡", "Batch/stream engines, DataFrames, MPP query engines, and semantic layers.",
  ["Unified Batch & Stream Processing","Batch Processing","Stream Processing","Python DataFrame & Processing Frameworks",
   "Python Workflow Scaling","MPP & Distributed SQL Query Engines","Semantic & Middleware Layer","Data Sharing"]),
 ("DataOps, Quality & Metadata", "🧭", "Data quality, versioning, modeling, pipeline observability, catalogs, lineage, and registries.",
  ["Data Quality & Validation","Data Versioning","Data Modeling & Transformation","Pipeline Observability",
   "Metadata Platforms & Data Catalogs","Open Metadata Standards","Schema Registries & Table Catalogs"]),
 ("Data Science, BI & Visualization", "📈", "BI platforms, data apps, notebooks, and visualization/scientific libraries.",
  ["BI & Dashboards","BI as Code & Data Apps","Notebooks & Query Collaboration","Scientific Computing & Visualization Libraries"]),
 ("Developer Tools & IDEs", "🛠️", "Editors, Git forges, testing, API governance, build systems, developer environments, and portals.",
  ["Code Editors & IDEs","Version Control & Code Hosting","Linters, Formatters & Git Hooks","Monorepo & Build Tools",
   "API Clients & Testing","Load & Performance Testing","Contract Testing","Service Virtualization & Mocking",
   "API Governance & Documentation","Test Data Management","Cloud Development Environments",
   "Developer Portals & Service Catalogs","Snippets & Pastebins","Developer Utilities","Experimental Languages"]),
 ("DevOps & Infrastructure", "🖥️", "Containers, Kubernetes, GitOps, IaC, platform engineering, service networking, PaaS, registries, and real-time/VoIP infrastructure.",
  ["Containers & Virtualization","Kubernetes & Orchestration","Resource Scheduling & Cluster Management",
   "CI / CD","GitOps & Progressive Delivery","Infrastructure as Code","Platform Engineering & Control Planes",
   "Feature Flags & Remote Configuration","Chaos Engineering & Resilience Testing",
   "Web Servers, Reverse Proxies & Load Balancers","API Gateways & Service Networking","Service Mesh",
   "Distributed Application Runtimes","PaaS & Self-Hosting Platforms","Container & Package Registries",
   "Artifact Repositories & Package Proxies","Real-Time Communication Infrastructure",
   "WebRTC & Real-Time Media Servers","VoIP, SIP & Telephony","Messaging APIs & Gateways",
   "Service Discovery & Coordination","Cost Management"]),
 ("Networking, VPN & DNS", "🌐", "VPN/mesh networks, DNS, tunnels, traffic analysis, network automation, labs, routing, and source-of-truth tooling.",
  ["VPN & Mesh Networking","DNS, Ad Blocking & Filtering","Tunnels","Network Diagnostics & Web Analysis",
   "Packet Capture & Traffic Analysis","IPAM, DCIM & Network Source of Truth","Network Automation & Configuration",
   "Network Emulation & Labs","Routing & Network Operating Systems"]),
 ("Security & Privacy", "🔒", "AppSec, scanning, runtime/network defense, threat intelligence, DFIR, supply-chain security, PKI, secrets, and privacy.",
  ["Container & Kubernetes Security","Endpoint & Runtime Security","Network Security, IDS & SIEM",
   "Web Application Firewalls & AppSec","Bot Protection & Intrusion Prevention","Privacy & Anonymity",
   "Reverse Engineering & Pentesting","Secret Scanning & Credential Detection","Secrets Management & Encryption",
   "PKI & Certificate Automation","Software Supply Chain & SBOM","Cloud Security Posture & IaC Security",
   "Vulnerability Scanning & Static Analysis","Threat Intelligence & Incident Response","Digital Forensics & DFIR",
   "Malware Analysis & Detection","Data Platform Security & Access","Remote Access","Security Utilities"]),
 ("Frontend & Web Development", "📱", "UI frameworks, meta-frameworks, JS runtimes/tooling, state and data layers, forms, components, testing, performance, accessibility, and styling.",
  ["UI Frameworks","Meta-Frameworks","JavaScript Runtimes, Bundlers & Build Tools","State Management & Data Fetching",
   "Forms, Validation & Schemas","Web Components","Web Component UI Libraries","Web Testing & Component Development","Web Performance & Accessibility",
   "Desktop & Cross-Platform Apps","CSS Frameworks","CSS Tooling & Styling","React UI Libraries","Vue UI Libraries",
   "Angular UI Libraries","UI Components","Icons","Animation"]),
 ("Design & Prototyping", "🎨", "Design editors, diagramming/whiteboards, and UX research.",
  ["Design Tools","Diagramming & Whiteboards","UX Research & Prototyping"]),
 ("Media Servers & Streaming", "🎵", "Self-hosted media, music, audiobook, radio, and live-streaming servers.",
  ["Media Servers & Streaming"]),
 ("Productivity, Collaboration & Business", "🤝", "Project management, team chat, video conferencing, support, CRM, marketing, billing, forms, signing, and habits.",
  ["Project Management & Issue Tracking","Workspaces & Collaboration","Team Chat & Messaging Servers",
   "Video Conferencing & Voice Chat","Customer Support & Live Chat","CRM & Growth",
   "Email Marketing & Newsletters","Billing, Metering & Entitlements","Forms & Surveys","Document Signing","Time Tracking & Habits"]),
 ("Mobile Apps (Android)", "📲", "Open-source Android apps across every category.",
  ["Browsers & Internet","File Management & Utilities","Launchers & Customization","Media & Music",
   "Messaging & Communication","Password Managers & Security","Productivity & Notes","Video & Streaming"]),
 ("Learning Resources", "📖", "Roadmaps, books, interview prep, and curated references.",
  ["Learning Resources"]),
 ("IoT & Edge", "📡", "MQTT brokers, IoT platforms, device management, and edge connectivity.",
  ["MQTT Brokers & IoT Messaging","IoT Platforms & Device Management"]),
 ("Miscellaneous Utilities", "🧩", "Notifications, email infrastructure, translation/localization, and other handy tools.",
  ["Notifications","Email Infrastructure & SMTP Testing","Translation & Localization","Other Utilities"]),
]
CAT_ORDER = [c[0] for c in TAXONOMY]

def slug(t):
    return re.sub(r"[^a-z0-9]+","-",t.lower()).strip("-")
def gh_repo(url):
    m = re.match(r"https?://github\.com/([^/]+)/([^/#?]+)", url)
    return f"{m.group(1)}/{m.group(2)}" if m else None
def stars_badge(url):
    r = gh_repo(url)
    return (f"![★](https://img.shields.io/github/stars/{r}?style=flat-square&color=f4c542&labelColor=1c1c1c&label=%E2%98%85)"
            if r else "—")
def esc(s): return s.replace("|","\\|")

# --------------------------------------------------------------------- load data
def load():
    if yaml is None:
        sys.exit("PyYAML required: pip install pyyaml")
    docs = list(yaml.safe_load_all(DATA.read_text(encoding="utf-8")))
    rows = docs[0]
    for r in rows:
        r.setdefault("alt", []); r.setdefault("status", [])
        assert r["cat"] in CAT_ORDER, f"unknown category {r['cat']!r} for {r['name']}"
        subs = dict(zip(CAT_ORDER,[t[3] for t in TAXONOMY]))[r["cat"]]
        assert r["sub"] in subs, f"unknown subcategory {r['sub']!r} in {r['cat']} for {r['name']}"
    return rows

def render(rows):
    from collections import defaultdict, Counter
    for r in rows:
        r.setdefault("alt", []); r.setdefault("status", [])
    placed = defaultdict(lambda: defaultdict(list))
    for r in rows: placed[r["cat"]][r["sub"]].append(r)
    total = len(rows)
    n_cat = sum(1 for c in CAT_ORDER if placed[c])
    n_sub = sum(1 for c,_ ,_,subs in TAXONOMY for s in subs if placed[c][s])

    o=[]; W=o.append
    # ---- header
    W('<div align="center">\n')
    W('<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Milky%20Way.png" width="90" alt="Atlas"/>\n')
    W("# ✦ OpenSource Atlas ✦\n")
    W("### The curated atlas of production-grade open-source software.\n")
    W("*One place to find the tool for the job — curated open-source projects, status-labelled and linked straight to their source repositories.*\n")
    badges = [
      "https://img.shields.io/badge/projects-{}-f4c542?style=for-the-badge&labelColor=1c1c1c".format(total),
      "https://img.shields.io/badge/categories-{}-4c9aff?style=for-the-badge&labelColor=1c1c1c".format(n_cat),
      "https://img.shields.io/badge/license-CC0--1.0-brightgreen?style=for-the-badge&labelColor=1c1c1c",
      "https://awesome.re/badge-flat2.svg",
    ]
    W(" ".join(f"![b]({b})" if "awesome" not in b else f"[![Awesome]({b})](https://awesome.re)" for b in badges) + "\n")
    W("[**Browse categories ↓**](#-categories) &nbsp;·&nbsp; [**Add a project**](CONTRIBUTING.md) &nbsp;·&nbsp; [**Report a dead link**](../../issues/new?template=broken-link.yml) &nbsp;·&nbsp; [**Security**](SECURITY.md)\n")
    W("</div>\n\n---\n")

    # ---- pitch
    W("## 💡 What this is\n")
    W("Finding the right open-source tool usually means wading through blog spam, dead links, and abandoned repos. "
      "**OpenSource Atlas** is a single, structured directory that cuts straight to the source.\n")
    W("| | |\n|---|---|")
    W(f"| 🗂️ **{n_cat} categories, {n_sub} subcategories** | From AI and databases to security, self-hosting, and mobile — organized so you can navigate by the problem you're solving. |")
    W("| 🔗 **Direct repository links** | Every entry points at the actual source repo. No aggregators, no paywalls, no redirects. |")
    W("| ✅ **Maintained & open source** | Entries must have a clear OSI/free license and recent activity. Inactive and archived projects are labelled, not hidden. |")
    W("| 🤖 **Automatically checked** | Pull requests run deterministic schema/build validation, while scheduled CI performs external link checks (see [`tools/`](tools)). |")
    W("| 🧩 **Data-driven** | The list is generated from a single [`data/projects.yaml`](data/projects.yaml); the README you're reading is a build artifact. |")
    W("| 🆓 **Public domain** | Released under [CC0-1.0](LICENSE) — copy, fork, embed, and build on it freely. |")
    W(f"\n> ⭐ **If this saves you time, please [star the repo](../../stargazers).** It takes two seconds and helps other developers find it.\n")
    W(f"<sub>Projects: {total} · Categories: {n_cat} · Subcategories: {n_sub}</sub>\n\n---\n")

    # ---- legend
    W("## 🧭 How to read an entry\n")
    W("```\n| [**Project Name**](https://github.com/owner/repo)  <description of what it does>  ★ 12,345 |\n```")
    W("| Marker | Meaning |\n|---|---|")
    W("| ★ badge | Live GitHub star count (updates automatically via shields.io). |")
    W("| `⚠️ inactive` | No significant activity recently — usable, but unlikely to receive updates. |")
    W("| `⛔ archived` | Repository is archived/read-only upstream. Included for reference and migration. |")
    W("| <sub>mirror:</sub> | An additional/mirror repository URL for the same project. |")
    W("| — | Not hosted on GitHub (e.g. GitLab, Codeberg, self-hosted forge), so no star badge is shown. |")
    W("\n---\n")

    # ---- categories index
    W('<a id="-categories"></a>\n## 📚 Categories\n')
    W("<table>")
    cols = 2
    cells = []
    for c, emoji, _, subs in TAXONOMY:
        if not placed[c]: continue
        cnt = sum(len(placed[c][s]) for s in subs)
        cells.append(f'<td valign="top" width="50%">\n\n**{emoji} [{c}](#{slug(c)})** · {cnt}\n\n' +
                     "".join(f"- [{s}](#{slug(s)}) `{len(placed[c][s])}`\n" for s in subs if placed[c][s]) + "\n</td>")
    for i in range(0, len(cells), cols):
        W("<tr>" + "".join(cells[i:i+cols]) + "</tr>")
    W("</table>\n")
    W("**Reference:** [Contributing](CONTRIBUTING.md) · [Code of Conduct](CODE_OF_CONDUCT.md) · [License](LICENSE)\n\n---\n")

    # ---- body
    for c, emoji, blurb, subs in TAXONOMY:
        if not placed[c]: continue
        cnt = sum(len(placed[c][s]) for s in subs)
        W(f'<a id="{slug(c)}"></a>\n## {emoji} {c}\n')
        W(f"> {blurb} · **{cnt} projects**\n")
        for s in subs:
            ps = placed[c][s]
            if not ps: continue
            W(f'<a id="{slug(s)}"></a>\n### {s}\n')
            W("| Project | Description | Stars |\n|---|---|---|")
            for p in sorted(ps, key=lambda p: re.sub(r"[^a-z0-9]","",p["name"].lower())):
                name = f"[**{esc(p['name'])}**]({p['url']})"
                fl=""
                for st in p["status"]:
                    low=st.lower()
                    if "archiv" in low: fl+=" `⛔ archived`"
                    elif "inactiv" in low: fl+=" `⚠️ inactive`"
                    else: fl+=f" `{st}`"
                if p["alt"]:
                    name += "<br><sub>mirror: " + " · ".join(
                        f"[{gh_repo(u) or re.sub(r'^https?://','',u)}]({u})" for u in p["alt"]) + "</sub>"
                W(f"| {name}{fl} | {esc(p['desc'])} | {stars_badge(p['url'])} |")
            W("")
        W("**[⬆ Back to categories](#-categories)**\n\n---\n")

    # ---- footer sections
    W("## 🤝 Contributing\n")
    W("Contributions are what keep this atlas useful. Adding a project is a small edit to one YAML file:\n")
    W("1. Fork the repo and branch: `feat/add-project-name`.")
    W("2. Add an entry to [`data/projects.yaml`](data/projects.yaml) under the right `cat` / `sub` (see the schema at the top of the file).")
    W("3. Run `make build` to regenerate `README.md`, then `make check` to validate schema, ordering, and generated output.")
    W("4. Open a PR titled `Add <Project> to <Category>`.\n")
    W("Full rules, the acceptance checklist, and the field reference live in **[CONTRIBUTING.md](CONTRIBUTING.md)**. "
      "Please also read our **[Code of Conduct](CODE_OF_CONDUCT.md)** and **[Security Policy](SECURITY.md)**.\n")
    W("## 📜 License\n")
    W("[![CC0-1.0](https://licensebuttons.net/p/zero/1.0/88x31.png)](LICENSE)\n")
    W("To the extent possible under law, the maintainers have waived all copyright and related rights to this "
      "curated list under the **[Creative Commons CC0 1.0 Universal](LICENSE)** dedication. The listed projects "
      "remain under their own respective licenses.\n")
    W('<div align="center">\n\n**Built for the developer community.** · [Add a project](CONTRIBUTING.md) · [Report a dead link](../../issues) · [Star it ⭐](../../stargazers)\n\n</div>')

    return "\n".join(o) + "\n"

def main():
    rows = load()
    md = render(rows)
    OUT.write_text(md, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} — {len(rows)} projects, {len(md.encode())} bytes")

if __name__ == "__main__":
    main()
