#!/usr/bin/env python3
"""
build.py — Generate GitHub Pages from Essence method RDF.

Usage:  python build.py
Output: docs/
"""

import pathlib
import re
import shutil

from rdflib import Graph, Namespace, URIRef, RDF
from jinja2 import Environment, FileSystemLoader

# ---------------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------------
ESS  = Namespace("https://www.hietkamp.nl/ontologies/essence-language#")
KERN = Namespace("https://www.hietkamp.nl/ontologies/essence-kernel#")
BASE = "https://hietkamp.nl/essence/"
METHOD_URI = URIRef(BASE + "method/essence-architecture-method")

ROOT = pathlib.Path(__file__).parent
TEMPLATES_DIR = ROOT / "templates"
DOCS_DIR = ROOT / "docs"

# ---------------------------------------------------------------------------
# Visual config — things not in RDF (colours, icons, UI text)
# ---------------------------------------------------------------------------

PRACTICE_CFG = {
    "enterprise-architecture": {
        "color":       "mva",
        "css_var":     "#27406b",
        "spoor":       "enterprise",
        "template":    "wow.html.j2",
        "num_color":   "bg-[#27406b]",
        "css":         "bg-[#27406b]",
        "gradient":    "from-[#27406b] to-[#1a2f5a]",
        "domain_name": "Enterprise Architectuur",
        "level_label": "Enterprise",
        "icon_path":   "<rect x='2' y='2' width='5' height='5'/><rect x='9' y='2' width='5' height='5'/>"
                       "<rect x='2' y='9' width='5' height='5'/><rect x='9' y='9' width='5' height='5'/>",
    },
    "solution-architecture": {
        "color":       "sol",
        "css_var":     "#0f6e63",
        "spoor":       "solution",
        "template":    "wow.html.j2",
        "num_color":   "bg-[#0f6e63]",
        "css":         "bg-[#0f6e63]",
        "gradient":    "from-[#0f6e63] to-[#0a4d45]",
        "domain_name": "Solution Architectuur",
        "level_label": "Solution",
        "domain_colored": True,
        "icon_path":   "<path d='M8 2L2 14h12L8 2zm0 4l3 6H5l3-6z'/>",
    },
    "architectural-governance": {
        "color":        "mvg",
        "css_var":      "#4f46e5",
        "spoor":        "governance",
        "template":     "governance.html.j2",
        "num_color":    "bg-indigo-200",
        "css":          "bg-indigo-100",
        "gradient":     "from-indigo-100 to-indigo-200",
        "header_light": True,
        "domain_name":  "Architectuursturing",
        "level_label":  "Governance",
        "icon_path":    "<path d='M8 1L1 5v4c0 3.55 2.96 6.88 7 7.93C12.04 15.88 15 12.55 15 9V5L8 1z'/>",
    },
    "portfolio-lifecycle": {
        "color":       "port",
        "css_var":     "#b45309",
        "spoor":       "enterprise",
        "template":    "wow.html.j2",
        "num_color":   "bg-amber-700",
        "css":         "bg-amber-700",
        "gradient":    "from-amber-700 to-amber-800",
        "domain_name": "Portfolio Levenscyclus",
        "level_label": "Portfolio",
        "icon_path":   "<rect x='2' y='2' width='4' height='4'/><rect x='8' y='2' width='4' height='4'/>"
                       "<rect x='2' y='8' width='4' height='4'/><rect x='8' y='8' width='4' height='4'/>",
    },
    "project-lifecycle": {
        "color":        "wf",
        "css_var":      "#EAB308",
        "spoor":        "solution",
        "template":     "wow.html.j2",
        "num_color":    "bg-yellow-500",
        "css":          "bg-yellow-500",
        "gradient":     "from-yellow-500 to-yellow-700",
        "header_light": True,
        "domain_name":  "Project levenscyclus",
        "level_label":  "Solution",
        "nav_title":    "Project levenscyclus",
        "icon_path":    "<path d='M2 2h12v2H2V2zm1 3h10v2H3V5zm1 3h8v2H4V8zm1 3h6v2H5v-2zm1 3h4v2H6v-2z'/>",
        "show_comp":    False,
    },
}

ROLE_CFG = {
    "enterprise-architect": {
        "head_color":    "bg-[#27406b]",
        "competencies":  ["Analyse", "Architectuur", "Leadership"],
    },
    "architecture-owner": {
        "head_color":    "bg-[#0f6e63]",
        "competencies":  ["Analyse", "Stakeholder Rep.", "Leadership"],
    },
    "architecture-sponsor": {
        "head_color":    "bg-indigo-200",
        "competencies":  ["Leadership", "Management"],
    },
    "governance-forum": {
        "head_color":    "bg-indigo-200",
        "competencies":  ["Analyse", "Leadership", "Management"],
    },
}

# Phase heuristic: first two activities in chain → analyse, rest → dev
ANALYSE_KERNEL_SPACES = {
    str(KERN.UnderstandStakeholderNeeds),
    str(KERN.UnderstandtheRequirements),
}

# Essence Kernel domain colours (OMG ptc/25-05-01): Solution, Customer, Endeavour.
# Maps the local name of an alpha (kernel or method-specific) to the kernel
# domain it belongs to, so activity cards can be tinted per touched alpha.
ALPHA_DOMAIN_CFG = {
    # Solution domain — System / Software System
    "architecture":           "solution",
    "architecture-decisions": "solution",
    "System":                 "solution",
    # Customer domain — Opportunity / Stakeholders / Requirements
    "architectural-drivers":  "customer",
    "Requirements":           "customer",
    "Opportunity":            "customer",
    "Stakeholders":           "customer",
    # Endeavour domain — Work / Way of Working / Team
    "paved-road":             "endeavour",
    "governance":             "endeavour",
    "Work":                   "endeavour",
    "WayofWorking":           "endeavour",
    "Team":                   "endeavour",
}

DOMAIN_COLOR_CFG = {
    "solution": {
        "num_color":      "bg-[#FFFF7F]",
        "num_text_color": "text-slate-800",
    },
    "customer": {
        "num_color":      "bg-[#D4FECE]",
        "num_text_color": "text-slate-800",
    },
    "endeavour": {
        "num_color":      "bg-indigo-100",
        "num_text_color": "text-slate-800",
    },
}

# ---------------------------------------------------------------------------
# Graph loading
# ---------------------------------------------------------------------------

def load_graph() -> Graph:
    g = Graph()
    for rdf_file in sorted((ROOT / "essence").rglob("*.rdf")):
        g.parse(str(rdf_file), format="xml")
    return g

# ---------------------------------------------------------------------------
# Helper: text extraction
# ---------------------------------------------------------------------------

