# CLAUDE.md — Enterprise Architecture Way of Working — GitHub Pages Generator

## Project doel

Genereer een statische GitHub Pages website vanuit RDF-bestanden die een Essence-method beschrijven. De RDF is de enige bron van waarheid; templates en build-script zijn afleidingen daarvan. Niets in templates of context-dictionaries mag hardcoded inhoud bevatten die ook in de RDF staat.

## Technische stack

- **RDF-parsing**: `rdflib` (Python) — laad alle `.rdf`-bestanden in één `Graph`
- **Templating**: Jinja2 — templates staan in `templates/`
- **Build-script**: `build.py` in de projectroot (aan te maken)
- **Output**: `docs/` directory → GitHub Pages serveert vandaar
- **CI/CD**: GitHub Actions (`.github/workflows/build.yml`) — bouwt bij push naar `main`

## Essence ontologie — kernconcepten

Namespace prefix `ess:` = `https://www.hietkamp.nl/ontologies/essence-language#`  
Kernel namespace = `https://www.hietkamp.nl/ontologies/essence-kernel#`  
Method base URI = `https://hietkamp.nl/essence/`

### Klassen in de RDF (uit `essence/essence-language.owl`)

| Klasse | Beschrijving | RDF-bestanden |
|--------|-------------|---------------|
| `ess:Method` | De samengestelde methode | `method/essence-architecture-method.rdf` |
| `ess:Practice` | Een practice binnen de methode | `method/practices/*.rdf` |
| `ess:Activity` | Eén activiteit binnen een practice | `method/activities/*.rdf` |
| `ess:WorkProduct` | Een werkproduct | `method/workproducts/*.rdf` |
| `ess:Alpha` | Een alpha (toestandsruimte) | `method/alphas/*.rdf` |
| `ess:Role` | Een rol | `method/roles/*.rdf` |
| `ess:Pattern` | Een patroon | `method/patterns/*.rdf` |
| `ess:Action` | Create/read/update-actie op WP of Alpha | in activity-bestanden |
| `ess:ActivityAssociation` | Volgorde/relatie tussen activiteiten | in practice-bestanden |
| `ess:PatternAssociation` | Relatie van een practice of pattern naar andere elementen | in practice/pattern-bestanden |
| `ess:CompletionCriterion` | Voltooiingscriterium voor een activiteit | in activity-bestanden |
| `ess:WorkProductManifest` | Koppeling WP ↔ Alpha | in workproduct-bestanden |

### Veelgebruikte properties

| Property | Type | Gebruik |
|----------|------|---------|
| `ess:name` | `rdf:langString` (nl/en) | Nederlandse naam altijd beschikbaar |
| `ess:briefDescription` | `rdf:langString` (nl/en) | Korte beschrijving voor kaarten/chips |
| `ess:description` | `rdf:langString` met HTML CDATA | Uitgebreide beschrijving (render met `\| safe`) |
| `ess:isSuppressable` | `xsd:boolean` | Of het element onderdrukt mag worden |
| `ess:ownedElements` | object property | Relatie methode→practice, practice→activiteit/WP |
| `ess:owner` | object property | Terug-relatie activiteit/WP→practice |
| `ess:action` | object property | Activiteit → Action (CRUD op WP/Alpha) |
| `ess:approach` | object property | Activiteit → Approach |
| `ess:criterion` | object property | Activiteit/AS → CompletionCriterion |
| `ess:requiredCompetencyLevel` | object property | Activiteit → competentieniveau |
| `ess:associations` | object property | Practice/Pattern → PatternAssociation |
| `ess:elements` | object property | PatternAssociation → gerefereerde elementen |
| `ess:workProduct` | object property | Action/Manifest → WorkProduct |
| `ess:alpha` | object property | Action/Manifest/Criterion → Alpha |
| `ess:tags` | object property | Pattern → Tag; ook Alpha/Activity → `esk:CustomerAreaOfConcern` \| `SolutionAreaOfConcern` \| `EndeavorAreaOfConcern` |
| `ess:end1` / `ess:end2` | object property | ActivityAssociation endpoints |
| `ess:associationKind` | `xsd:string` | bv. `"end-before-start"`, `"part-of"` |

