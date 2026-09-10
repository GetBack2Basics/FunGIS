# FunGIS Community & Projects Repository

This repository documents integrated geospatial technology, community engagement, and spatial innovation work delivered with and during tenure with the **Far North GIS User Group (FunGIS)** — Australia's longest-running GIS user group, founded in **1988** and incorporated in **1990**.

It highlights a practice-based community leadership track that combines professional GIS delivery, event coordination, spatial analytics, and open-source tooling to strengthen the GIS community across regional Australia and build bridges between traditional enterprise GIS and emerging cloud-native spatial technologies.

---

## About FunGIS: A 35-Year Legacy

### Far North Queensland GIS Group Inc (FunGIS)

**Founded:** 1988 | **Incorporated:** 1990 | **Status:** Australia's longest-running GIS user group (35+ years)

FunGIS is a regional community of GIS professionals, researchers, and practitioners across northern Queensland and beyond. The group focuses on:

- Advancing GIS knowledge and best practices through collaborative learning
- Sharing enterprise and open-source GIS workflows
- Bridging traditional cartographic and data-driven analysis approaches
- Supporting regional planning, environmental management, and community initiatives
- Experimenting with emerging spatial technologies and cloud-native architectures

**Founding Members:** Bob Peever (surveyor, Atherton Tablelands) and Les Searle (consultant, Cairns) — both continuing to engage with the community decades later, reflecting FunGIS's remarkable legacy of volunteer-driven spatial innovation.

**Key Community Values:**
- **Practical, reusable knowledge** — tooling and workflows designed to be reproducible and adapted across contexts
- **Open-source-first philosophy** — leveraging QGIS, PostGIS, and modern open spatial stacks alongside enterprise tools
- **Regional empowerment** — making advanced spatial analysis and cloud technologies accessible beyond major metropolitan centers
- **Experimentation culture** — safe spaces to prototype, fail fast, and learn from spatial innovation
- **Safety and rigor** — particularly in statutory GIS and infrastructure planning, where hallucinated data is fatal

---

## Featured Projects & Community Leadership

### 🎯 **FunGIS Spatial Olympics** (Co-Led, 3+ Years)

**Annual Competitive Spatial Challenge Event** — Co-leading an innovative, gamified spatial competition that brings together regional GIS professionals and emerging talent.

**Purpose & Impact:**
- Strengthen regional GIS networks through friendly competition
- Demonstrate cutting-edge spatial technologies and rendering techniques
- Create approachable entry points for GIS learners and emerging professionals
- Showcase innovation in geospatial analysis, visualization, and data engineering

**Your Co-Leadership Role:**
- Co-lead organizer alongside Will Dean and FunGIS executive
- Technical infrastructure design and innovation
- Integration of emerging tools (AI-assisted pipelines, cloud spatial SQL, interactive visualization)
- Mentorship and knowledge sharing with competitors and community

**Associated Repositories & Initiatives:**

#### 📐 **[FunGIS_SpatialOlympics26_MapInABox](https://github.com/GetBack2Basics/FunGIS_SpatialOlympics26_MapInABox)**

**SpatialOlympics3 Team Photo EXIF Audit Pipeline** — a self-contained, repeatable pipeline for competition photo metadata extraction and interactive audit reporting.

- **Purpose:** Validate photo submissions, extract geospatial metadata, and provide real-time audit feedback to competition organizers and participants.
- **Tech Stack:** Python (Pillow, pillow-heif for HEIC/HEIF), Leaflet (local vendor), AlaSQL (in-browser SQL queries), HTML template injection.
- **Key Features:**
  - Per-team EXIF CSV extraction (coordinates, timestamp, camera metadata, SHA-256 content hash)
  - Interactive HTML report: Leaflet map (team-colored markers, numbered capture order, photo + metadata popups)
  - Capture-order time-slider with ▶ Play for temporal sequencing
  - Team Submission Scorecard: geotag coverage %, timestamp coverage %, camera consistency, duplicate-file detection
  - SQL Explorer tab (in-browser AlaSQL queries with autocomplete, draggable command palette, result export as CSV)
  - "Ask AI" box generates copy-paste prompts for LLM SQL synthesis
  - Vendored dependencies (Leaflet, AlaSQL, local fonts) = zero third-party load-time requests; map tiles only
  - Repeatable: `python extract_exif.py && python build_exif_report.py` after new submissions
- **Status:** Active for FunGIS Spatial Olympics 2026 event · Started 08/2026

---

#### 🎮 **[SplatOlympics](https://github.com/GetBack2Basics/SplatOlympics)**

**FunGIS Spatial Game Using Gaussian Blur Rendering** — applying GIS techniques to gamified spatial challenges.