def get_name(g: Graph, uri, lang: str = "nl") -> str:
    for obj in g.objects(uri, ESS.name):
        if hasattr(obj, "language") and obj.language == lang:
            return str(obj)
    for obj in g.objects(uri, ESS.name):
        return str(obj)
    return ""

def get_brief(g: Graph, uri, lang: str = "nl") -> str:
    for obj in g.objects(uri, ESS.briefDescription):
        if hasattr(obj, "language") and obj.language == lang:
            return str(obj)
    for obj in g.objects(uri, ESS.briefDescription):
        return str(obj)
    return ""

def get_desc(g: Graph, uri, lang: str = "nl") -> str:
    for obj in g.objects(uri, ESS.description):
        if hasattr(obj, "language") and obj.language == lang:
            return str(obj)
    for obj in g.objects(uri, ESS.description):
        return str(obj)
    return ""

def slug(uri) -> str:
    return str(uri).rstrip("/").split("/")[-1]

def local_path(uri) -> str:
    return str(uri).replace(BASE, "")

# ---------------------------------------------------------------------------
# Helper: activity ordering
# ---------------------------------------------------------------------------

def sorted_activities(g: Graph, practice_uri) -> list:
    """Return Activity URIs in end-before-start order for a practice."""
    acts = set()
    for el in g.objects(practice_uri, ESS.ownedElements):
        if (el, RDF.type, ESS.Activity) in g:
            acts.add(el)

    next_map: dict = {}
    prev_map: dict = {}
    for assoc in g.subjects(RDF.type, ESS.ActivityAssociation):
        kind_vals = list(g.objects(assoc, ESS.associationKind))
        if not kind_vals:
            continue
        if str(kind_vals[0]) != "end-before-start":
            continue
        a1 = next(g.objects(assoc, ESS.end1), None)
        a2 = next(g.objects(assoc, ESS.end2), None)
        if a1 in acts and a2 in acts:
            next_map[a1] = a2
            prev_map[a2] = a1

    starts = [a for a in acts if a not in prev_map]
    result: list = []
    for start in starts:
        cur = start
        while cur:
            result.append(cur)
            cur = next_map.get(cur)

    for a in acts:
        if a not in result:
            result.append(a)
    return result

# ---------------------------------------------------------------------------
# Helper: activity inputs / outputs / patterns
# ---------------------------------------------------------------------------

def _action_kind(g: Graph, action_uri) -> str:
    """Return the local name of ess:kind, e.g. 'create', 'read', 'update'."""
    kind_uri = next(g.objects(action_uri, ESS.kind), None)
    if kind_uri is None:
        return ""
    return str(kind_uri).split("#")[-1].lower()

def activity_inputs(g: Graph, activity_uri) -> list[str]:
    names = []
    for action in g.objects(activity_uri, ESS.action):
        if _action_kind(g, action) == "read":
            wp = next(g.objects(action, ESS.workProduct), None)
            if wp:
                n = get_name(g, wp)
                if n and n not in names:
                    names.append(n)
    return names

def activity_outputs(g: Graph, activity_uri, lod_filter: dict = None) -> list[dict]:
    """Return [{"name": str, "lods": [str]}] for each WP created/updated by the activity.

    lod_filter: {wp_uri: [lod_name, ...]} — when provided, only show the listed LOD names
    for that WP; WPs not in the filter get no LODs shown.
    """
    results = []
    seen: set = set()
    for action in g.objects(activity_uri, ESS.action):
        if _action_kind(g, action) in ("create", "update"):
            wp = next(g.objects(action, ESS.workProduct), None)
            if wp and wp not in seen:
                seen.add(wp)
                n = get_name(g, wp)
                if n:
                    if lod_filter is not None:
                        lods = sorted(lod_filter.get(wp, []))
                    else:
                        lods = sorted(
                            [get_name(g, lod) for lod in g.objects(wp, ESS.levelOfDetail)
                             if get_name(g, lod)]
                        )
                    results.append({"name": n, "lods": lods})
    return results

def activity_output_wps(g: Graph, activity_uri) -> list:
    """Return WorkProduct URIs created/updated by the activity."""
    wps = []
    seen = set()
    for action in g.objects(activity_uri, ESS.action):
        if _action_kind(g, action) in ("create", "update"):
            wp = next(g.objects(action, ESS.workProduct), None)
            if wp and wp not in seen:
                wps.append(wp)
                seen.add(wp)
    return wps

def activity_patterns(g: Graph, activity_uri) -> list[str]:
    """Return names of patterns that use this activity."""
    names = []
    for assoc in g.subjects(ESS.elements, activity_uri):
        if (assoc, RDF.type, ESS.PatternAssociation) not in g:
            continue
        assoc_name = get_name(g, assoc, lang="en")
        if assoc_name.lower() != "uses":
            continue
        pattern = next(g.subjects(ESS.associations, assoc), None)
        if pattern and (pattern, RDF.type, ESS.Pattern) in g:
            n = get_name(g, pattern)
            if n and n not in names:
                names.append(n)
    return names

# ---------------------------------------------------------------------------
# Helper: alpha bar (completion criteria → alpha states)
# ---------------------------------------------------------------------------

def alpha_bar_html(g: Graph, activity_uri) -> str:
    bars = []
    for crit in g.objects(activity_uri, ESS.criterion):
        if (crit, RDF.type, ESS.CompletionCriterion) not in g:
            continue
        state = next(g.objects(crit, ESS.state), None)
        if state is None:
            continue
        alpha = next(g.subjects(ESS.states, state), None)
        if alpha is None:
            continue
        alpha_name = get_name(g, alpha)
        state_name = get_name(g, state)
        if alpha_name and state_name:
            bars.append(f"{alpha_name} → <b>{state_name}</b>")
    return " · ".join(bars)

# ---------------------------------------------------------------------------
# Helper: kernel activity space chip
# ---------------------------------------------------------------------------

def activity_space_chip(g: Graph, activity_uri) -> str:
    """Return the kernel activity space name for this activity (via part-of)."""
    for assoc in g.subjects(RDF.type, ESS.ActivityAssociation):
        kind_vals = list(g.objects(assoc, ESS.associationKind))
        if not kind_vals or str(kind_vals[0]) != "part-of":
            continue
        a1 = next(g.objects(assoc, ESS.end1), None)
        if a1 != activity_uri:
            continue
        a2 = next(g.objects(assoc, ESS.end2), None)
        if a2 is None:
            continue
        name = get_name(g, a2)
        if name:
            return name
    return ""

def activity_phase(g: Graph, activity_uri) -> str:
    """Return 'analyse' if mapped to an understanding kernel space, else 'dev'."""
    for assoc in g.subjects(RDF.type, ESS.ActivityAssociation):
        kind_vals = list(g.objects(assoc, ESS.associationKind))
        if not kind_vals or str(kind_vals[0]) != "part-of":
            continue
        a1 = next(g.objects(assoc, ESS.end1), None)
        if a1 != activity_uri:
            continue
        a2 = next(g.objects(assoc, ESS.end2), None)
        if a2 and str(a2) in ANALYSE_KERNEL_SPACES:
            return "analyse"
    return "dev"