### Meertaligheid

Gebruik altijd Nederlands (`xml:lang="nl"`) als primaire taal. Engelse tekst (`xml:lang="en"`) als fallback of als ondertitel. In SPARQL: `FILTER(LANG(?name) = "nl")`.

## Bestandsstructuur

```
essencev3/
├── essence/
│   ├── essence-language.owl       # Ontologie (klassen + properties)
│   ├── essence-kernel.rdf         # Essence Kernel (OMG ptc/25-05-01)
│   ├── ptc-25-05-01.pdf           # Essence v2.0 specificatie
│   └── method/
│       ├── essence-architecture-method.rdf
│       ├── practices/             # 5 practices (enterprise-architecture, solution-architecture, ...)
│       ├── activities/            # ~17 activiteiten
│       ├── workproducts/          # ~13 werkproducten
│       ├── alphas/                # 5 alphas
│       ├── roles/                 # 4 rollen
│       └── patterns/              # 5 patronen
├── templates/                     # Jinja2-sjablonen
│   ├── _base.html.j2              # Basislay-out (nav, footer)
│   ├── _macros.html.j2            # Gedeelde macro's
│   ├── _card_activity.html.j2     # Macro: één activiteitskaart
│   ├── _collection_activities.html.j2  # Macro: collectie activiteitskaarten
│   ├── index.html.j2              # Methode-startpagina
│   ├── practices.html.j2          # Practices-overzicht
│   ├── wow.html.j2                # Way of Working — enige practice-detailtemplate (alle 5 practices, incl. architectural-governance)
│   ├── act.html.j2                # Individuele activiteitspagina
│   ├── wp.html.j2                 # Werkproductpagina
│   └── resources.html.j2          # Downloads/bronnen
├── docs/                          # Gegenereerde output (GitHub Pages)
├── build.py                       # Build-script (te maken)
├── .github/
│   └── workflows/
│       └── build.yml              # GitHub Actions (te maken)
└── CLAUDE.md
```

## Build-script (`build.py`) — architectuur

Het script laadt alle RDF in één graph en rendert per pagina een Jinja2-template.

```python
from rdflib import Graph, Namespace, RDF, RDFS, Literal
from rdflib.namespace import XSD
from jinja2 import Environment, FileSystemLoader
import pathlib, re

ESS  = Namespace("https://www.hietkamp.nl/ontologies/essence-language#")
KERN = Namespace("https://www.hietkamp.nl/ontologies/essence-kernel#")
BASE = "https://hietkamp.nl/essence/"

# Laad alle RDF-bestanden
g = Graph()
for rdf_file in pathlib.Path("essence").rglob("*.rdf"):
    g.parse(rdf_file, format="xml")
```

### Hulpfuncties

```python
def name_nl(subject) -> str:
    """Haal Nederlandse naam op; fallback naar Engels."""
    for obj in g.objects(subject, ESS.name):
        if obj.language == "nl":
            return str(obj)
    for obj in g.objects(subject, ESS.name):
        return str(obj)
    return ""

def brief_nl(subject) -> str:
    """Haal Nederlandse briefDescription op."""
    for obj in g.objects(subject, ESS.briefDescription):
        if obj.language == "nl":
            return str(obj)
    return ""

def desc_nl(subject) -> str:
    """Haal Nederlandse description op (kan HTML bevatten)."""
    for obj in g.objects(subject, ESS.description):
        if obj.language == "nl":
            return str(obj)
    return ""

def local_id(uri: str) -> str:
    """Extraheer het lokale pad na de BASE-URI, bv. 'activity/enterprise-understand'."""
    return str(uri).replace(BASE, "")

def slug(uri: str) -> str:
    """Laatste segment van een URI als slug, bv. 'enterprise-understand'."""
    return str(uri).rstrip("/").split("/")[-1]

def output_path(kind: str, id_slug: str) -> str:
    """Bouw het uitvoerpad in docs/, bv. 'docs/act/enterprise-understand.html'."""
    mapping = {
        "activity": "act",
        "workproduct": "wp",
        "practice": "practice",
        "pattern": "pattern",
    }
    prefix = mapping.get(kind, kind)
    return f"docs/{prefix}/{id_slug}.html"
```