- **Purpose:** Create an engaging, shareable spatial game that demonstrates geospatial rendering techniques in a competitive, accessible context.
- **Tech Stack:** TypeScript, Gaussian blur rendering, interactive challenge mechanics.
- **Key Features:**
  - Real-time blur-based spatial puzzles
  - Competitive leaderboards
  - Shareable challenge links
  - Spatial reasoning and pattern recognition gameplay
- **Status:** FunGIS Spatial Olympics 2026 experiment · Started 08/2026

---

### 🛰️ **National Spatial Infrastructure & AI Safeguards**

#### LinkedIn Presentation: ["What happens when you ask an AI agent to build a national spatial pipeline?"](https://www.linkedin.com/feed/update/urn:li:activity:7500769842455531520/)

**FunGIS 2026 Conference Presentation**

**Core Insight:** AI agents can silently hallucinate spatial data—applying Sydney coordinates to Victorian layers, mocking API responses, simulating success. In national infrastructure siting and statutory GIS, hallucinated data is fatal.

**The Problem:**
- Heavy CRS transforms (GDA2020), multi-hazard overlays, API latency
- Unconstrained AI agents silently mock responses and simulate success
- Traditional QA methods insufficient for scale and speed

**The Solution: The Human-AI Triad Architecture**

1. **The Orchestrator** (Human Intent)
   - Sets statutory thresholds and canonical themes
   - Establishes universal EPSG:7844 baselines
   - Defines decision criteria and constraints

2. **The AI Engine** (High-Speed Translation)
   - Translates intent into declarative configs and ETL scripts
   - Generates differential sync tools
   - Accelerates problem-solving and code generation

3. **The QA Gate** (Human Safety Valve)
   - Holds commit keys
   - Enforces live count reconciliation before write-backs
   - Validates data integrity at every step

**Key Principles:**
- **AI does not remove QA.** It concentrates human time where it matters most: problem definition and quality acceptance.
- **Deterministic architecture over AI autonomy** — constraints and validation gates are non-negotiable for statutory work.
- **Live verification at scale** — reconciling against live API endpoints, not cached responses.

**Anti-Mock Safeguards Implemented:**

| Safeguard | Purpose | Implementation |
| :--- | :--- | :--- |
| **Live API Reconciliation** | Pre-flight QA | Connects to live query endpoints to reconcile counts against S3 tables |
| **Deep Payload Inspection** | Eliminate false positives | Inspects JSON bodies and Content-Types (ArcGIS servers return HTTP 200 on internal 404/499 errors or HTML pages) |
| **GeoLibre QA Inspector** | Single-source inspection | Dual-contrast symbology, 30% basemaps, in-browser spatial SQL |
| **Dry Run Airlock** | Pre-commit validation | Hashes, ETags, coordinate bounds asserted before any write operation |

**National Release Outcomes:**
- Statutory layers across NSW, QLD, VIC, WA, SA, and TAS
- Multi-hazard modeling: Landslide, Earthquake (NSHA), Cyclone (TCHA), Flooding
- Cloud-native GeoParquet with sub-second DuckDB-WASM spatial querying ($0.00 compute spend)