# ---------------------------------------------------------------------------
# Helper: primary alpha for an activity
# ---------------------------------------------------------------------------

def primary_alpha_name(g: Graph, activity_uri) -> str:
    """Return the name of the primary alpha touched by this activity, preferring
    method-specific alphas over kernel alphas, falling back to kernel if none."""
    alpha = primary_alpha_uri(g, activity_uri)
    return get_name(g, alpha) if alpha is not None else ""

def primary_alpha_uri(g: Graph, activity_uri):
    """Return the URI of the primary alpha touched by this activity, preferring
    method-specific (non-kernel) alphas over kernel alphas."""
    fallback = None
    for action in g.objects(activity_uri, ESS.action):
        alpha = next(g.objects(action, ESS.alpha), None)
        if alpha is None:
            continue
        if str(alpha).startswith(BASE):
            return alpha
        if fallback is None:
            fallback = alpha
    return fallback

def _alpha_key(uri) -> str:
    """Local name of an alpha URI, kernel (fragment-based) or method (path-based)."""
    s = str(uri)
    return s.split("#")[-1] if "#" in s else s.rstrip("/").split("/")[-1]

def activity_domain_color(g: Graph, activity_uri) -> dict:
    """Return the Essence Kernel domain colour (Solution/Customer/Endeavour) for
    the alpha this activity primarily works on, or {} if no mapping applies."""
    alpha = primary_alpha_uri(g, activity_uri)
    if alpha is None:
        return {}
    domain = ALPHA_DOMAIN_CFG.get(_alpha_key(alpha))
    if not domain:
        return {}
    return {"domain": domain, **DOMAIN_COLOR_CFG[domain]}

# ---------------------------------------------------------------------------
# Helper: workproduct → owning practice role
# ---------------------------------------------------------------------------

def wp_proves(g: Graph, wp_uri) -> str:
    """Return a short string like 'Architectuurbepalende Eisen → Gekwantificeerd'."""
    manifests = list(g.subjects(ESS.workProduct, wp_uri))
    parts = []
    for manifest in manifests:
        alpha = next(g.objects(manifest, ESS.alpha), None)
        if alpha and str(alpha).startswith(BASE):
            parts.append(get_name(g, alpha))
    return " · ".join(p for p in parts if p)

# ---------------------------------------------------------------------------
# Helper: parse structured fields from workproduct description HTML
# ---------------------------------------------------------------------------

def parse_wp_desc(html: str) -> list:
    """Split ess:description HTML into sections on <h3> headings."""
    leading = re.split(r'<h3>', html, maxsplit=1)[0].strip()
    sections = []
    if leading:
        sections.append({
            "id": "beschrijving",
            "h2": "Beschrijving",
            "body_html": leading,
            "section_kind": "content",
        })
    return sections

def _strip_tags(html: str) -> str:
    return re.sub(r'<[^>]+>', '', html).strip()


def truncate_sentences(text: str, max_sentences: int = 2) -> str:
    """Keep at most max_sentences sentences from text; append '...' if cut."""
    if not text:
        return text
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= max_sentences:
        return text
    return " ".join(sentences[:max_sentences]).rstrip(".") + "..."


def fix_desc_paths(html: str, root: str) -> str:
    """Prepend root to relative src/href attributes in description HTML.
    Also converts <canvas>path</canvas> and <canvas src="path"> to <img src="path">.
    Allows RDF descriptions to use paths like assets/images/foo.png
    regardless of the output page depth."""
    if not html:
        return html
    # <canvas>path</canvas> → <img src="path" ...>
    html = re.sub(
        r'<canvas>([^<]+)</canvas>',
        lambda m: f'<img src="{m.group(1).strip()}" style="max-width:100%;height:auto;margin:1rem 0;">',
        html,
    )
    # <canvas src="path" ...> → <img src="path" ...>
    html = re.sub(r'<canvas(\s[^>]*)?>', lambda m: f'<img{m.group(1) or ""}>', html)
    html = re.sub(r'</canvas>', '</img>', html)
    if not root:
        return html
    html = re.sub(r'src="(?!https?://|//|/)([^"]+)"',
                  lambda m: f'src="{root}{m.group(1)}"', html)
    html = re.sub(r'href="(?!https?://|//|#|/)([^"]+)"',
                  lambda m: f'href="{root}{m.group(1)}"', html)
    return html

# ---------------------------------------------------------------------------
# Href helpers
# ---------------------------------------------------------------------------

def practice_href(practice_slug: str, root: str = "") -> str:
    return f"{root}practice/{practice_slug}.html"

def activity_href(act_slug: str, root: str = "") -> str:
    return f"{root}act/{act_slug}.html"

def wp_href(wp_slug: str, root: str = "") -> str:
    return f"{root}wp/{wp_slug}.html"

# ---------------------------------------------------------------------------
# Per-page context builders
# ---------------------------------------------------------------------------

def build_nav_practices(g: Graph, root: str = "") -> list[dict]:
    """Build the list of practices for the top-nav dropdown."""
    result = []
    for practice in g.objects(METHOD_URI, ESS.ownedElements):
        if (practice, RDF.type, ESS.Practice) not in g:
            continue
        s = slug(practice)
        cfg = PRACTICE_CFG.get(s, {})
        result.append({
            "id":    s,
            "title": cfg.get("nav_title") or get_name(g, practice),
            "href":  practice_href(s, root),
            "color": cfg.get("color", "mva"),
        })
    return result


def _base_ctx(g: Graph, root: str = "", data_prac: str = "",
              title: str = "", description: str = "") -> dict:
    return {
        "title":       title,
        "description": description,
        "root":        root,
        "css_path":    f"{root}style.css",
        "data_prac":   data_prac,
        "nav_practices": build_nav_practices(g, root),
    }


# ── index.html ──────────────────────────────────────────────────────────────