### Gegenereerde pagina's en templates

| Outputbestand | Template | RDF-bron |
|---------------|----------|----------|
| `docs/index.html` | `index.html.j2` | `ess:Method` |
| `docs/practices.html` | `practices.html.j2` | alle `ess:Practice` |
| `docs/practice/{id}.html` | `wow.html.j2` (alle 5 practices, geen aparte template per practice) | `ess:Practice` + ownedElements |
| `docs/act/{id}.html` | `act.html.j2` | `ess:Activity` + actions + criteria |
| `docs/wp/{id}.html` | `wp.html.j2` | `ess:WorkProduct` + manifests |

## Template-context variabelen

### `_base.html.j2` (altijd aanwezig)

```python
{
    "title": str,           # <title>-tag
    "description": str,     # meta description
    "root": str,            # relatief pad naar root, bv. "../" of ""
    "css_path": str,        # pad naar style.css
    "data_prac": str,       # CSS-klasse voor practice-kleur, altijd "neutral"
}
```

### `practices.html.j2`

```python
{
    "hero_data": { "kicker": str, "h1_pre": str, "h1_em": str, "lede": str },
    "practices": [
        {
            "id": str,          # rdf:about slug, bv. "enterprise-architecture"
            "href": str,        # bv. "practice/enterprise-architecture.html"
            "title": str,       # ess:name (nl)
            "desc": str,        # ess:briefDescription (nl)
            "color": str,       # CSS-variabelenaam zonder --, altijd "neutral" (practices zijn nooit domein-gekleurd)
            "tags": [str],      # ownedElements-slugs of tags
            "icon_path": str,   # SVG path-data
        }
    ]
}
```

### `wow.html.j2` (practice-pagina)

```python
{
    "hero_data": { ... },
    "crumbs": [{"href": str, "label": str}],
    "spoor": "enterprise" | "solution",
    "inherited_context": None | {"title": str, "body": str},
    "activities": {
        "title": str,
        "intro": str,
        "domains": [
            {
                "name": str,
                "alphas": str,      # kommagescheiden alpha-namen
                "css": str,
                "gradient": str,
                "num_color": str,
                "connector_after": str,
                "items": [
                    {
                        "type": "space" | "space_gap" | "activity",
                        # bij type == "activity": volledig act-dict (zie _card_activity.html.j2)
                        "href": str,
                        "num": str,
                        "title": str,
                        "desc": str,
                        "phase": "analyse" | "dev",
                        "chips": {"space": str, "alpha": str},
                        "inputs": [str],    # WP-namen
                        "outputs": [str],   # WP-namen
                        "patterns": [str],  # patroon-namen
                        "alpha_bar": str,   # optioneel HTML
                    }
                ]
            }
        ]
    },
    "diff_grid": None | { ... },
    "roles": {
        "intro": str,
        "cards": [
            { "id": str, "name": str, "desc": str, "head_color": str, "competencies": [str], "owns": str }
        ],  # 1 kaart voor de meeste practices, 2 voor architectural-governance — wow.html.j2 rendert altijd als grid
    },
    "closing_panel": {"title": str, "body": [str]},
}
```

### `act.html.j2` (activiteitspagina)

```python
{
    "title": str,
    "act_name": str,        # ess:name (nl)
    "title_en": str,        # ess:name (en)
    "lede": str,            # ess:briefDescription (nl)
    "act_num": str,         # bv. "Activiteit 01 / 06"
    "breadcrumb": {
        "parents": [{"href": str, "label": str}],
        "current": str,
    },
    "chips": {"space": str},
    "extra_chips": [],
    "alpha_bar": str,       # HTML voor alpha-voortgangsbalk
    "desc_html": str,       # volledige ess:description HTML, gerenderd via rdf_prose() (macro uit _macros.html.j2), net als op wow.html.j2
    "steps": [{"title": str, "desc": str}],
    "cots_box": str,        # optioneel HTML (COTS-context)
    "work_products": [
        {
            "title": str,
            "desc": str,
            "proves": str,  # alpha-state-progressie tekst
            "href": str | None,
            "practice": str,  # naam van de practice die het werkproduct bezit (ess:owner)
        }
    ],
    "roles": None | {
        "intro": str,
        "cards": [{ "role": str, "scope": str, "desc": str,
                    "makes": str, "competencies": [str], "lc_css": str, "id": str }]
    },
    "nav": {
        "prev": None | {"href": str, "label": str},
        "next": None | {"href": str, "label": str},
        "overview": str,
    },
}
```

