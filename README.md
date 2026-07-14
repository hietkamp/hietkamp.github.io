# Essence Architecture Method — GitHub Pages Generator

Een statische website die de **Essence Architecture Method** beschrijft (Enterprise Architecture, Solution Architecture, Architectuursturing, Verandermanagement- en Project-levenscyclus), volledig gegenereerd uit RDF-bronbestanden.

**RDF is de enige bron van waarheid.** Namen, beschrijvingen, volgorde van activiteiten, in-/outputs, rollen en patronen komen allemaal uit `essence/`. `build.py` en de Jinja2-templates in `templates/` bevatten geen inhoud — alleen logica om die RDF-data op te halen en weer te geven.

Live site: gepubliceerd via GitHub Pages vanuit de `docs/`-map (zie [Pipeline](#pipeline-github-actions)).

## Architectuur

```
RDF (essence/)  --rdflib-->  Graph  --build.py-->  Jinja2 context  --templates/-->  HTML (docs/)
```

1. **`essence/`** — de RDF-bronbestanden (OWL-ontologie + Essence Kernel + de method zelf).
2. **`build.py`** — laadt alle `.rdf`-bestanden in één `rdflib.Graph`, haalt met helper­functies en SPARQL-achtige graph-queries de benodigde data op, bouwt per pagina een context-`dict` en rendert die met Jinja2.
3. **`templates/`** — Jinja2-sjablonen die uitsluitend de context-variabelen weergeven (geen hardcoded methode-inhoud).
4. **`docs/`** — het gegenereerde resultaat. Dit is de map die GitHub Pages serveert. **Niet handmatig bewerken** — wordt bij elke build overschreven.

### RDF-bronstructuur (`essence/`)

| Map/bestand | Inhoud | Aantal |
|---|---|---|
| `essence-language.owl` | Ontologie: klassen (`ess:Method`, `ess:Practice`, `ess:Activity`, `ess:WorkProduct`, `ess:Alpha`, `ess:Role`, `ess:Pattern`, ...) en properties | — |
| `essence-kernel.rdf` | De Essence Kernel (OMG ptc/25-05-01) | — |
| `method/essence-architecture-method.rdf` | De samengestelde methode (`ess:Method`), verwijst naar alle practices | 1 |
| `method/practices/*.rdf` | Practices | 5 |
| `method/activities/*.rdf` | Activiteiten binnen practices | 16 |
| `method/workproducts/*.rdf` | Werkproducten | 15 |
| `method/alphas/*.rdf` | Alphas (toestandsruimtes) | 5 |
| `method/roles/*.rdf` | Rollen | 4 |
| `method/patterns/*.rdf` | Patronen | 5 |

### Build-script (`build.py`)

Belangrijkste onderdelen, van boven naar beneden:

- **Namespaces & constanten** — `ESS`, `KERN`, `BASE`, `METHOD_URI`, paden (`ROOT`, `TEMPLATES_DIR`, `DOCS_DIR`).
- **`PRACTICE_CFG`** — de *enige* plek met visuele configuratie die niet uit RDF komt: kleuren, CSS-klassen, iconen (SVG path-data) per practice-slug. Dit is bewust gescheiden van inhoud: als je een nieuwe practice toevoegt in de RDF, moet je hier een entry toevoegen zodat de pagina weet welke kleur/icoon te gebruiken.
- **`ROLE_CFG`** — vergelijkbare visuele config per rol (kopkleur, competentie-labels).
- **Graph-helpers** — `load_graph()`, `get_name()`, `get_brief()`, `get_desc()` (NL-first met EN-fallback), `slug()`, `local_path()`.
- **Volgorde-logica** — `sorted_activities()` reconstrueert de activiteitenvolgorde per practice uit `ess:ActivityAssociation`-ketens (`end-before-start`), **niet** uit de volgorde van `ess:ownedElements`.
- **Action/Alpha-helpers** — `activity_inputs()`, `activity_outputs()`, `activity_patterns()`, `alpha_bar_html()`, `wp_proves()`, etc. Vertalen `ess:Action`, `ess:WorkProductManifest` en `ess:CompletionCriterion` naar leesbare lijsten/HTML voor de templates.
- **HTML-hulpfuncties** — `parse_wp_desc()`, `truncate_sentences()`, `fix_desc_paths()` verwerken de HTML die in `ess:description` (CDATA) zit.
- **Context-bouwers** (één per pagina-type) — `build_index_ctx()`, `build_practices_ctx()`, `build_practice_ctx()` / `build_phase_practice_ctx()`, `build_activity_ctx()`, `build_wp_ctx()`. Elke functie query't de graph en retourneert exact de dict-structuur die het bijbehorende template verwacht (zie context-schema's hieronder in CLAUDE.md).
- **`make_env()` / `write_page()`** — Jinja2-environment opzetten en een pagina naar `docs/` schrijven.
- **`main()`** — orkestreert alles: laadt de graph, genereert `index.html`, `practices.html`, per practice een practice-pagina, per activiteit een activiteitspagina, per werkproduct een werkproductpagina.

### Templates (`templates/`)

| Template | Rol |
|---|---|
| `_base.html.j2` | Basislay-out: nav, footer, `<head>`. Alle andere templates extend'en dit. |
| `_macros.html.j2`, `_card_activity.html.j2` | Herbruikbare Jinja2-macro's (o.a. activiteitskaarten). |
| `index.html.j2` | Methode-startpagina. |
| `practices.html.j2` | Overzicht van alle practices. |
| `wow.html.j2` | "Way of Working"-pagina — enige practice-detailtemplate, gebruikt voor alle 5 practices (Enterprise architectuur, Solution architectuur, Architectuursturing, Verandermanagement, Project). |
| `act.html.j2` | Individuele activiteitspagina. |
| `wp.html.j2` | Individuele werkproductpagina. |

## Pipeline (GitHub Actions)

![Pipeline C4 Level 2 – Containers](PipelineContainerView.png)

Zie [`c4-pipeline.dsl`](c4-pipeline.dsl) voor een Structurizr C4-containerdiagram van deze pijplijn (RDF → build-script → templates → gegenereerde site → CI/CD → GitHub Pages).

Gedefinieerd in [`.github/workflows/build.yml`](.github/workflows/build.yml):

1. Trigger: push naar `main`, of handmatig via `workflow_dispatch`.
2. Checkout → Python 3.12 opzetten (met pip-cache) → `pip install -r requirements.txt`.
3. `python build.py` genereert `docs/`.
4. `docs/` wordt geüpload als Pages-artifact en gedeployed naar GitHub Pages (`deploy`-job, environment `github-pages`).

Concurrency is beperkt tot één Pages-deployment tegelijk (`group: pages`).

**Belangrijk:** commit `docs/` niet handmatig aan met wijzigingen die je verwacht — de workflow bouwt de map bij elke push naar `main` opnieuw vanaf de RDF. Lokale wijzigingen in `docs/` die je niet via `build.py` genereert, worden bij de volgende push overschreven.

## Lokaal draaien

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # rdflib, jinja2
python build.py
```

Open daarna `docs/index.html` in de browser, of serveer de map lokaal:

```bash
python -m http.server -d docs 8000
```

## De site aanpassen

### Inhoud wijzigen (namen, beschrijvingen, volgorde, in-/outputs, rollen, patronen)

Pas **alleen de RDF-bestanden** in `essence/method/` aan — nooit `build.py` of de templates voor inhoudelijke wijzigingen. Bijvoorbeeld:

- Tekst van een activiteit/werkproduct/practice wijzigen → `ess:name` / `ess:briefDescription` / `ess:description` in het betreffende `.rdf`-bestand.
- Volgorde van activiteiten wijzigen → de `ess:ActivityAssociation`-ketens (`end-before-start`) in het practice- of activity-bestand.
- Welk werkproduct een activiteit leest/schrijft → de `ess:Action`-elementen (`ess:kind` = create/read/update) in het activity-bestand.
- Nieuw werkproduct/activiteit/practice toevoegen → nieuw `.rdf`-bestand in de juiste submap, gekoppeld via `ess:ownedElements` / `ess:owner`.

Draai daarna `python build.py` opnieuw; de RDF-wijziging verschijnt automatisch op de juiste pagina('s).

### Nieuwe practice toevoegen

1. Nieuw `.rdf`-bestand in `essence/method/practices/`, gekoppeld via `ess:ownedElements` vanuit `essence-architecture-method.rdf`.
2. Voeg een entry toe aan `PRACTICE_CFG` in `build.py` (slug, kleur, icoon) — dit is de enige plek waar niet-RDF (visuele) configuratie per practice hoort.
3. Voeg een link toe in de hoofdnavigatie (`templates/_base.html.j2`) als de practice een eigen instappunt (spoor) moet krijgen.
4. Voeg zo nodig de kleur toe aan `docs/style.css` (CSS custom property, zie `CLAUDE.md`).

### Layout/stijl wijzigen

Pas de templates in `templates/` of `docs/style.css` aan. Templates mogen **geen** methode-inhoud bevatten die uit RDF hoort te komen — alleen structuur en het weergeven van context-variabelen.

### Ontologie uitbreiden (nieuwe klasse/property)

Pas `essence/essence-language.owl` aan en voeg de bijbehorende ophaal-/mapping-logica toe aan `build.py` (een nieuwe helper- of context-bouwfunctie), niet aan de templates.

## Licentie

Dit project is gelicenseerd onder de [GNU General Public License v3.0](LICENSE) (GPLv3). Zie het [`LICENSE`](LICENSE)-bestand voor de volledige tekst.

## Gedetailleerde regels & context-schema's

Volledige beschrijving van de Essence-ontologie, alle context-dictionary-schema's per template, SPARQL-voorbeeldqueries en de harde regels voor dit project (RDF als enige bron, geen JSON/YAML tussenlagen, relatieve paden, etc.) staan in [`CLAUDE.md`](CLAUDE.md).