def build_index_ctx(g: Graph) -> dict:
    method_name = get_name(g, METHOD_URI)
    method_brief = get_brief(g, METHOD_URI)

    # Collect practices in order
    practices = []
    for practice in g.objects(METHOD_URI, ESS.ownedElements):
        if (practice, RDF.type, ESS.Practice) not in g:
            continue
        s = slug(practice)
        cfg = PRACTICE_CFG.get(s, {})
        practices.append({
            "id":    s,
            "title": get_name(g, practice),
            "brief": get_brief(g, practice),
            "href":  practice_href(s),
            "color": cfg.get("color", "mva"),
        })

    # Path cards: portfolio and project entry points
    port_uri = URIRef(BASE + "practice/portfolio-lifecycle")
    wf_uri   = URIRef(BASE + "practice/project-lifecycle")
    paths = [
        {
            "level": "Portfolio context",
            "role":  "Enterprise Architect · Portfolio Manager",
            "title": "Portfolio",
            "desc":  get_brief(g, port_uri) or "Stuur de architectuurvolwassenheid over meerdere projecten heen via fases en gates.",
            "bullets": [
                {"label": "Fases",  "text": "Initiatie · Planning · Uitvoering · Optimalisatie"},
                {"label": "Gates",  "text": "Gericht · Bruikbaar · Gevestigd"},
                {"label": "Alpha",  "text": "Architectuur · Governance"},
            ],
            "cta":  "Portfolio spoor",
            "href": practice_href("portfolio-lifecycle"),
            "css":  "border-t-[var(--port)] hover:border-t-[var(--port)]",
        },
        {
            "level": "Project context",
            "role":  "Architecture Owner · Projectleider",
            "title": "Project",
            "desc":  get_brief(g, wf_uri) or "Begeleid één project van requirementsdefinitie tot operationele test via vaste fases.",
            "bullets": [
                {"label": "Fases",  "text": "Requirementsdefinitie → Operationele test"},
                {"label": "Gates",  "text": "Gericht · Omschreven · Bewezen · Bruikbaar · Gevestigd"},
                {"label": "Alpha",  "text": "Architectuur · Architectuurbeslissingen"},
            ],
            "cta":  "Project",
            "href": practice_href("project-lifecycle"),
            "css":  "border-t-[var(--wf)] hover:border-t-[var(--wf)]",
        },
    ]

    # Process steps
    steps = [
        {
            "num": "01",
            "title": "Begrijpen",
            "desc": "Identificeer en kwantificeer de sturende eisen met meetbare succescriteria.",
            "metric": "ASRs geïdentificeerd",
        },
        {
            "num": "02",
            "title": "Richten",
            "desc": "Maak de architectuurrichting zichtbaar in een beknopte visie.",
            "metric": "Architectuur Gericht",
        },
        {
            "num": "03",
            "title": "Kiezen",
            "desc": "Neem en documenteer de architectureel significante beslissingen.",
            "metric": "Beslissingen Beslist",
        },
        {
            "num": "04",
            "title": "Bewijzen",
            "desc": "Bewijs de risicovolste integratiekeuzes via prototypes of PoC's.",
            "metric": "Architectuur Aangetoond",
        },
        {
            "num": "05",
            "title": "Plannen",
            "desc": "Maak de roadmap en stel de transitiestaten vast.",
            "metric": "Architectuur Bruikbaar",
        },
        {
            "num": "06",
            "title": "Borgen",
            "desc": "Begeleid de levering en stel governance bij op basis van bewijs.",
            "metric": "Governance Effectief",
        },
    ]

    # Background decks: the 5 practices
    decks = []
    for prac in practices:
        decks.append({
            "href":  prac["href"],
            "color": prac["color"],
            "tag":   "Practice",
            "title": prac["title"],
            "desc":  truncate_sentences(prac["brief"], 2),
            "open":  "Bekijk practice",
        })

    ctx = _base_ctx(g, root="", data_prac="mva",
                    title=method_name, description=method_brief)
    ctx.update({
        "hero_data": {
            "kicker":   "Essence Methode",
            "h1_pre":   method_name,
            "title_en": get_name(g, METHOD_URI, lang="en") or "Way of Working",
            "lede":     method_brief,
            "chips":    [p["title"] for p in practices],
        },
        "toolbar": [
            {"href": "#start",       "label": "Kies de context"},
            {"href": "#achtergrond", "label": "Practices"},
        ],
        "sections": {
            "start": {
                "num":   "01",
                "title": "Kies de context",
                "intro": "De methode ondersteunt twee contexten — kies het spoor dat bij jouw situatie past.",
                "paths": paths,
                "note":  "Beide sporen delen dezelfde practices en werken samen — portfolio levert de kaders voor projecten.",
            },
            "achtergrond": {
                "num":   "02",
                "title": "Practices in deze methode",
                "intro": "De methode bestaat uit vijf samenhangende practices.",
                "decks": decks,
                "panel": {
                    "title": "Gebaseerd op Essence v2.0",
                    "body":  [
                        "De methode is uitgedrukt in de Essence-taal (OMG ptc/25-05-01). "
                        "De ontologie, kernel en alle method-elementen zijn beschikbaar als RDF.",
                    ],
                },
            },
        },
    })
    return ctx


# ── practices.html ──────────────────────────────────────────────────────────

def build_practices_ctx(g: Graph) -> dict:
    practices = []
    for practice in g.objects(METHOD_URI, ESS.ownedElements):
        if (practice, RDF.type, ESS.Practice) not in g:
            continue
        s = slug(practice)
        cfg = PRACTICE_CFG.get(s, {})
        if s in PHASE_PRACTICES:
            phases, _ = _phase_patterns(g, practice)
            tags = [get_name(g, p) for p in phases[:3] if get_name(g, p)]
        else:
            acts = sorted_activities(g, practice)
            tags = [get_name(g, a) for a in acts[:3] if get_name(g, a)]
        practices.append({
            "id":        s,
            "href":      practice_href(s),
            "title":     get_name(g, practice),
            "desc":      get_brief(g, practice),
            "color":     cfg.get("color", "mva"),
            "tags":      tags,
            "icon_path": cfg.get("icon_path", ""),
        })

    ctx = _base_ctx(g, root="", data_prac="mva",
                    title="Practices", description="Overzicht van alle practices")
    ctx.update({
        "hero_data": {
            "kicker": "Essence Methode",
            "h1_pre": "Practices",
            "h1_br":  False,
            "h1_em":  "",
            "lede":   "De methode bestaat uit vijf samenhangende practices.",
        },
        "practices": practices,
    })
    return ctx


# ── practice page (wow / governance) ────────────────────────────────────────

# Practices that organise activities into phases (ess:Pattern) rather than
# owning them directly as ess:Activity elements.
PHASE_PRACTICES = {"project-lifecycle", "portfolio-lifecycle"}


def _phase_patterns(g: Graph, practice_uri) -> tuple[list, list]:
    """Return (phases, gates) as separate lists of Pattern URIs, in RDF order."""
    phases: list = []
    gates: list = []
    for el in g.objects(practice_uri, ESS.ownedElements):
        if (el, RDF.type, ESS.Pattern) not in g:
            continue
        s = slug(el)
        if "gate" in s:
            gates.append(el)
        else:
            phases.append(el)
    return phases, gates


def _phase_activities(g: Graph, phase_uri) -> list:
    """Return Activity URIs included in a phase via its 'bevat' PatternAssociation."""
    for assoc in g.objects(phase_uri, ESS.associations):
        name_nl = get_name(g, assoc, lang="nl")
        name_en = get_name(g, assoc, lang="en")
        if "bevat" in name_nl.lower() or "includes" in name_en.lower():
            return [el for el in g.objects(assoc, ESS.elements)
                    if (el, RDF.type, ESS.Activity) in g]
    return []