### `wp.html.j2` (werkproductpagina)

```python
{
    "title": str,
    "kicker": str,
    "h1_pre": str,
    "h1_em": str,
    "lede": str,            # ess:briefDescription (nl)
    "meta_pills": [str],
    "download": {"type": "xlsx"|"docx", "filename": str, "desc": str},
    "semantic_role": str,
    "purpose": str,
    "answers_question": str,
    "object_boundary": str,
    "primary_audience": str,
    "essence_evidence": str,
    "archimate_layer": str,
    "c4_level": str,
    "update_cadence": str,
    "information_elements": [{"element": str, "meaning": str, "required": str}],
    "quality_criteria": [{"criterion": str, "check": str}],
    "trace_links": [{"link": str}],
    "sections": [
        {
            "id": str,
            "h2": str,
            "body_html": str,       # HTML (gebruik | safe in template)
            "section_kind": str,    # bv. "content"
        }
    ],
    "breadcrumb": {"parent_href": str, "parent_label": str, "current": str},
}
```

## RDF → context-mapping patterns

### Activiteit → work product namen (inputs/outputs)

```python
# inputs: alle WP's die de activiteit leest
inputs = []
for action in g.objects(activity_uri, ESS.action):
    action_kind = str(next(g.objects(action, ESS.kind), ""))
    if "read" in action_kind:
        wp = next(g.objects(action, ESS.workProduct), None)
        if wp:
            inputs.append(name_nl(wp))

# outputs: alle WP's die de activiteit aanmaakt of bijwerkt
outputs = []
for action in g.objects(activity_uri, ESS.action):
    action_kind = str(next(g.objects(action, ESS.kind), ""))
    if "create" in action_kind or "update" in action_kind:
        wp = next(g.objects(action, ESS.workProduct), None)
        if wp:
            outputs.append(name_nl(wp))
```

### Activiteitsvolgorde per practice

```python
# end-before-start-ketens ophalen voor een practice
q = """
PREFIX ess: <https://www.hietkamp.nl/ontologies/essence-language#>
SELECT ?a1 ?a2 WHERE {
    ?assoc a ess:ActivityAssociation ;
           ess:end1 ?a1 ;
           ess:end2 ?a2 ;
           ess:associationKind "end-before-start" .
    ?a1 ess:owner <%s> .
}
""" % practice_uri
```

### HTML uit ess:description parsen

```python
import re

def description_sections(desc_html: str) -> list[dict]:
    """Splits CDATA-description in secties op basis van <h3>-koppen."""
    sections = []
    # naïeve split; rdflib geeft de CDATA-inhoud als str
    parts = re.split(r'(?=<h3)', desc_html, flags=re.IGNORECASE)
    for part in parts:
        if part.strip():
            sections.append({"h2": "", "body_html": part, "section_kind": "content"})
    return sections
```

## GitHub Actions workflow (`.github/workflows/build.yml`)

