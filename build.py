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

# A Practice is never itself in an area of concern (Customer/Solution/Endeavor) —
# only Alphas and Activities are, via ess:tags in the RDF. Practices therefore all
# get the same neutral colour; per-activity colouring comes from activity_domain_color().
NEUTRAL = "#0f172a"

PRACTICE_CFG = {
    "enterprise-architecture": {
        "color":       "neutral",
        "spoor":       "enterprise",
        "num_color":   f"bg-[{NEUTRAL}]",
        "css":         f"bg-[{NEUTRAL}]",
        "gradient":    f"from-[{NEUTRAL}] to-[{NEUTRAL}]",
        "icon_path":   "<rect x='2' y='2' width='5' height='5'/><rect x='9' y='2' width='5' height='5'/>"
                       "<rect x='2' y='9' width='5' height='5'/><rect x='9' y='9' width='5' height='5'/>",
    },
    "solution-architecture": {
        "color":       "neutral",
        "spoor":       "solution",
        "num_color":   f"bg-[{NEUTRAL}]",
        "css":         f"bg-[{NEUTRAL}]",
        "gradient":    f"from-[{NEUTRAL}] to-[{NEUTRAL}]",
        "icon_path":   "<path d='M8 2L2 14h12L8 2zm0 4l3 6H5l3-6z'/>",
    },
    "architectural-governance": {
        "color":        "neutral",
        "spoor":        "governance",
        "num_color":    f"bg-[{NEUTRAL}]",
        "css":          f"bg-[{NEUTRAL}]",
        "gradient":     f"from-[{NEUTRAL}] to-[{NEUTRAL}]",
        "icon_path":    "<path d='M8 1L1 5v4c0 3.55 2.96 6.88 7 7.93C12.04 15.88 15 12.55 15 9V5L8 1z'/>",
    },
    "project-lifecycle": {
        "color":        "neutral",
        "spoor":        "solution",
        "num_color":    f"bg-[{NEUTRAL}]",
        "css":          f"bg-[{NEUTRAL}]",
        "gradient":     f"from-[{NEUTRAL}] to-[{NEUTRAL}]",
        "icon_path":    "<path d='M2 2h12v2H2V2zm1 3h10v2H3V5zm1 3h8v2H4V8zm1 3h6v2H5v-2zm1 3h4v2H6v-2z'/>",
    },
    "change-management-lifecycle": {
        "color":        "neutral",
        "spoor":        "enterprise",
        "num_color":    f"bg-[{NEUTRAL}]",
        "css":          f"bg-[{NEUTRAL}]",
        "gradient":     f"from-[{NEUTRAL}] to-[{NEUTRAL}]",
        "icon_path":    "<path d='M8 1a7 7 0 015.9 3.2l-1.7.9A5 5 0 008 3V1zm5.9 3.2A7 7 0 0115 8h-2a5 5 0 00-1.8-3.9l1.7-.9zM15 8a7 7 0 01-3.2 5.9l-.9-1.7A5 5 0 0013 8h2zM11.8 13.9A7 7 0 018 15v-2a5 5 0 003.9-1.8l1.9 1.7zM8 15a7 7 0 01-5.9-3.2l1.7-.9A5 5 0 008 13v2zM2.1 11.8A7 7 0 011 8h2a5 5 0 001.8 3.9l-1.7 1.9zM1 8a7 7 0 013.2-5.9l.9 1.7A5 5 0 003 8H1zM4.2 2.1A7 7 0 018 1v2a5 5 0 00-3.9 1.8L2.2 2.1z'/>",
    },
}


# Phase heuristic: first two activities in chain → analyse, rest → dev
ANALYSE_KERNEL_SPACES = {
    str(KERN.UnderstandStakeholderNeeds),
    str(KERN.UnderstandtheRequirements),
}

# Essence Kernel areas of concern (OMG ptc/25-05-01): Solution, Customer, Endeavor.
# Alphas and Activities carry their area of concern directly in the RDF via
# ess:tags (rdf:resource pointing at esk:CustomerAreaOfConcern / SolutionAreaOfConcern /
# EndeavorAreaOfConcern) — this just maps that RDF Tag's local name to our colour key.
AREA_OF_CONCERN_DOMAIN = {
    "CustomerAreaOfConcern":  "customer",
    "SolutionAreaOfConcern":  "solution",
    "EndeavorAreaOfConcern":  "endeavour",
}