def _phase_lods(g: Graph, phase_uri) -> list[dict]:
    """Return [{wp_name, wp_href, lod_names}] grouped by workproduct for a phase's
    'detailniveau' PatternAssociation."""
    for assoc in g.objects(phase_uri, ESS.associations):
        name_nl = get_name(g, assoc, lang="nl")
        name_en = get_name(g, assoc, lang="en")
        if "detailniveau" in name_nl.lower() or "level of detail" in name_en.lower():
            # Group LODs by their owning workproduct
            groups: dict = {}  # wp_uri → list of lod names
            for el in g.objects(assoc, ESS.elements):
                if (el, RDF.type, ESS.LevelOfDetail) not in g:
                    continue
                wp = next(g.subjects(ESS.levelOfDetail, el), None)
                groups.setdefault(wp, []).append(get_name(g, el))
            result = []
            for wp, lod_names in groups.items():
                wp_slug = slug(wp) if wp else None
                result.append({
                    "wp_name": get_name(g, wp) if wp else "",
                    "wp_href": f"../wp/{wp_slug}.html" if wp_slug else None,
                    "lod_names": lod_names,
                })
            return result
    return []


def _phase_lod_filter(g: Graph, phase_uri) -> dict:
    """Return {wp_uri: [lod_name, ...]} for the phase's 'detailniveau' association.
    Used to restrict LOD display on activity outputs to only phase-relevant levels."""
    for assoc in g.objects(phase_uri, ESS.associations):
        name_nl = get_name(g, assoc, lang="nl")
        name_en = get_name(g, assoc, lang="en")
        if "detailniveau" in name_nl.lower() or "level of detail" in name_en.lower():
            result: dict = {}
            for el in g.objects(assoc, ESS.elements):
                if (el, RDF.type, ESS.LevelOfDetail) not in g:
                    continue
                wp = next(g.subjects(ESS.levelOfDetail, el), None)
                if wp:
                    result.setdefault(wp, []).append(get_name(g, el))
            return result
    return {}


def _gate_state(g: Graph, gate_uri):
    """Return the alpha State URI that a gate checks (via 'sluit aan op' assoc)."""
    for assoc in g.objects(gate_uri, ESS.associations):
        name_nl = get_name(g, assoc, lang="nl")
        name_en = get_name(g, assoc, lang="en")
        if "sluit aan op" in name_nl.lower() or "aligns" in name_en.lower():
            for el in g.objects(assoc, ESS.elements):
                if "activity/" not in str(el):
                    return el
    return None


def _gate_govern_activity(g: Graph, gate_uri):
    """Return (name, href) of the governance activity referenced by this gate, or None."""
    for assoc in g.objects(gate_uri, ESS.associations):
        for el in g.objects(assoc, ESS.elements):
            el_str = str(el)
            if "activity/" in el_str:
                act_slug = el_str.rstrip("/").split("/")[-1]
                return get_name(g, el), f"../act/{act_slug}.html"
    return None


def _gate_for_phases(g: Graph, phases: list, gates: list) -> dict:
    """Map phase_uri → gate_uri via direct 'afgesloten door'/'concluded by' association."""
    result: dict = {}
    for phase in phases:
        for assoc in g.objects(phase, ESS.associations):
            name_nl = get_name(g, assoc, lang="nl")
            name_en = get_name(g, assoc, lang="en")
            if "afgesloten door" in name_nl.lower() or "concluded by" in name_en.lower():
                gate = next(g.objects(assoc, ESS.elements), None)
                if gate:
                    result[phase] = gate
                break
    return result


def _phase_desc_html(g: Graph, phase_uri) -> str:
    """Return a phase's full description HTML, minus the 'Activiteiten in deze
    fase' section (that content is already shown via the activity cards)."""
    desc = get_desc(g, phase_uri)
    if not desc:
        return ""
    desc = re.split(r'<h4>', desc, maxsplit=1)[0].strip()
    return fix_desc_paths(desc, "../")


def _build_phase_domains(g: Graph, practice_uri, practice_slug: str) -> list[dict]:
    """Build the `domains` list for wow.html.j2 from phase patterns."""
    cfg = PRACTICE_CFG.get(practice_slug, {})
    phases, gates = _phase_patterns(g, practice_uri)
    gate_map = _gate_for_phases(g, phases, gates)

    # Count total activities across all phases for continuous numbering
    all_phase_acts = [_phase_activities(g, phase) for phase in phases]
    total_all = sum(len(a) for a in all_phase_acts)

    domains: list = []
    running_num = 0
    for phase, phase_acts in zip(phases, all_phase_acts):
        lod_filter = _phase_lod_filter(g, phase)  # {} means no LODs; None means unfiltered
        items = [
            _activity_dict(g, act, running_num + i + 1, total_all, practice_slug,
                           lod_filter=lod_filter)
            for i, act in enumerate(phase_acts)
        ]
        running_num += len(phase_acts)

        # Alphas touched inside this phase
        alpha_names = []
        for act in phase_acts:
            n = primary_alpha_name(g, act)
            if n and n not in alpha_names:
                alpha_names.append(n)

        # Gate connector
        gate = gate_map.get(phase)
        if gate:
            govern = _gate_govern_activity(g, gate)
            connector = {
                "is_gate":       True,
                "name":          get_name(g, gate),
                "brief":         get_brief(g, gate),
                "govern_name":   govern[0] if govern else None,
                "govern_href":   govern[1] if govern else None,
            }
        else:
            connector = {"is_gate": False}

        header_light = cfg.get("header_light", False)
        domains.append({
            "name":            get_name(g, phase),
            "alphas":          " · ".join(alpha_names),
            "desc_html":       _phase_desc_html(g, phase),
            "lods":            _phase_lods(g, phase),
            "css":             cfg.get("css", "bg-slate-700"),
            "gradient":        cfg.get("gradient", ""),
            "num_color":       cfg.get("num_color", "bg-slate-700"),
            "num_text_color":  "text-slate-800" if header_light else "text-white",
            "header_light":    header_light,
            "connector_after": connector,
            "items":           items,
        })

    return domains