```yaml
name: Build GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install rdflib jinja2

      - name: Build site
        run: python build.py

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

## CSS-variabelen en practice-kleuren

**Een Practice bevindt zich nooit in een domein/area of concern** — alleen `ess:Alpha` en `ess:Activity` doen dat (zie hieronder). Practices krijgen daarom allemaal dezelfde neutrale kleur. Definieer deze in `docs/style.css`:

```css
:root {
  --neutral: #0f172a;   /* neutrale practice-kleur, voor alle 5 practices */
  --prac:    var(--neutral); /* overridden by data-prac selector below */
}
[data-prac="neutral"] { --prac: var(--neutral); }
```

Alle practice-headers (`enterprise-architecture`, `solution-architecture`, `architectural-governance`, `portfolio-lifecycle`, `project-lifecycle`) renderen met `bg-[#0f172a]` en witte tekst — geen enkele practice krijgt een eigen kleur. De kleur die je per activiteit ziet komt uitsluitend van de area-of-concern-tag op die activiteit (zie hieronder).

## Essence Kernel areas of concern (Customer / Solution / Endeavor)

De Essence Kernel onderscheidt drie areas of concern. Dit is **RDF-content, geen build.py-config**: elke `ess:Alpha` en `ess:Activity` (kernel én method-specifiek) draagt zijn area of concern rechtstreeks via `ess:tags`:

```xml
<ess:tags rdf:resource="https://www.hietkamp.nl/ontologies/essence-kernel#SolutionAreaOfConcern"/>
```

De drie tag-individuals (`esk:CustomerAreaOfConcern`, `esk:SolutionAreaOfConcern`, `esk:EndeavorAreaOfConcern`) staan gedefinieerd in `essence/essence-kernel.rdf` en worden daar al gebruikt op alle Kernel-Alphas en -ActivitySpaces. Dezelfde tags staan nu ook op de 5 method-Alphas (`essence/method/alphas/*.rdf`) en de 17 method-Activities (`essence/method/activities/*.rdf`).

`build.py` leest deze tag puur via rdflib (`activity_domain_color()`, build.py) — er is **geen** hardcoded Alpha→domein-mapping meer. `AREA_OF_CONCERN_DOMAIN` in build.py is uitsluitend een technische vertaling van de RDF Tag-URI naar een interne kleursleutel, geen inhoudelijke aanname.

Alle drie de kleuren zijn een solide `-700`-gewicht vulling met witte tekst — dezelfde stijl als de bestaande fase-badges (`bg-blue-700` voor "analyse", `bg-slate-700` voor "dev"), zodat het num-badge overal op de site één consistente taal spreekt. De tinten zijn zo gekozen dat ze niet botsen met `blue-700`/`indigo-700`/`emerald-700`, die al gebruikt worden door de chips.space/comp/alpha-chips op dezelfde kaart:

| Area of concern | Kleur | Hex | Toepassing |
|--------|-----|-----|------------|
| Solution | `bg-amber-700` | `#B45309` | Activiteiten/alphas getagd `SolutionAreaOfConcern` (architectuur, architectuurbeslissingen, architectuurbepalende eisen, requirements) |
| Customer | `bg-teal-700` | `#0F766E` | Activiteiten/alphas getagd `CustomerAreaOfConcern` (stakeholders, opportunity, scope/mandaat) |
| Endeavor | `bg-violet-700` | `#6D28D9` | Activiteiten/alphas getagd `EndeavorAreaOfConcern` (governance, paved road, way of working, team) |

Tekstkleur is altijd `text-white` (niet `text-slate-800`), passend bij de verzadigde `-700`-achtergrond.

Een Activity zonder `ess:tags` toont geen domeinkleur en valt terug op de neutrale practice-kleur.

## Regels en beslissingen

1. **RDF is de enige bron**. Geen inhoud hardcoden in `build.py` of templates die ook in RDF staat. Gebruik SPARQL of rdflib-queries om alle tekst, namen en relaties op te halen.

   **Concreet verboden patroon**: een Python-lijst of -dict met copy-tekst rechtstreeks in een context-builder-functie, bijvoorbeeld:
   ```python
   steps = [
       {"num": "01", "title": "Begrijpen", "desc": "Identificeer en kwantificeer de sturende eisen…"},
       ...
   ]
   ```
   Dit soort blokken duplicerene (en raken vrijwel gegarandeerd) namen/teksten die al in de RDF staan — zo verwees een dergelijk blok in `build_index_ctx()` nog naar activiteitnamen die allang hernoemd waren in de RDF. Titels, beschrijvingen, rollen, fases, gates en alpha's moeten altijd via `get_name()`/`get_brief()`/`get_desc()` of een SPARQL-query worden opgehaald, ook voor kaarten/hero-secties op `index.html`. Puur presentationele config (kleuren, CSS-klassen, icon-paths, welke template) mag wel in `build.py` staan — dat is geen "inhoud".

2. **Nederlandse primaire taal**. Filter altijd op `xml:lang="nl"` voor namen en beschrijvingen. Engelse tekst als ondertitel of fallback.

3. **Relatieve paden in `docs/`**. Alle gegenereerde HTML gebruikt relatieve hrefs (`../index.html`, niet absolute URLs). De `root`-variabele in de base template regelt de diepte.

4. **`ess:description` bevat HTML**. De CDATA-inhoud is HTML met `<p>`, `<strong>`, `<h3>`, `<table>`, `<ul>`. Render altijd met `| safe` in Jinja2.

5. **Templates aanpassen is toegestaan en vereist**. De huidige templates zijn startpunten; ze werken nog niet op basis van RDF-context. Pas ze aan zodat ze de context-variabelen correct weergeven.

6. **Geen statische JSON/YAML databestanden**. Gebruik geen tussenliggende YAML- of JSON-bestanden als databron. Alles gaat via rdflib direct naar Jinja2.

7. **`docs/` is gegenereerd**. Commit de `docs/`-directory niet handmatig; GitHub Actions bouwt hem opnieuw bij elke push.

8. **Activiteitsolgorde via ActivityAssociation**. De volgorde van activiteiten binnen een practice wordt bepaald door de `end-before-start`-ketens in de RDF, niet door de volgorde van `ess:ownedElements`.

9. **WorkProductManifest koppelt WP aan Alpha**. Gebruik `ess:WorkProductManifest` om te tonen welke alpha's een werkproduct bewijst.

10. **Area of concern (Customer/Solution/Endeavor) hoort bij Alpha en Activity, nooit bij Practice**. Een Practice krijgt altijd de neutrale practice-kleur (`#0f172a`); domeinkleur komt uitsluitend uit de `ess:tags`-property op de Alpha of Activity zelf. Voeg bij nieuwe Alphas/Activities altijd een `ess:tags`-verwijzing naar één van de drie `esk:*AreaOfConcern`-individuals toe — laat dit nooit afleiden of gokken in `build.py`.

## Veel voorkomende SPARQL-queries

### Alle practices van de methode
```sparql
PREFIX ess: <https://www.hietkamp.nl/ontologies/essence-language#>
SELECT ?practice ?name WHERE {
    <https://hietkamp.nl/essence/method/essence-architecture-method> ess:ownedElements ?practice .
    ?practice a ess:Practice ;
              ess:name ?name .
    FILTER(LANG(?name) = "nl")
}
```

### Alle activiteiten van een practice
```sparql
PREFIX ess: <https://www.hietkamp.nl/ontologies/essence-language#>
SELECT ?activity ?name ?brief WHERE {
    ?activity a ess:Activity ;
              ess:owner <PRACTICE_URI> ;
              ess:name ?name ;
              ess:briefDescription ?brief .
    FILTER(LANG(?name) = "nl")
    FILTER(LANG(?brief) = "nl")
}
```

### Work products aangemaakt door een activiteit
```sparql
PREFIX ess: <https://www.hietkamp.nl/ontologies/essence-language#>
SELECT ?wp ?wpname WHERE {
    <ACTIVITY_URI> ess:action ?action .
    ?action ess:kind <https://www.hietkamp.nl/ontologies/essence-language#create> ;
            ess:workProduct ?wp .
    ?wp ess:name ?wpname .
    FILTER(LANG(?wpname) = "nl")
}
```

### Patronen gebruikt door een activiteit
```sparql
PREFIX ess: <https://www.hietkamp.nl/ontologies/essence-language#>
SELECT ?pattern ?pname WHERE {
    ?assoc a ess:PatternAssociation ;
           ess:elements <ACTIVITY_URI> .
    ?pattern ess:associations ?assoc ;
             a ess:Pattern ;
             ess:name ?pname .
    FILTER(LANG(?pname) = "nl")
}
```

### Area of concern van een Alpha of Activity
```sparql
PREFIX ess: <https://www.hietkamp.nl/ontologies/essence-language#>
SELECT ?tag WHERE {
    <ALPHA_OF_ACTIVITY_URI> ess:tags ?tag .
    FILTER(STRSTARTS(STR(?tag), "https://www.hietkamp.nl/ontologies/essence-kernel#") &&
           STRENDS(STR(?tag), "AreaOfConcern"))
}
```