# Solid `-700`-weight fills with white text, matching the existing phase badges
# (bg-blue-700 for "analyse", bg-slate-700 for "dev") — one consistent num-badge
# language site-wide, with hues chosen to avoid the blue-700/indigo-700/emerald-700
# already used by the chips.space/comp/alpha chips on the same card.
DOMAIN_COLOR_CFG = {
    "solution": {
        "num_color":      "bg-yellow-600",
        "num_text_color": "text-white",
        "chip_css":       "border-yellow-700/25 bg-yellow-700/10 text-yellow-700",
    },
    "customer": {
        "num_color":      "bg-green-700",
        "num_text_color": "text-white",
        "chip_css":       "border-green-700/25 bg-green-700/10 text-green-700",
    },
    "endeavour": {
        "num_color":      "bg-sky-700",
        "num_text_color": "text-white",
        "chip_css":       "border-sky-700/25 bg-sky-700/10 text-sky-700",
    },
}

# ess:Action CRUD kinds, translated once and reused everywhere an action kind
# is shown (practice-overview activity cards, activity detail page "Acties").
ACTION_KIND_NL = {
    "create": "Aanmaken",
    "read":   "Lezen",
    "update": "Wijzigen",
    "delete": "Verwijderen",
}
ACTION_KIND_CSS = {
    "create": "border-emerald-700/30 bg-emerald-700/10 text-emerald-700",
    "read":   "border-blue-700/30 bg-blue-700/10 text-blue-700",
    "update": "border-amber-700/30 bg-amber-700/10 text-amber-700",
    "delete": "border-red-700/30 bg-red-700/10 text-red-700",
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

def activity_actions_by_kind(g: Graph, activity_uri) -> list[dict]:
    """Return [{"kind", "kind_nl", "kind_css", "wps": [{"name"}]}] for each
    CRUD kind (create/read/update/delete) that this activity has actions for, in that
    canonical order — the same kind labels/colours as the activity detail page's
    "Acties" list, so the overview and detail pages stay consistent.
    """
    by_kind: dict = {}
    seen: set = set()
    for action in g.objects(activity_uri, ESS.action):
        kind = _action_kind(g, action)
        if kind not in ACTION_KIND_NL:
            continue
        wp = next(g.objects(action, ESS.workProduct), None)
        if not wp or (kind, wp) in seen:
            continue
        seen.add((kind, wp))
        n = get_name(g, wp)
        if not n:
            continue
        by_kind.setdefault(kind, []).append({"name": n})
    return [
        {"kind": kind, "kind_nl": ACTION_KIND_NL[kind], "kind_css": ACTION_KIND_CSS[kind],
         "wps": wps}
        for kind in ("create", "read", "update", "delete")
        if (wps := by_kind.get(kind))
    ]

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
    """Return the Essence Kernel area-of-concern colour (Solution/Customer/Endeavour)
    tagged directly on this activity via ess:tags, or {} if untagged."""
    for tag in g.objects(activity_uri, ESS.tags):
        domain = AREA_OF_CONCERN_DOMAIN.get(_alpha_key(tag))
        if domain:
            return {"domain": domain, **DOMAIN_COLOR_CFG[domain]}
    return {}

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
            "color": cfg.get("color", "neutral"),
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
            "color": cfg.get("color", "neutral"),
        })

    # Path cards: one entry point per phase-based practice (project,
    # change management, ...), fully derived from RDF — any practice that
    # organises its activities into phases automatically gets a card here.
    paths = [
        _phase_entrypoint_card(g, practice)
        for practice in g.objects(METHOD_URI, ESS.ownedElements)
        if (practice, RDF.type, ESS.Practice) in g and _is_phase_practice(g, practice)
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

    ctx = _base_ctx(g, root="", data_prac="neutral",
                    title=method_name, description=method_brief)
    ctx.update({
        "hero_data": {
            "kicker":   "Essence methode",
            "h1_pre":   method_name,
            "lede":     method_brief,
            "chips":    [p["title"] for p in practices],
        },
        "toolbar": [
            {"href": "#start",       "label": "Kies de context"},
            {"href": "#achtergrond", "label": "Practices"},
            {"href": "#licentie",    "label": "Licentie"},
        ],
        "sections": {
            "start": {
                "num":   "01",
                "title": "Kies de context",
                "intro": "De methode ondersteunt meerdere contexten — kies het spoor dat bij jouw situatie past.",
                "paths": paths,
                "note":  "Alle sporen delen dezelfde practices en werken samen — verandermanagement levert de architectuurroadmap waarbinnen projecten opleveren.",
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
            "licentie": {
                "num":   "03",
                "title": "Open source licentie",
                "intro": "Zowel de methode-inhoud als de website die je nu bekijkt zijn open source.",
                "panel": {
                    "title": "GNU General Public License v3.0",
                    "body":  [
                        "Deze site en de bijbehorende RDF-bronbestanden zijn vrijgegeven onder de "
                        "GNU General Public License v3.0 (GPLv3). Je mag de broncode en de methode-inhoud "
                        "vrij bekijken, hergebruiken en aanpassen, mits afgeleide werken onder dezelfde "
                        "licentie beschikbaar blijven.",
                        "De volledige licentietekst en broncode staan op "
                        "<a href=\"https://github.com/hietkamp/hietkamp.github.io\" target=\"_blank\" rel=\"noopener\">GitHub</a>, "
                        "in het bestand "
                        "<a href=\"https://github.com/hietkamp/hietkamp.github.io/blob/main/LICENSE\" target=\"_blank\" rel=\"noopener\">LICENSE</a>.",
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
        if _is_phase_practice(g, practice):
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
            "color":     cfg.get("color", "neutral"),
            "tags":      tags,
            "icon_path": cfg.get("icon_path", ""),
        })

    ctx = _base_ctx(g, root="", data_prac="neutral",
                    title="Practices", description="Overzicht van alle practices")
    ctx.update({
        "hero_data": {
            "kicker": "Essence methode",
            "h1_pre": "Practices",
            "h1_br":  False,
            "h1_em":  "",
            "lede":   "De methode bestaat uit vijf samenhangende practices.",
        },
        "practices": practices,
    })
    return ctx


# ── practice page (wow / governance) ────────────────────────────────────────

def _is_phase_practice(g: Graph, practice_uri) -> bool:
    """True if this practice organises activities into phases (ess:Pattern
    ownedElements with 'bevat'/'includes' PatternAssociations) rather than
    owning ess:Activity elements directly. Derived from the RDF structure
    itself, not a hardcoded practice list."""
    phases, _ = _phase_patterns(g, practice_uri)
    return bool(phases)


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


def _strip_fase_prefix(name: str) -> str:
    """Strip a leading 'Fase N — ' / 'Gate N — ' label down to its own name."""
    return name.split("—", 1)[1].strip() if "—" in name else name


def _phase_entrypoint_card(g: Graph, practice_uri) -> dict:
    """Build a homepage entry-point card for any phase-based practice, fully
    derived from its RDF: phases, gates, and the roles/alphas of the
    activities it includes."""
    s = slug(practice_uri)
    cfg = PRACTICE_CFG.get(s, {})
    phases, gates = _phase_patterns(g, practice_uri)

    acts = []
    for phase in phases:
        acts.extend(_phase_activities(g, phase))

    owners = {o for a in acts for o in g.objects(a, ESS.owner)}
    roles: list = []
    for owner in owners:
        for r in practice_role_uris(g, owner):
            n = get_name(g, r)
            if n and n not in roles:
                roles.append(n)

    alphas: list = []
    for a in acts:
        n = primary_alpha_name(g, a)
        if n and n not in alphas:
            alphas.append(n)

    color = cfg.get("color", "neutral")
    return {
        "level": cfg.get("spoor", "").capitalize(),
        "role":  " · ".join(roles),
        "title": get_name(g, practice_uri),
        "desc":  get_brief(g, practice_uri),
        "bullets": [
            b for b in [
                {"label": "Fases", "text": " · ".join(_strip_fase_prefix(get_name(g, p)) for p in phases)},
                {"label": "Gates", "text": " · ".join(_strip_fase_prefix(get_name(g, gt)) for gt in gates)},
                {"label": "Alpha", "text": " · ".join(alphas)},
            ] if b["text"]
        ],
        "cta":  "Bekijk practice",
        "href": practice_href(s),
        "css":  f"border-t-[var(--{color})] hover:border-t-[var(--{color})] [&_.pc-cta]:bg-[var(--{color})]",
    }


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
        items = [
            _activity_dict(g, act, running_num + i + 1, total_all, practice_slug)
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
    """Context builder for phase-based practices (waterfall, project-lifecycle, ...)."""
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

    ctx = _base_ctx(g, root="../", data_prac=cfg.get("color", "neutral"),
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
        "work_products": [],
        "roles": {"intro": "", "cards": []},
    })
    return ctx, "wow.html.j2"


def _activity_dict(g: Graph, act_uri, num: int, total: int,
                   practice_slug: str) -> dict:
    s = slug(act_uri)
    cfg = PRACTICE_CFG.get(practice_slug, {})
    domain_color = activity_domain_color(g, act_uri)
    return {
        "type":           "activity",
        "href":           activity_href(s, root="../"),
        "num":            f"{num:02d}",
        "act_num":        f"Activiteit {num:02d} / {total:02d}",
        "title":          get_name(g, act_uri),
        "desc":           get_brief(g, act_uri),
        "lede":           get_brief(g, act_uri),
        "phase":          activity_phase(g, act_uri),
        "chips": {
            "space": activity_space_chip(g, act_uri),
            "alpha": primary_alpha_name(g, act_uri),
        },
        "actions":   activity_actions_by_kind(g, act_uri),
        "patterns":  activity_patterns(g, act_uri),
        "alpha_bar": alpha_bar_html(g, act_uri),
        "domain":         domain_color.get("domain"),
        "num_color":      domain_color.get("num_color"),
        "num_text_color": domain_color.get("num_text_color"),
    }


def practice_role_uris(g: Graph, practice_uri) -> list:
    """Return the role URIs that perform this practice, via its 'performed by' association."""
    for assoc_uri in g.objects(practice_uri, ESS.associations):
        if get_name(g, assoc_uri, lang="en").lower() != "performed by":
            continue
        return list(g.objects(assoc_uri, ESS.elements))
    return []


def role_competencies(g: Graph, role_uri) -> list:
    """Return the names of Competency individuals required by this role, via its
    'requires competency' association. Skips non-Competency elements (e.g. a
    required CompetencyLevel such as Masters, which is a level, not an area)."""
    for assoc_uri in g.objects(role_uri, ESS.associations):
        if get_name(g, assoc_uri, lang="en").lower() != "requires competency":
            continue
        return [
            get_name(g, el) for el in g.objects(assoc_uri, ESS.elements)
            if (el, RDF.type, ESS.Competency) in g
        ]
    return []


def build_practice_ctx(g: Graph, practice_uri) -> tuple[dict, str]:
    s = slug(practice_uri)
    if _is_phase_practice(g, practice_uri):
        return build_phase_practice_ctx(g, practice_uri)
    cfg = PRACTICE_CFG.get(s, {})

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
    for r in practice_role_uris(g, practice_uri):
        rs = slug(r)
        role_dicts.append({
            "id":           rs,
            "name":         get_name(g, r),
            "desc":         get_brief(g, r),
            "head_color":   f"bg-[{NEUTRAL}]",
            "competencies": role_competencies(g, r),
            "owns":         ", ".join(wp["title"] for wp in wps[:3]),
        })

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

    ctx = _base_ctx(g, root="../", data_prac=cfg.get("color", "neutral"),
                    title=title, description=brief)
    ctx.update({
        "hero_data": {
            "kicker":   "Practice",
            "h1_pre":   title,
            "h1_br":    False,
            "lede":     brief,
        },
        "crumbs": [
            {"href": "../practices.html", "label": "Practices"},
            {"href": None, "label": title},
        ],
        "spoor": cfg.get("spoor", "enterprise"),
        "inherited_context": None,
        "activities": {
            "title": "Beschrijving",
            "intro": fix_desc_paths(get_desc(g, practice_uri), "../") or brief,
            "domains_title": "Activiteiten",
            "domains": domains,
        },
        "diff_grid": None,
        "work_products": wps,
        "roles": {
            "intro": "Rollen die deze practice uitvoeren.",
            "cards": role_dicts,
        },
    })
    return ctx, "wow.html.j2"


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
        wp_owner = next(g.objects(wp_uri, ESS.owner), None)
        wp_cards.append({
            "title":    get_name(g, wp_uri),
            "desc":     get_brief(g, wp_uri),
            "proves":   wp_proves(g, wp_uri),
            "href":     wp_href(ws, root="../"),
            "practice": get_name(g, wp_owner) if wp_owner else "",
        })

    # Approach
    approach_uri = next(g.objects(act_uri, ESS.approach), None)
    approach = None
    if approach_uri:
        ap_desc = get_desc(g, approach_uri) or get_brief(g, approach_uri)
        if ap_desc:
            approach = {
                "name": get_name(g, approach_uri),
                "desc": fix_desc_paths(ap_desc, "../"),
            }

    # Full description HTML, rendered as-is (like wow.html.j2's rdf_prose)
    desc_html = fix_desc_paths(get_desc(g, act_uri), "../")

    # Actions on work products and alphas
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
            "kind_nl":  ACTION_KIND_NL.get(kind, kind.capitalize()),
            "kind_css": ACTION_KIND_CSS.get(kind, ""),
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

    # Sequence: end-before-start associations, limited to activities owned by
    # this same practice — cross-practice associations (e.g. project-lifecycle
    # phase ordering) describe a different kind of sequencing and don't belong
    # in this per-practice "Volgorde" widget.
    predecessors = []
    successors = []
    for assoc in g.subjects(RDF.type, ESS.ActivityAssociation):
        kind_vals = list(g.objects(assoc, ESS.associationKind))
        if not kind_vals or str(kind_vals[0]) != "end-before-start":
            continue
        a1 = next(g.objects(assoc, ESS.end1), None)
        a2 = next(g.objects(assoc, ESS.end2), None)
        if a2 == act_uri and a1 and next(g.objects(a1, ESS.owner), None) == practice_uri:
            predecessors.append({
                "name": get_name(g, a1),
                "href": f"../act/{slug(str(a1))}.html",
            })
        if a1 == act_uri and a2 and next(g.objects(a2, ESS.owner), None) == practice_uri:
            successors.append({
                "name": get_name(g, a2),
                "href": f"../act/{slug(str(a2))}.html",
            })
    sequence = {"predecessors": predecessors, "successors": successors} \
        if predecessors or successors else None

    # Role(s) that perform the owning practice, and so this activity
    role_cards = []
    for r in practice_role_uris(g, practice_uri):
        rs = slug(r)
        role_cards.append({
            "id":           rs,
            "role":         get_name(g, r),
            "scope":        get_name(g, practice_uri),
            "desc":         get_brief(g, r),
            "makes":        ", ".join(wp["title"] for wp in wp_cards[:3]),
            "competencies": role_competencies(g, r),
            "lc_css":       f"[&_.lc-head]:bg-[{NEUTRAL}]",
        })
    roles = {
        "intro": "Rol die deze activiteit uitvoert." if len(role_cards) == 1
                 else "Rollen die deze activiteit uitvoeren.",
        "cards": role_cards,
    } if role_cards else None

    title = get_name(g, act_uri)
    brief = get_brief(g, act_uri)

    ctx = _base_ctx(g, root="../", data_prac=cfg.get("color", "neutral"),
                    title=title, description=brief)
    ctx.update({
        "act_name":  title,
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
            "space":     activity_space_chip(g, act_uri),
            "space_css": activity_domain_color(g, act_uri).get(
                "chip_css", "border-blue-700/25 bg-blue-700/10 text-blue-700"),
        },
        "extra_chips": [],
        "alpha_bar":  alpha_bar_html(g, act_uri),
        "approach":   approach,
        "desc_html":  desc_html,
        "actions":    actions,
        "steps":      [],
        "cots_box":   None,
        "work_products": wp_cards,
        "completion_criteria": completion_criteria,
        "sequence":  sequence,
        "roles": roles,
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
        lod_desc = fix_desc_paths(lod_desc, "../")
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
    template_uri = None
    for owned in g.objects(wp_uri, ESS.ownedElements):
        if (owned, RDF.type, ESS.TypedResource) not in g:
            continue
        kind = next(g.objects(owned, ESS.kind), None)
        if kind == TEMPLATE_TYPE:
            template_url = str(next(g.objects(owned, ESS.content), "")) or None
            template_uri = owned
            break

    download = None
    if template_url:
        ext = template_url.rsplit(".", 1)[-1].lower() if "." in template_url else "docx"
        download = {
            "type":    ext,
            "url":     template_url,
            "filename": template_url.rsplit("/", 1)[-1],
            "desc":    get_brief(g, template_uri) or f"Sjabloon voor {title}",
        }

    ctx = _base_ctx(g, root="../", data_prac=cfg.get("color", "neutral"),
                    title=title, description=brief)
    ctx.update({
        "kicker":     "Werkproduct",
        "h1_pre":     title,
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
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR = ROOT / "static"
    for asset in ("style.css", "nav.js"):
        src = STATIC_DIR / asset
        if src.exists():
            shutil.copy(src, DOCS_DIR / asset)
            print(f"  static: copied {asset} to docs/")
        else:
            print(f"  warning: static/{asset} not found — create it")

    assets_src = STATIC_DIR / "assets"
    if assets_src.exists():
        shutil.copytree(assets_src, DOCS_DIR / "assets", dirs_exist_ok=True)
        print("  static: copied assets/ to docs/assets/")
    else:
        print("  warning: static/assets/ not found — create it")

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