def build_phase_practice_ctx(g: Graph, practice_uri) -> tuple[dict, str]:
    """Context builder for waterfall / portfolio-lifecycle (phase-based practices)."""
    s = slug(practice_uri)
    cfg = PRACTICE_CFG.get(s, {})

    title = get_name(g, practice_uri)
    brief = get_brief(g, practice_uri)
    desc  = get_desc(g, practice_uri)

    domains = _build_phase_domains(g, practice_uri, s)

    # Collect all unique activities across all phases for tags / nav
    all_acts: list = []
    seen: set = set()
    for domain in domains:
        for item in domain["items"]:
            href = item.get("href", "")
            if href not in seen:
                all_acts.append(item)
                seen.add(href)

    # Parse description into prose sections
    prose_parts = re.findall(r'<p[^>]*>(.*?)</p>', desc, re.DOTALL)
    prose_text = " ".join(_strip_tags(p) for p in prose_parts[:2] if p.strip())

    ctx = _base_ctx(g, root="../", data_prac=cfg.get("color", "mva"),
                    title=title, description=brief)

    # Collect description sections (phase details come from the desc HTML)
    desc_sections: list = []
    phase_blocks = re.findall(
        r'<p><strong>(Fase[^<]+):</strong>(.*?)</p>', desc, re.DOTALL
    )
    if not phase_blocks:
        # Fallback: plain prose
        desc_sections = [{"id": "beschrijving", "h2": "Beschrijving",
                          "body_html": desc, "section_kind": "content"}]

    ctx.update({
        "hero_data": {
            "kicker":   "Practice",
            "h1_pre":   title,
            "h1_br":    False,
            "title_en": get_name(g, practice_uri, lang="en"),
            "lede":     brief,
        },
        "crumbs": [
            {"href": "../practices.html", "label": "Practices"},
            {"href": None, "label": title},
        ],
        "spoor":            cfg.get("spoor", "solution"),
        "inherited_context": None,
        "activities": {
            "title": "Beschrijving",
            "intro": fix_desc_paths(desc, "../") or brief,
            "domains_title": "Fasen en activiteiten",
            "domains": domains,
        },
        "diff_grid":  None,
        "role":       None,
        "work_products": [],
        "closing_panel": {
            "title": "Over deze practice",
            "body":  [brief],
        },
        "roles": {"intro": "", "cards": []},
    })
    return ctx, "wow.html.j2"


def _activity_dict(g: Graph, act_uri, num: int, total: int,
                   practice_slug: str, lod_filter: dict = None) -> dict:
    s = slug(act_uri)
    cfg = PRACTICE_CFG.get(practice_slug, {})
    domain_color = activity_domain_color(g, act_uri) if cfg.get("domain_colored") else {}
    return {
        "type":           "activity",
        "href":           activity_href(s, root="../"),
        "num":            f"{num:02d}",
        "act_num":        f"Activiteit {num:02d} / {total:02d}",
        "title":          get_name(g, act_uri),
        "title_en":       get_name(g, act_uri, lang="en"),
        "desc":           get_brief(g, act_uri),
        "lede":           get_brief(g, act_uri),
        "phase":          activity_phase(g, act_uri),
        "practice_level": cfg.get("level_label", ""),
        "chips": {
            "space": activity_space_chip(g, act_uri),
            "comp":  "" if not cfg.get("show_comp", True) else "Masters",
            "alpha": primary_alpha_name(g, act_uri),
        },
        "inputs":    activity_inputs(g, act_uri),
        "outputs":   activity_outputs(g, act_uri, lod_filter=lod_filter),
        "patterns":  activity_patterns(g, act_uri),
        "alpha_bar": alpha_bar_html(g, act_uri),
        "domain":         domain_color.get("domain"),
        "num_color":      domain_color.get("num_color"),
        "num_text_color": domain_color.get("num_text_color"),
    }


def build_practice_ctx(g: Graph, practice_uri) -> tuple[dict, str]:
    s = slug(practice_uri)
    if s in PHASE_PRACTICES:
        return build_phase_practice_ctx(g, practice_uri)
    cfg = PRACTICE_CFG.get(s, {})
    template = cfg.get("template", "wow.html.j2")

    acts = sorted_activities(g, practice_uri)
    total = len(acts)

    items = [
        _activity_dict(g, act, i + 1, total, s)
        for i, act in enumerate(acts)
    ]

    # Work products owned by this practice
    wps = []
    for el in g.objects(practice_uri, ESS.ownedElements):
        if (el, RDF.type, ESS.WorkProduct) in g:
            ws = slug(el)
            wps.append({
                "title":  get_name(g, el),
                "desc":   get_brief(g, el),
                "proves": wp_proves(g, el),
                "href":   wp_href(ws, root="../"),
            })

    # Role(s) for this practice
    role_dicts = []
    for assoc_uri in g.objects(practice_uri, ESS.associations):
        assoc_name_en = get_name(g, assoc_uri, lang="en")
        if assoc_name_en.lower() != "performed by":
            continue
        role_uris = list(g.objects(assoc_uri, ESS.elements))
        for r in role_uris:
            rs = slug(r)
            rcfg = ROLE_CFG.get(rs, {})
            role_dicts.append({
                "id":           rs,
                "name":         get_name(g, r),
                "desc":         get_brief(g, r),
                "level":        cfg.get("level_label", ""),
                "head_color":   rcfg.get("head_color", "bg-slate-700"),
                "competencies": rcfg.get("competencies", []),
                "owns":         ", ".join(wp["title"] for wp in wps[:3]),
                "intro":        "De volgende rol voert de activiteiten in deze practice uit.",
                "involves":     ", ".join(get_name(g, a) for a in acts),
            })
        break
    role_dict = role_dicts[0] if role_dicts else None

    domain_name = cfg.get("domain_name", get_name(g, practice_uri))
    # Alphas touched by activities in this practice
    alpha_names = []
    for act in acts:
        n = primary_alpha_name(g, act)
        if n and n not in alpha_names:
            alpha_names.append(n)

    header_light = cfg.get("header_light", False)
    domains = [{
        "name":            domain_name,
        "alphas":          " · ".join(alpha_names),
        "css":             cfg.get("css", "bg-slate-700"),
        "gradient":        cfg.get("gradient", ""),
        "num_color":       cfg.get("num_color", "bg-slate-700"),
        "num_text_color":  "text-slate-800" if header_light else "text-white",
        "header_light":    header_light,
        "connector_after": {"is_gate": False},
        "items":           items,
    }]

    title = get_name(g, practice_uri)
    brief = get_brief(g, practice_uri)

    ctx = _base_ctx(g, root="../", data_prac=cfg.get("color", "mva"),
                    title=title, description=brief)
    ctx.update({
        "hero_data": {
            "kicker":   "Practice",
            "h1_pre":   title,
            "h1_br":    False,
            "title_en": get_name(g, practice_uri, lang="en"),
            "lede":     brief,
        },
        "crumbs": [
            {"href": "../practices.html", "label": "Practices"},
            {"href": None, "label": title},
        ],
        "spoor": cfg.get("spoor", "enterprise"),
        "inherited_context": None,
        "activities": {
            "title": "Activiteiten",
            "intro": fix_desc_paths(get_desc(g, practice_uri), "../") or brief,
            "domains": domains,
        },
        "diff_grid": None,
        "role": role_dict,
        "closing_panel": {
            "title": "Meer over deze practice",
            "body":  [brief, get_desc(g, practice_uri)],
        },
        "work_products": wps,
        # for governance.html.j2 compatibility
        "roles": {
            "intro": "Rollen die deze practice uitvoeren.",
            "cards": role_dicts,
        },
    })
    return ctx, template