**Resources:**
- [QA Report](https://lnkd.in/ghEQURVW)
- [GeoLibre App](https://lnkd.in/g_UP-dSj)
- [Map Inspector](https://lnkd.in/gJWMRFCG)
- [Anti-Mock Playbook](https://lnkd.in/gP3pQGvb)
- [GitHub Repo (aura_siting_crafter)](https://lnkd.in/g4CqRR-h)

**Community Discussion Questions:**
- How are you preventing AI hallucinations in your spatial pipelines?
- Are you using dry-run airlocks before data commits?

---

## Related FunGIS-Branded Repositories

The following repositories carry the **"FunGIS" name brand** or are directly connected to FunGIS community events and initiatives:

| Repository | Purpose | Tech Stack | Status |
| :--- | :--- | :--- | :--- |
| **[FunGIS_SpatialOlympics26_MapInABox](https://github.com/GetBack2Basics/FunGIS_SpatialOlympics26_MapInABox)** | EXIF audit + interactive mapping for Spatial Olympics 2026 | Python, Leaflet, AlaSQL | Active for FunGIS events |
| **[SplatOlympics](https://github.com/GetBack2Basics/SplatOlympics)** | Gaussian blur–based spatial game for Olympics competition | TypeScript | Event experiment (08/2026) |
| **[FunGIS](https://github.com/GetBack2Basics/FunGIS)** | Main community collection (this repo) | Multi-language | Active archive |

---

## Community Events & Milestones

### FunGIS 35-Year History Highlights

| Year | Milestone |
| :--- | :--- |
| **1988** | FunGIS founded by local GIS innovators |
| **1990** | Incorporated as not-for-profit user group |
| **2006** | Conference theme: "Sandbags and Sandals" (post-Cyclone Larry response) |
| **2012** | Conference theme: "Combined LiDAR Technologies" |
| **2013** | 25th anniversary celebration |
| **2016** | Launch of FunGIS MapChats (informal face-to-face networking) |
| **2022** | Conference theme: "Mapping on the Move" |
| **2024** | Inaugural **FunGIS Geospatial Excellence Awards** established |
| **2026** | 35th anniversary conference: **"Past, Present, Future"** — celebrating advances and legacies of GIS in northern Australia |

### FunGIS Spatial Olympics (3+ Years Co-Leadership)

Annual competitive event demonstrating:
- Innovative spatial rendering and data engineering techniques
- Cloud-native and AI-assisted GIS workflows
- Real-world problem-solving with geospatial data
- Mentorship and knowledge transfer to emerging professionals

---

## Tech Stack & Expertise

FunGIS community work and projects draw on:

| Category | Tools & Technologies |
| :--- | :--- |
| **Languages** | Python (Pillow, geospatial libraries), TypeScript/JavaScript (React, Vite, interactive mapping), HTML/CSS, SQL |
| **Geospatial Tools** | QGIS, ArcGIS Pro/Enterprise, PostGIS, Leaflet, OpenLayers, GeoServer, MapLibre |
| **Cloud Spatial SQL** | Apache Sedona, Wherobots, Apache Iceberg, DuckDB-WASM, GeoParquet |
| **Data Formats** | GeoJSON, GeoParquet, EXIF/HEIF metadata extraction, WKT (Well-Known Text) |
| **Frontend & Visualization** | React, Vite, Tailwind CSS, Leaflet, AlaSQL (in-browser SQL), GeoLibre, interactive dashboards |
| **QA & Validation** | Live API reconciliation, dry-run airlocks, deep payload inspection, content-type validation |
| **DevOps & Infrastructure** | Docker, GitHub Actions, REST APIs, cloud storage (S3, Wherobots cloud) |
| **AI & Automation** | LLM-assisted development, metadata synthesis, query generation, deterministic AI architectures |

---

## Broader Portfolio Context

These repositories connect to and support the FunGIS ecosystem:

- **[aura_siting_crafter](https://github.com/GetBack2Basics/aura_siting_crafter)** — Cloud-native spatial ETL and multi-criteria decision analysis (MCDA) framework demonstrating modern GIS delivery patterns that FunGIS community explores. Features the Human-AI Triad architecture for preventing hallucinated data in statutory planning.
- **[QGIS_Remote_Sensing_Workflow](https://github.com/GetBack2Basics/QGIS_Remote_Sensing_Workflow)** — End-to-end QGIS-based remote sensing operations platform used and presented to FunGIS community.
- **[Spatial_Report_Crafter](https://github.com/GetBack2Basics/Spatial_Report_Crafter)** — Portable spatial reporting for client feedback workflows — a pattern frequently discussed in community best-practices forums.
- **[qgis-mcp](https://github.com/GetBack2Basics/qgis-mcp)** — QGIS automation via Model Context Protocol (MCP) for AI-assisted GIS workflows.
- **[SLWCS](https://github.com/GetBack2Basics/SLWCS)** — Historical conservation work repository showing long-term application of GIS to real-world impact.
- **[CheatSheets](https://github.com/GetBack2Basics/CheatSheets)** — Operational playbooks and setup guides for tools and stacks discussed in FunGIS workshops and conferences.

---

## Notes & Usage

- **This repository is a living archive** of FunGIS community work, events, and innovations. It continues to grow as new projects and initiatives emerge.
- **Projects are designed for reuse** — spatial workflows, pipelines, and code patterns are documented to be adapted by other communities and organizations.
- **Open-source contributions** — many FunGIS projects integrate or build upon open-source spatial ecosystems (QGIS, PostGIS, Apache Sedona). Community work reinforces broader open-source GIS adoption.
- **Safety-first in statutory GIS** — all projects involving national infrastructure or regulatory data include rigorous QA gates and validation layers. AI acceleration without QA safeguards is unacceptable for this work.
- **Using This Repository with AI Agents** — all projects include structured documentation, code comments, and metadata to support AI-assisted analysis and code generation workflows. See [Anti-Mock Playbook](#national-spatial-infrastructure--ai-safeguards) for guardrails.

---

## Connect

- **FunGIS Community:** Far North Queensland GIS Group Inc — [fungis.org](https://www.fungis.org/)
- **LinkedIn:** [George Chandeep Corea](https://www.linkedin.com/in/coreagc)
- **GitHub:** [GetBack2Basics](https://github.com/GetBack2Basics)
- **Location:** Newcastle, Australia 🇦🇺

---

**Last updated:** September 2026  
**FunGIS Legacy:** 35 years of spatial innovation and community building (1988–2026)