# ── activity page ────────────────────────────────────────────────────────────

def build_activity_ctx(g: Graph, act_uri, practice_uri,
                       ordered_acts: list) -> dict:
    s = slug(act_uri)
    ps = slug(practice_uri)
    cfg = PRACTICE_CFG.get(ps, {})

    idx = ordered_acts.index(act_uri)
    total = len(ordered_acts)

    prev_act = ordered_acts[idx - 1] if idx > 0 else None
    next_act = ordered_acts[idx + 1] if idx < total - 1 else None

    # Work products produced (for the wp cards section)
    output_wps = activity_output_wps(g, act_uri)
    wp_cards = []
    for wp_uri in output_wps:
        ws = slug(wp_uri)
        wp_cards.append({
            "title":  get_name(g, wp_uri),
            "desc":   get_brief(g, wp_uri),
            "proves": wp_proves(g, wp_uri),
            "href":   wp_href(ws, root="../"),
        })

    # Approach
    approach_uri = next(g.objects(act_uri, ESS.approach), None)
    approach = None
    if approach_uri:
        ap_desc = get_desc(g, approach_uri) or get_brief(g, approach_uri)
        if ap_desc:
            approach = {
                "name": get_name(g, approach_uri),
                "desc": ap_desc,
            }

    # Prose from description — split on <p> tags; fall back to raw desc, then brief
    desc_html = get_desc(g, act_uri)
    prose_parts = re.findall(r'<p[^>]*>(.*?)</p>', desc_html, re.DOTALL)
    if prose_parts:
        prose = [p.strip() for p in prose_parts if p.strip()]
    elif desc_html.strip():
        prose = [desc_html.strip()]
    else:
        prose = []

    # Actions on work products and alphas
    _kind_nl  = {"create": "Aanmaken", "read": "Lezen", "update": "Bijwerken"}
    _kind_css = {
        "create": "border-emerald-700/30 bg-emerald-700/10 text-emerald-700",
        "read":   "border-blue-700/30 bg-blue-700/10 text-blue-700",
        "update": "border-amber-700/30 bg-amber-700/10 text-amber-700",
    }
    actions = []
    for action_uri in g.objects(act_uri, ESS.action):
        kind = _action_kind(g, action_uri)
        wp   = next(g.objects(action_uri, ESS.workProduct), None)
        alph = next(g.objects(action_uri, ESS.alpha), None)
        if wp:
            target_name = get_name(g, wp)
            href = wp_href(slug(str(wp)), root="../")
            target_type = "Werkproduct"
        elif alph:
            target_name = get_name(g, alph)
            href = None
            target_type = "Alpha"
        else:
            continue
        if not target_name:
            continue
        actions.append({
            "kind":     kind,
            "kind_nl":  _kind_nl.get(kind, kind.capitalize()),
            "kind_css": _kind_css.get(kind, ""),
            "target":   target_name,
            "type":     target_type,
            "href":     href,
        })

    # CompletionCriteria
    def _state_label(state_uri) -> str:
        n = get_name(g, state_uri)
        if n:
            return n
        local = str(state_uri).split("#")[-1].split("/")[-1]
        return local.replace("_", " ")

    def _alpha_from_state(state_uri) -> str:
        alpha = next(g.subjects(ESS.states, state_uri), None)
        if alpha:
            return get_name(g, alpha)
        local = str(state_uri).split("#")[-1]
        parts = local.split("_")
        return parts[0] if len(parts) > 1 else ""

    completion_criteria = []
    for crit_uri in g.objects(act_uri, ESS.criterion):
        if (crit_uri, RDF.type, ESS.CompletionCriterion) not in g:
            continue
        state = next(g.objects(crit_uri, ESS.state), None)
        if not state:
            continue
        completion_criteria.append({
            "alpha": _alpha_from_state(state),
            "state": _state_label(state),
        })

    # Sequence: end-before-start associations
    predecessors = []
    successors = []
    for assoc in g.subjects(RDF.type, ESS.ActivityAssociation):
        kind_vals = list(g.objects(assoc, ESS.associationKind))
        if not kind_vals or str(kind_vals[0]) != "end-before-start":
            continue
        a1 = next(g.objects(assoc, ESS.end1), None)
        a2 = next(g.objects(assoc, ESS.end2), None)
        if a2 == act_uri and a1:
            predecessors.append({
                "name": get_name(g, a1),
                "href": f"../act/{slug(str(a1))}.html",
            })
        if a1 == act_uri and a2:
            successors.append({
                "name": get_name(g, a2),
                "href": f"../act/{slug(str(a2))}.html",
            })
    sequence = {"predecessors": predecessors, "successors": successors} \
        if predecessors or successors else None

    title = get_name(g, act_uri)
    brief = get_brief(g, act_uri)

    ctx = _base_ctx(g, root="../", data_prac=cfg.get("color", "mva"),
                    title=title, description=brief)
    ctx.update({
        "act_name":  title,
        "title_en":  get_name(g, act_uri, lang="en"),
        "lede":      brief,
        "act_num":   f"Activiteit {idx + 1:02d} / {total:02d}",
        "breadcrumb": {
            "parents": [
                {"href": "../practices.html",           "label": "Practices"},
                {"href": f"../practice/{ps}.html",      "label": get_name(g, practice_uri)},
            ],
            "current": title,
        },
        "chips": {
            "space": activity_space_chip(g, act_uri),
            "comp":  "" if not cfg.get("show_comp", True) else "Masters",
        },
        "extra_chips": [],
        "alpha_bar":  alpha_bar_html(g, act_uri),
        "approach":   approach,
        "prose":      prose,
        "actions":    actions,
        "steps":      [],
        "cots_box":   None,
        "work_products": wp_cards,
        "completion_criteria": completion_criteria,
        "sequence":  sequence,
        "roles": None,
        "nav": {
            "prev": {
                "href":  f"../act/{slug(prev_act)}.html",
                "label": f"← {get_name(g, prev_act)}",
            } if prev_act else None,
            "next": {
                "href":  f"../act/{slug(next_act)}.html",
                "label": f"{get_name(g, next_act)} →",
            } if next_act else None,
            "overview": f"../practice/{ps}.html",
        },
    })
    return ctx


# ── workproduct page ─────────────────────────────────────────────────────────

def build_wp_ctx(g: Graph, wp_uri) -> dict:
    s = slug(wp_uri)
    practice_uri = next(g.objects(wp_uri, ESS.owner), None)
    ps = slug(practice_uri) if practice_uri else ""
    cfg = PRACTICE_CFG.get(ps, {})

    title = get_name(g, wp_uri)
    brief = get_brief(g, wp_uri)

    # Alphas via WorkProductManifest
    manifest_uris = list(g.subjects(ESS.workProduct, wp_uri))
    alpha_names = []
    manifests = []
    for m in manifest_uris:
        alpha = next(g.objects(m, ESS.alpha), None)
        if not alpha:
            continue
        alpha_name = get_name(g, alpha)
        lower = str(next(g.objects(m, ESS.lowerBound), "0"))
        upper = str(next(g.objects(m, ESS.upperBound), ""))
        is_kernel = not str(alpha).startswith(BASE)
        if alpha_name and alpha_name not in alpha_names:
            alpha_names.append(alpha_name)
        manifests.append({
            "alpha":       alpha_name,
            "lower_bound": lower,
            "upper_bound": upper,
            "is_kernel":   is_kernel,
        })

    # External resources (ess:resources → ess:content URL)
    wp_resources = []
    for res in g.objects(wp_uri, ESS.resources):
        url = str(next(g.objects(res, ESS.content), ""))
        if url:
            wp_resources.append(url)

    # Levels of detail — ordered via successor chain
    def _ordered_lods(g, wp_uri) -> list:
        lod_uris = list(g.objects(wp_uri, ESS.levelOfDetail))
        if not lod_uris:
            return []
        next_map = {}
        for lod in lod_uris:
            succ = next(g.objects(lod, ESS.successor), None)
            if succ:
                next_map[lod] = succ
        starts = [l for l in lod_uris if l not in next_map.values()]
        result = []
        cur = starts[0] if starts else lod_uris[0]
        visited = set()
        while cur and cur not in visited:
            visited.add(cur)
            result.append(cur)
            cur = next_map.get(cur)
        for l in lod_uris:
            if l not in visited:
                result.append(l)
        return result

    lod_list = []
    for lod_uri in _ordered_lods(g, wp_uri):
        sufficient = str(next(g.objects(lod_uri, ESS.isSufficientLevel), "false")).lower() == "true"
        checks = []
        for cp in g.objects(lod_uri, ESS.checkListItem):
            cp_desc = get_desc(g, cp) or get_brief(g, cp)
            if not cp_desc:
                for obj in g.objects(cp, ESS.description):
                    cp_desc = str(obj); break
            checks.append(cp_desc)
        lod_desc = get_desc(g, lod_uri) or ""
        if not lod_desc:
            for obj in g.objects(lod_uri, ESS.description):
                lod_desc = str(obj); break
        lod_list.append({
            "name":      get_name(g, lod_uri),
            "desc":      lod_desc,
            "sufficient": sufficient,
            "checks":    checks,
        })

    meta_pills = []
    if alpha_names:
        meta_pills.append("Alpha: " + " · ".join(alpha_names))
    if practice_uri:
        meta_pills.append(get_name(g, practice_uri))

    sections = parse_wp_desc(fix_desc_paths(get_desc(g, wp_uri), "../"))

    # TypedResource with kind=type/template
    TEMPLATE_TYPE = URIRef(BASE + "type/template")
    template_url = None
    for owned in g.objects(wp_uri, ESS.ownedElements):
        if (owned, RDF.type, ESS.TypedResource) not in g:
            continue
        kind = next(g.objects(owned, ESS.kind), None)
        if kind == TEMPLATE_TYPE:
            template_url = str(next(g.objects(owned, ESS.content), "")) or None
            break

    download = None
    if template_url:
        ext = template_url.rsplit(".", 1)[-1].lower() if "." in template_url else "docx"
        download = {
            "type":    ext,
            "url":     template_url,
            "filename": template_url.rsplit("/", 1)[-1],
            "desc":    f"Sjabloon voor {title}",
        }

    ctx = _base_ctx(g, root="../", data_prac=cfg.get("color", "mva"),
                    title=title, description=brief)
    ctx.update({
        "kicker":     "Werkproduct",
        "h1_pre":     title,
        "h1_em":      get_name(g, wp_uri, lang="en"),
        "lede":       brief,
        "meta_pills": meta_pills,
        "download":   download,
        "manifests":  manifests,
        "lod_list":   lod_list,
        "resources":  wp_resources,
        "sections": sections,
        "breadcrumb": {
            "parent_href":  f"../practice/{ps}.html",
            "parent_label": get_name(g, practice_uri) if practice_uri else "Practices",
            "current":      title,
        },
    })
    return ctx


# ---------------------------------------------------------------------------
# Jinja2 environment
# ---------------------------------------------------------------------------

def make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
    )
    return env


# ---------------------------------------------------------------------------
# Write helper
# ---------------------------------------------------------------------------

def write_page(env: Environment, template_name: str, ctx: dict,
               out_path: pathlib.Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = env.get_template(template_name).render(**ctx)
    out_path.write_text(html, encoding="utf-8")
    print(f"  wrote {out_path.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading RDF graph…")
    g = load_graph()
    print(f"  {len(g)} triples loaded")

    env = make_env()

    # Copy static assets
    for asset in ("style.css", "nav.js"):
        src = ROOT / "docs" / asset
        if src.exists():
            print(f"  static: {asset} already in docs/")
        else:
            print(f"  warning: docs/{asset} not found — create it")

    print("Generating pages…")

    # index.html
    write_page(env, "index.html.j2",
               build_index_ctx(g),
               DOCS_DIR / "index.html")

    # practices.html
    write_page(env, "practices.html.j2",
               build_practices_ctx(g),
               DOCS_DIR / "practices.html")

    # Practice pages
    for practice in g.objects(METHOD_URI, ESS.ownedElements):
        if (practice, RDF.type, ESS.Practice) not in g:
            continue
        ps = slug(practice)
        ctx, template = build_practice_ctx(g, practice)
        write_page(env, template, ctx,
                   DOCS_DIR / "practice" / f"{ps}.html")

    # Activity pages
    for practice in g.objects(METHOD_URI, ESS.ownedElements):
        if (practice, RDF.type, ESS.Practice) not in g:
            continue
        ps = slug(practice)
        ordered = sorted_activities(g, practice)
        for act in ordered:
            as_ = slug(act)
            ctx = build_activity_ctx(g, act, practice, ordered)
            write_page(env, "act.html.j2", ctx,
                       DOCS_DIR / "act" / f"{as_}.html")

    # Workproduct pages
    for wp in g.subjects(RDF.type, ESS.WorkProduct):
        ws = slug(wp)
        ctx = build_wp_ctx(g, wp)
        write_page(env, "wp.html.j2", ctx,
                   DOCS_DIR / "wp" / f"{ws}.html")

    print("Done.")


if __name__ == "__main__":
    main()
