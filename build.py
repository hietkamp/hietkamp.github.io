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
# get the same neutral colour; per-activity/alpha colouring comes from domain_color_for().
NEUTRAL = "#0f172a"
NEUTRAL_TOPBAR = f"bg-[{NEUTRAL}]"

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
    "use-cases": {
        "color":        "neutral",
        "spoor":        "solution",
        "num_color":    f"bg-[{NEUTRAL}]",
        "css":          f"bg-[{NEUTRAL}]",
        "gradient":     f"from-[{NEUTRAL}] to-[{NEUTRAL}]",
        "icon_path":    "<ellipse cx='8' cy='8' rx='6.5' ry='4' fill='none' stroke='currentColor' stroke-width='1.4'/>",
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

# Canonical order of the kernel's Activity Spaces within each area of concern,
# per the Essence Kernel spec (OMG ptc/25-05-01, §8.2.3/8.3.3/8.4.3) — the
# lifecycle sequence each area's activity spaces are defined in, not
# alphabetical. Used to order the activity-space subgroups on activiteiten.html.
ACTIVITY_SPACE_ORDER = [
    "Mogelijkheden verkennen", "Stakeholderbehoeften begrijpen",
    "Stakeholdertevredenheid borgen", "Systeem gebruiken",
    "Requirements begrijpen", "Systeem vormgeven", "Systeem bouwen",
    "Systeem testen", "Systeem uitrollen", "Systeem exploiteren",
    "Werk voorbereiden", "Activiteiten coördineren", "Team ondersteunen",
    "Voortgang bewaken", "Werk afronden",
]

# Custom domain triad — still recognisably yellow/green/blue, but with more
# character than the Tailwind defaults and WCAG-AA text contrast on every fill:
# helder geel #F0C419 carries dark text (white on yellow never reaches 4.5:1),
# dennengroen #1E6B52 and kobalt #2557A7 carry white text (6.3:1 / 6.7:1).
# Chip text uses a darkened variant of the hue so it stays readable on white.
# Colour fills are reserved exclusively for domain meaning — all other chips
# and labels on the site are neutral slate.
DOMAIN_COLOR_CFG = {
    "solution": {
        "num_color":      "bg-[#F0C419]",
        "num_text_color": "text-slate-900",
        "solid_css":      "bg-[#F0C419] text-slate-900 hover:bg-[#DDB213]",
        "chip_css":       "border-[#B89412]/50 bg-[#F0C419]/20 text-[#8A6D03]",
    },
    "customer": {
        "num_color":      "bg-[#1E6B52]",
        "num_text_color": "text-white",
        "solid_css":      "bg-[#1E6B52] text-white hover:bg-[#175843]",
        "chip_css":       "border-[#1E6B52]/30 bg-[#1E6B52]/10 text-[#1E6B52]",
    },
    "endeavour": {
        "num_color":      "bg-[#2557A7]",
        "num_text_color": "text-white",
        "solid_css":      "bg-[#2557A7] text-white hover:bg-[#1E4A8F]",
        "chip_css":       "border-[#2557A7]/30 bg-[#2557A7]/10 text-[#2557A7]",
    },
}

def domain_legend() -> list[dict]:
    """Legend rows explaining the domain-colour system (dot + label), for pages
    where cards are coloured by Customer/Solution/Endeavour but that meaning
    is never otherwise spelled out (alphas.html, activiteiten.html)."""
    return [
        {"label": key.capitalize(), "dot": DOMAIN_COLOR_CFG[key]["num_color"]}
        for key in ("customer", "solution", "endeavour")
    ]

# ess:Action CRUD kinds, translated once and reused everywhere an action kind
# is shown (practice-overview activity cards, activity detail page "Acties").
ACTION_KIND_NL = {
    "create": "Aanmaken",
    "read":   "Lezen",
    "update": "Wijzigen",
    "delete": "Verwijderen",
}
# Neutral on purpose: coloured fills are reserved for the domain triad, so the
# CRUD kind reads from its label, not from a competing hue.
ACTION_KIND_CSS = {
    "create": "border-slate-300 bg-slate-100 text-slate-600",
    "read":   "border-slate-300 bg-slate-100 text-slate-600",
    "update": "border-slate-300 bg-slate-100 text-slate-600",
    "delete": "border-slate-300 bg-slate-100 text-slate-600",
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
    "Acties" list, so the overview and detail pages stay consistent. Covers actions
    on both work products and alphas (an action always targets exactly one of the two).
    """
    by_kind: dict = {}
    seen: set = set()
    for action in g.objects(activity_uri, ESS.action):
        kind = _action_kind(g, action)
        if kind not in ACTION_KIND_NL:
            continue
        target = next(g.objects(action, ESS.workProduct), None) \
            or next(g.objects(action, ESS.alpha), None)
        if not target or (kind, target) in seen:
            continue
        seen.add((kind, target))
        n = get_name(g, target)
        if not n:
            continue
        by_kind.setdefault(kind, []).append({"name": n})
    return [
        {"kind": kind, "kind_nl": ACTION_KIND_NL[kind], "kind_css": ACTION_KIND_CSS[kind],
         "wps": wps}
        for kind in ("create", "read", "update", "delete")
        if (wps := by_kind.get(kind))
    ]

ROLE_TYPE = URIRef(BASE + "type/role")


def role_uris(g: Graph):
    """Yield the role patterns, sorted by name.

    Essence has no Role class: a role is a Pattern that ties required
    competencies, the activities it participates in, and the work products it
    is responsible for together (Essence v2.0, §9.3.2.13). Roles are modelled
    as ess:TypedPattern with ess:kind type/role, which is what distinguishes
    them from the phase and gate patterns — not their rdf:about path.
    """
    roles = [r for r in g.subjects(RDF.type, ESS.TypedPattern)
             if next(g.objects(r, ESS.kind), None) == ROLE_TYPE]
    return sorted(roles, key=lambda r: get_name(g, r))


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

def domain_color_for(g: Graph, uri) -> dict:
    """Return the Essence Kernel area-of-concern colour (Solution/Customer/Endeavour)
    tagged directly on this Activity or Alpha via ess:tags, or {} if untagged."""
    for tag in g.objects(uri, ESS.tags):
        domain = AREA_OF_CONCERN_DOMAIN.get(_alpha_key(tag))
        if domain:
            return {"domain": domain, **DOMAIN_COLOR_CFG[domain]}
    return {}

def _checkpoint_order(cp_uri):
    local = _alpha_key(cp_uri)
    return (0, int(local)) if local.isdigit() else (1, local)

def state_checklist_texts(g: Graph, state_uri) -> list[str]:
    """Return this state's checklist criteria texts, in checkpoint order —
    the conditions that must hold for the alpha to be in this state."""
    checkpoints = sorted(g.objects(state_uri, ESS.checkListItem), key=_checkpoint_order)
    return [t for cp in checkpoints if (t := (get_brief(g, cp) or get_desc(g, cp)))]

def alpha_ordered_states(g: Graph, alpha_uri) -> list:
    """Return this alpha's states in life-cycle order, following ess:successor chains."""
    states = list(g.objects(alpha_uri, ESS.states))
    next_map = {s: next(g.objects(s, ESS.successor), None) for s in states}
    prev_states = set(next_map.values())
    starts = [s for s in states if s not in prev_states]
    result: list = []
    for start in starts:
        cur = start
        while cur and cur not in result:
            result.append(cur)
            cur = next_map.get(cur)
    for s in states:
        if s not in result:
            result.append(s)
    return result

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

def role_href(role_slug: str, root: str = "") -> str:
    return f"{root}role/{role_slug}.html"

def alpha_href(alpha_slug: str, root: str = "") -> str:
    return f"{root}alpha/{alpha_slug}.html"

# ---------------------------------------------------------------------------
# Per-page context builders
# ---------------------------------------------------------------------------

def _base_ctx(g: Graph, root: str = "", data_prac: str = "",
              title: str = "", description: str = "") -> dict:
    return {
        "title":       title,
        "description": description,
        "root":        root,
        "css_path":    f"{root}style.css",
        "data_prac":   data_prac,
    }


# ── Sidenav "siblings" builders ─────────────────────────────────────────────
# The left sidenav is site navigation, not just an in-page table of contents:
# on a detail page it lists the siblings of the thing you're looking at (other
# activities in the same practice, other alphas in the same domain, ...) with
# the current one marked, so you can move sideways without going back to the
# overview. The five flat overview pages (practices/roles/alphas/workproducts/
# activiteiten.html) opt out via ctx["no_sidenav"] = True instead of getting
# an empty sidenav — there's no meaningful "siblings" concept one level above
# the top of each hierarchy.

def _practice_sidenav(g: Graph, current_uri, root: str) -> dict:
    items = []
    for p in g.objects(METHOD_URI, ESS.ownedElements):
        if (p, RDF.type, ESS.Practice) not in g:
            continue
        items.append({"href": practice_href(slug(p), root),
                       "label": get_name(g, p), "current": p == current_uri})
    return {"group_label": "Practices", "icon": "practice", "links": items}


def _activity_sidenav(g: Graph, current_uri, practice_uri,
                       ordered_acts: list, root: str) -> dict:
    items = []
    for i, a in enumerate(ordered_acts):
        domain_color = domain_color_for(g, a)
        items.append({
            "href": activity_href(slug(a), root), "label": get_name(g, a),
            "num": f"{i + 1:02d}", "current": a == current_uri,
            "num_color": domain_color.get("num_color", "bg-slate-700"),
            "num_text_color": domain_color.get("num_text_color", "text-white"),
        })
    return {"group_label": get_name(g, practice_uri), "icon": "activity", "links": items}


def _wp_sidenav(g: Graph, current_uri, practice_uri, root: str) -> dict:
    items = []
    for wp in g.subjects(RDF.type, ESS.WorkProduct):
        if next(g.objects(wp, ESS.owner), None) != practice_uri:
            continue
        items.append({"href": wp_href(slug(wp), root),
                       "label": get_name(g, wp), "current": wp == current_uri})
    items.sort(key=lambda i: i["label"])
    return {"group_label": get_name(g, practice_uri) if practice_uri else "Werkproducten",
            "icon": "wp", "links": items}


def _role_sidenav(g: Graph, current_uri, root: str) -> dict:
    items = []
    for r in role_uris(g):
        items.append({"href": role_href(slug(r), root),
                       "label": get_name(g, r), "current": r == current_uri})
    items.sort(key=lambda i: i["label"])
    return {"group_label": "Rollen", "icon": "role", "links": items}


def _alpha_sidenav(g: Graph, current_uri, root: str) -> dict:
    domain_color = domain_color_for(g, current_uri)
    domain = domain_color.get("domain")
    items = []
    for a in g.subjects(RDF.type, ESS.Alpha):
        if domain_color_for(g, a).get("domain") != domain:
            continue
        items.append({"href": alpha_href(_alpha_key(a), root),
                       "label": get_name(g, a), "current": a == current_uri})
    items.sort(key=lambda i: i["label"])
    return {"group_label": domain.capitalize() if domain else "Alpha", "icon": "alpha",
            "icon_css": domain_color.get("chip_css", "border-slate-300 bg-slate-100 text-slate-500"),
            "links": items}


# ── index.html ──────────────────────────────────────────────────────────────

def build_index_ctx(g: Graph) -> dict:
    method_name = get_name(g, METHOD_URI)
    method_brief = get_brief(g, METHOD_URI)
    download = template_download(g, METHOD_URI, root="")

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
            {"href": "#start",        "label": "Kies de context"},
            {"href": "#achtergrond",  "label": "Practices"},
            {"href": "#hulpmiddelen", "label": "Download"},
            {"href": "#licentie",     "label": "Licentie"},
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
            "hulpmiddelen": {
                "num":      "03",
                "title":    "Hulpmiddelen",
                "intro":    "Download het werkblad om de methode direct toe te passen.",
                "download": download,
            },
            "licentie": {
                "num":   "04",
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
        "no_sidenav": True,
    })
    return ctx


def build_roles_ctx(g: Graph) -> dict:
    roles = []
    for role in role_uris(g):
        s = slug(role)
        roles.append({
            "href":   role_href(s),
            "title":  get_name(g, role),
            "desc":   get_brief(g, role),
            "topbar": DOMAIN_COLOR_CFG["endeavour"]["num_color"],
        })
    roles.sort(key=lambda r: r["title"])

    ctx = _base_ctx(g, root="", data_prac="neutral",
                    title="Rollen", description="Overzicht van alle rollen")
    ctx.update({
        "hero_data": {
            "kicker": "Essence methode",
            "h1_pre": "Rollen",
            "lede":   "De rollen die de activiteiten van de methode uitvoeren.",
        },
        "roles": roles,
        "no_sidenav": True,
    })
    return ctx


def build_alphas_ctx(g: Graph) -> dict:
    by_domain: dict = {}
    for alpha in g.subjects(RDF.type, ESS.Alpha):
        als = _alpha_key(alpha)
        domain = domain_color_for(g, alpha)
        key = domain.get("domain")
        if not key:
            continue
        by_domain.setdefault(key, []).append({
            "href":   alpha_href(als),
            "title":  get_name(g, alpha),
            "desc":   get_brief(g, alpha),
            "domain": key.capitalize(),
            "topbar": domain.get("num_color", NEUTRAL_TOPBAR),
        })

    alpha_groups = [
        {"domain": key.capitalize(), "alphas": sorted(by_domain[key], key=lambda a: a["title"])}
        for key in ("customer", "solution", "endeavour")
        if by_domain.get(key)
    ]

    ctx = _base_ctx(g, root="", data_prac="neutral",
                    title="Alphas", description="Overzicht van alle alphas")
    ctx.update({
        "hero_data": {
            "kicker": "Essence methode",
            "h1_pre": "Alphas",
            "lede":   "De toestandsruimtes die de voortgang van de methode bewaken.",
        },
        "alpha_groups": alpha_groups,
        "no_sidenav": True,
        "domain_legend": domain_legend(),
    })
    return ctx


def build_workproducts_ctx(g: Graph) -> dict:
    # Group work products by their owning practice, in the method's own
    # ownedElements order — the same practice order practices.html renders.
    by_practice: dict = {}
    for wp in g.subjects(RDF.type, ESS.WorkProduct):
        owner = next(g.objects(wp, ESS.owner), None)
        by_practice.setdefault(owner, []).append({
            "href":   wp_href(slug(wp)),
            "title":  get_name(g, wp),
            "desc":   get_brief(g, wp),
            "topbar": NEUTRAL_TOPBAR,
        })

    workproduct_groups = []
    for practice in g.objects(METHOD_URI, ESS.ownedElements):
        wps = by_practice.get(practice)
        if not wps:
            continue
        workproduct_groups.append({
            "practice":     get_name(g, practice),
            "workproducts": sorted(wps, key=lambda w: w["title"]),
        })

    ctx = _base_ctx(g, root="", data_prac="neutral",
                    title="Werkproducten", description="Overzicht van alle werkproducten")
    ctx.update({
        "hero_data": {
            "kicker": "Essence methode",
            "h1_pre": "Werkproducten",
            "lede":   "De werkproducten die de methode oplevert.",
        },
        "workproduct_groups": workproduct_groups,
        "no_sidenav": True,
    })
    return ctx


def build_activities_ctx(g: Graph) -> dict:
    # Group by domain (Customer/Solution/Endeavour, from the activity's own
    # ess:tags), then within each domain by kernel activity space — the same
    # two-level structure the "Alphas" overview already uses for its domains.
    by_domain: dict = {}
    for act in g.subjects(RDF.type, ESS.Activity):
        domain = domain_color_for(g, act)
        key = domain.get("domain")
        if not key:
            continue
        owner = next(g.objects(act, ESS.owner), None)
        space = activity_space_chip(g, act) or "Overig"
        card = {
            "href":     activity_href(slug(act)),
            "title":    get_name(g, act),
            "desc":     get_brief(g, act),
            "practice": get_name(g, owner) if owner else "",
            "topbar":   domain.get("num_color", NEUTRAL_TOPBAR),
        }
        by_domain.setdefault(key, {}).setdefault(space, []).append(card)

    activity_groups = []
    for key in ("customer", "solution", "endeavour"):
        spaces = by_domain.get(key)
        if not spaces:
            continue
        def _space_order(space: str) -> tuple:
            try:
                return (0, ACTIVITY_SPACE_ORDER.index(space))
            except ValueError:
                return (1, space)

        space_groups = [
            {"space": space, "activities": sorted(spaces[space], key=lambda a: a["title"])}
            for space in sorted(spaces, key=_space_order)
        ]
        activity_groups.append({"domain": key.capitalize(), "spaces": space_groups})

    ctx = _base_ctx(g, root="", data_prac="neutral",
                    title="Activiteiten", description="Overzicht van alle activiteiten")
    ctx.update({
        "hero_data": {
            "kicker": "Essence methode",
            "h1_pre": "Activiteiten",
            "lede":   "De activiteiten die de practices van de methode uitvoeren.",
        },
        "activity_groups": activity_groups,
        "no_sidenav": True,
        "domain_legend": domain_legend(),
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
    for phase_num, (phase, phase_acts) in enumerate(zip(phases, all_phase_acts), start=1):
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
            "phase_num":       phase_num,
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
        "sidenav": _practice_sidenav(g, practice_uri, root="../"),
    })
    return ctx, "wow.html.j2"


def _activity_dict(g: Graph, act_uri, num: int, total: int,
                   practice_slug: str) -> dict:
    s = slug(act_uri)
    cfg = PRACTICE_CFG.get(practice_slug, {})
    domain_color = domain_color_for(g, act_uri)
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
        },
        "actions":   activity_actions_by_kind(g, act_uri),
        "patterns":  activity_patterns(g, act_uri),
        "alpha_bar": alpha_bar_html(g, act_uri),
        "domain":         domain_color.get("domain"),
        "num_color":      domain_color.get("num_color"),
        "num_text_color": domain_color.get("num_text_color"),
    }


def practice_role_uris(g: Graph, practice_uri) -> list:
    """Return the role URIs that perform this practice, via its 'performed by' association.
    Matched on the association's URI slug rather than ess:name — these
    PatternAssociations carry no ess:name literal."""
    for assoc_uri in g.objects(practice_uri, ESS.associations):
        if slug(assoc_uri) != "performed-by":
            continue
        return list(g.objects(assoc_uri, ESS.elements))
    return []


def activity_role_uris(g: Graph, activity_uri) -> list:
    """Return the role URIs that participate in this activity, via each role's
    own 'participates in' PatternAssociation (the reverse of practice_role_uris:
    a role lists the activities it participates in, not the other way round)."""
    roles = []
    for assoc_uri in g.subjects(ESS.elements, activity_uri):
        if slug(assoc_uri) != "participates-in":
            continue
        if (assoc_uri, RDF.type, ESS.PatternAssociation) not in g:
            continue
        role = next(g.subjects(ESS.associations, assoc_uri), None)
        if role is not None and role not in roles:
            roles.append(role)
    return roles


def _pattern_elements(g: Graph, pattern_uri, assoc_name: str, element_type) -> list:
    """Return the elements a pattern links to through a named PatternAssociation.

    Selection is on ess:name, which Essence makes mandatory precisely because
    the name carries the meaning of the link (v2.0, §9.3.2.14) — not on the
    association's rdf:about slug.
    """
    for assoc_uri in g.objects(pattern_uri, ESS.associations):
        if get_name(g, assoc_uri).lower() != assoc_name:
            continue
        return [el for el in g.objects(assoc_uri, ESS.elements)
                if (el, RDF.type, element_type) in g]
    return []


def role_activity_uris(g: Graph, role_uri) -> list:
    """Return the activity URIs this role participates in — the forward
    direction of activity_role_uris, used on the role's own detail page."""
    return _pattern_elements(g, role_uri, "neemt deel aan", ESS.Activity)


def role_workproduct_uris(g: Graph, role_uri) -> list:
    """Return the work products this role is responsible for.

    Together with the required competencies and the activities it participates
    in, this is the third leg Essence names when it describes how to model a
    role as a pattern (v2.0, §9.3.2.13).
    """
    return _pattern_elements(g, role_uri, "verantwoordelijk voor", ESS.WorkProduct)


def role_competency_requirements(g: Graph, role_uri) -> dict:
    """Return {Competency URI: CompetencyLevel URI} for this role, by reading
    every 'requires competency' PatternAssociation attached to it. A role can
    have several such associations — one per competency — each pairing
    exactly one ess:Competency with the one ess:CompetencyLevel required for
    it, so different competencies can require different levels (e.g. Leadership
    at Applies, Analysis at Masters). Matched on the association URI's slug
    prefix — see practice_role_uris."""
    reqs: dict = {}
    for assoc_uri in g.objects(role_uri, ESS.associations):
        if "/requires-competency" not in local_path(assoc_uri):
            continue
        elements = list(g.objects(assoc_uri, ESS.elements))
        comp = next((el for el in elements if (el, RDF.type, ESS.Competency) in g), None)
        level = next((el for el in elements if (el, RDF.type, ESS.CompetencyLevel) in g), None)
        if comp is not None:
            reqs[comp] = level
    return reqs


def role_competencies(g: Graph, role_uri) -> list:
    """Return the names of Competency individuals required by this role —
    see role_competency_requirements."""
    return [get_name(g, comp) for comp in role_competency_requirements(g, role_uri)]


def competency_matrix(g: Graph, role_uri) -> list:
    """Return every ess:Competency the Essence Kernel defines — not just this
    role's own subset — each flagged whether it's in this role's 'requires
    competency' associations. Each competency also carries its own
    ess:possibleLevel ladder (ordered by ess:level), with that specific
    competency's own required ess:CompetencyLevel checked — not a single
    level shared across the whole role, since different competencies can
    require different levels (see role_competency_requirements). Competencies
    are grouped by their own ess:tags area of concern (Customer/Solution/
    Endeavour — the same tag used for Alpha/Activity domain colour), in that
    fixed Customer → Solution → Endeavour reading order."""
    reqs = role_competency_requirements(g, role_uri)

    by_domain: dict[str, list] = {}
    for comp in g.subjects(RDF.type, ESS.Competency):
        domain = domain_color_for(g, comp)
        domain_key = domain.get("domain", "")
        is_required = comp in reqs
        required_level_name = get_name(g, reqs[comp]) if is_required and reqs[comp] is not None else ""
        possible_levels = sorted(
            g.objects(comp, ESS.possibleLevel),
            key=lambda lv: int(next(g.objects(lv, ESS.level), 0)),
        )
        by_domain.setdefault(domain_key, []).append({
            "name":          get_name(g, comp),
            "brief":         get_brief(g, comp),
            "checked":       is_required,
            "chip_css":      domain.get("chip_css", ""),
            "dot":           domain.get("num_color", ""),
            "dot_text":      domain.get("num_text_color", "text-white"),
            "levels": [
                {"name": get_name(g, lv), "brief": get_brief(g, lv),
                 "checked": is_required and get_name(g, lv) == required_level_name}
                for lv in possible_levels
            ],
        })

    groups = []
    for key in ("customer", "solution", "endeavour"):
        items = sorted(by_domain.get(key, []), key=lambda c: c["name"])
        if items:
            groups.append({
                "domain": key,
                "label":  key.capitalize(),
                "dot":    DOMAIN_COLOR_CFG[key]["num_color"],
                "items":  items,
            })
    return groups


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
        "sidenav": _practice_sidenav(g, practice_uri, root="../"),
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

    # Action chips, grouped by CRUD kind (Lezen, Aanmaken, Wijzigen, Verwijderen —
    # in that order) so the "Acties" section can render one compact flow row per
    # kind (icon + label, then a chip per target) instead of a full card grid.
    # Each target is a work product (neutral chip) or an alpha (chip tinted in
    # its ess:tags domain colour, same treatment as elsewhere on the site).
    action_by_kind: dict = {}
    for action_uri in g.objects(act_uri, ESS.action):
        kind = _action_kind(g, action_uri)
        if kind not in ACTION_KIND_NL:
            continue
        wp   = next(g.objects(action_uri, ESS.workProduct), None)
        alph = next(g.objects(action_uri, ESS.alpha), None)
        if wp:
            title = get_name(g, wp)
            if not title:
                continue
            chip = {"kind": "wp", "title": title, "href": wp_href(slug(wp), root="../")}
        elif alph:
            title = get_name(g, alph)
            if not title:
                continue
            chip = {
                "kind":     "alpha",
                "title":    title,
                "href":     alpha_href(_alpha_key(alph), root="../"),
                "chip_css": domain_color_for(g, alph).get(
                    "chip_css", "border-slate-300 bg-slate-100 text-slate-500"),
            }
        else:
            continue
        action_by_kind.setdefault(kind, []).append(chip)

    action_groups = [
        {"kind": kind, "kind_nl": ACTION_KIND_NL[kind], "chips": action_by_kind[kind]}
        for kind in ("read", "create", "update", "delete")
        if action_by_kind.get(kind)
    ]

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

    def _lod_groups(crit_uri) -> list[dict]:
        """Group this criterion's ess:levelOfDetail refs by their owning work
        product, so each work product gets its own card of LOD chips."""
        groups: dict = {}
        order: list = []
        for lod in g.objects(crit_uri, ESS.levelOfDetail):
            name = get_name(g, lod)
            if not name:
                continue
            wp = next(
                (s for s in g.subjects(ESS.levelOfDetail, lod)
                 if (s, RDF.type, ESS.WorkProduct) in g),
                None,
            )
            if wp not in groups:
                groups[wp] = []
                order.append(wp)
            groups[wp].append(name)
        return [
            {
                "wp_name": get_name(g, wp) if wp else "",
                "wp_href": wp_href(slug(wp), root="../") if wp else None,
                "lod_names": groups[wp],
            }
            for wp in order
        ]

    # An Entry/CompletionCriterion has two independent aspects — the alpha state
    # it requires or reaches, and (optionally) the level of detail a work product
    # must have — so each becomes its own card: one for the alpha, one per
    # referenced work product. Shared between entry and completion criteria,
    # which differ only in rdf:type.
    def _criterion_cards(criterion_type) -> list[dict]:
        cards = []
        for crit_uri in g.objects(act_uri, ESS.criterion):
            if (crit_uri, RDF.type, criterion_type) not in g:
                continue
            state = next(g.objects(crit_uri, ESS.state), None)
            if state:
                alpha_uri = next(g.subjects(ESS.states, state), None)
                cards.append({
                    "kind":   "alpha",
                    "alpha":  _alpha_from_state(state),
                    "state":  _state_label(state),
                    "href":   alpha_href(_alpha_key(alpha_uri), root="../") if alpha_uri else None,
                    "topbar": domain_color_for(g, alpha_uri).get("num_color", NEUTRAL_TOPBAR)
                              if alpha_uri else NEUTRAL_TOPBAR,
                })
            for group in _lod_groups(crit_uri):
                cards.append({
                    "kind":      "wp",
                    "wp_name":   group["wp_name"],
                    "lod_names": group["lod_names"],
                    "href":      group["wp_href"],
                    "topbar":    NEUTRAL_TOPBAR,
                })
        return cards

    entry_criteria = _criterion_cards(ESS.EntryCriterion)
    completion_criteria = _criterion_cards(ESS.CompletionCriterion)

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

    # Role(s) that participate in this specific activity (via each role's own
    # 'participates in' association), not just any role performing the practice.
    # Shown as a chip in the hero, coloured with the endeavour domain — roles
    # belong to the endeavour area of concern.
    role_chips = [
        {"role": get_name(g, r), "href": role_href(slug(r), root="../"),
         "css":  DOMAIN_COLOR_CFG["endeavour"]["solid_css"]}
        for r in activity_role_uris(g, act_uri)
    ]

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
            "space_css": domain_color_for(g, act_uri).get(
                "chip_css", "border-slate-400/40 bg-slate-100 text-slate-600"),
        },
        "extra_chips": [],
        "alpha_bar":  alpha_bar_html(g, act_uri),
        "approach":   approach,
        "desc_html":  desc_html,
        "action_groups": action_groups,
        "steps":      [],
        "cots_box":   None,
        "entry_criteria": entry_criteria,
        "completion_criteria": completion_criteria,
        "sequence":  sequence,
        "role_chips": role_chips,
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
        "sidenav": _activity_sidenav(g, act_uri, practice_uri, ordered_acts, root="../"),
    })
    return ctx


# ── workproduct page ─────────────────────────────────────────────────────────

TEMPLATE_TYPE = URIRef(BASE + "type/template")

def template_download(g: Graph, owner_uri, root: str = "",
                      fallback_desc: str = "") -> dict | None:
    """Return a wp.html.j2-shaped download dict for owner_uri's ess:TypedResource
    of kind type/template (an ownedElements child pointing at a downloadable
    file via ess:content), or None if it has no such resource.

    ess:content holds the canonical published location of the file, which may be
    an absolute URL. The generated site must stay relative so it also works from
    a local docs/ directory, so only the filename is taken from ess:content and
    the href is rebuilt against the page's own depth via root.
    """
    for owned in g.objects(owner_uri, ESS.ownedElements):
        if (owned, RDF.type, ESS.TypedResource) not in g:
            continue
        if next(g.objects(owned, ESS.kind), None) != TEMPLATE_TYPE:
            continue
        url = str(next(g.objects(owned, ESS.content), "")) or None
        if not url:
            return None
        filename = url.rsplit("/", 1)[-1]
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "docx"
        return {
            "type":     ext,
            "url":      f"{root}downloads/{filename}",
            "filename": filename,
            "desc":     get_brief(g, owned) or fallback_desc,
        }
    return None


WPTEMPLATES_DIR = ROOT / "wptemplates"


def copy_downloads(g: Graph) -> None:
    """Copy every file referenced from the RDF via ess:content into docs/downloads/.

    Work product templates live in wptemplates/ and are maintained by hand; the
    other downloadable assets sit alongside the RDF in essence/. A referenced
    file that cannot be found is reported rather than silently skipped, so a
    dead download button shows up at build time instead of in the browser.
    """
    downloads_dir = DOCS_DIR / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    wanted: set[str] = set()
    for res in g.subjects(RDF.type, ESS.TypedResource):
        url = str(next(g.objects(res, ESS.content), ""))
        if url:
            wanted.add(url.rsplit("/", 1)[-1])
    for res in g.subjects(RDF.type, ESS.Resource):
        url = str(next(g.objects(res, ESS.content), ""))
        if url.lower().endswith((".docx", ".xlsx", ".pdf")):
            wanted.add(url.rsplit("/", 1)[-1])

    search_dirs = (WPTEMPLATES_DIR, ROOT / "essence")
    for filename in sorted(wanted):
        for folder in search_dirs:
            src = folder / filename
            if src.exists():
                shutil.copy(src, downloads_dir / filename)
                print(f"  static: copied {filename} to docs/downloads/")
                break
        else:
            print(f"  warning: {filename} referenced from the RDF but not found "
                  f"in wptemplates/ or essence/")


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

    download = template_download(g, wp_uri, root="../",
                                fallback_desc=f"Sjabloon voor {title}")

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
            "parent_href":  "../workproducts.html",
            "parent_label": "Werkproducten",
            "current":      title,
        },
        "sidenav": _wp_sidenav(g, wp_uri, practice_uri, root="../"),
    })
    return ctx


def build_role_ctx(g: Graph, role_uri) -> dict:
    s = slug(role_uri)
    title = get_name(g, role_uri)
    brief = get_brief(g, role_uri)
    desc = get_desc(g, role_uri)
    beschrijving_html = f"<p>{desc}</p>" if desc else ""

    competency_groups = competency_matrix(g, role_uri)

    activity_cards = []
    for a in role_activity_uris(g, role_uri):
        act_title = get_name(g, a)
        if not act_title:
            continue
        owner = next(g.objects(a, ESS.owner), None)
        activity_cards.append({
            "title":  act_title,
            "desc":   get_brief(g, a),
            "href":   activity_href(slug(a), root="../"),
            "type":   get_name(g, owner) if owner else "Activiteit",
            "topbar": domain_color_for(g, a).get("num_color", NEUTRAL_TOPBAR),
        })

    wp_cards = []
    for wp in role_workproduct_uris(g, role_uri):
        wp_title = get_name(g, wp)
        if not wp_title:
            continue
        owner = next(g.objects(wp, ESS.owner), None)
        wp_cards.append({
            "title":  wp_title,
            "desc":   get_brief(g, wp),
            "href":   wp_href(slug(wp), root="../"),
            "type":   get_name(g, owner) if owner else "Werkproduct",
            "topbar": NEUTRAL_TOPBAR,
        })
    wp_cards.sort(key=lambda c: c["title"])

    sections = [
        {"id": "beschrijving", "h2": "Beschrijving", "body_html": beschrijving_html},
    ]
    if competency_groups:
        sections.append({"id": "competenties", "h2": "Competenties",
                          "section_kind": "competencies", "groups": competency_groups})
    if activity_cards:
        sections.append({"id": "activiteiten", "h2": "Activiteiten",
                          "section_kind": "cards", "cards": activity_cards})
    if wp_cards:
        sections.append({"id": "werkproducten", "h2": "Verantwoordelijk voor",
                          "section_kind": "cards", "cards": wp_cards})

    ctx = _base_ctx(g, root="../", data_prac="neutral", title=title, description=brief)
    ctx.update({
        "kicker":     "Rol",
        "h1_pre":     title,
        "lede":       brief,
        "meta_pills": [],
        "sections":   sections,
        "breadcrumb": {
            "parent_href":  "../roles.html",
            "parent_label": "Rollen",
            "current":      title,
        },
        "sidenav": _role_sidenav(g, role_uri, root="../"),
    })
    return ctx


def build_alpha_ctx(g: Graph, alpha_uri) -> dict:
    title = get_name(g, alpha_uri)
    brief = get_brief(g, alpha_uri)
    desc_html = fix_desc_paths(get_desc(g, alpha_uri), "../")
    domain = domain_color_for(g, alpha_uri)
    topbar = domain.get("num_color", NEUTRAL_TOPBAR)
    topbar_text = domain.get("num_text_color", "text-white")

    state_cards = []
    for state in alpha_ordered_states(g, alpha_uri):
        state_cards.append({
            "title":       get_name(g, state) or _alpha_key(state),
            "desc":        get_brief(g, state) or get_desc(g, state),
            "checklist":   state_checklist_texts(g, state),
            "dot":         topbar,
            "dot_text":    topbar_text,
        })

    sections = [
        {"id": "beschrijving", "h2": "Beschrijving",
         "body_html": desc_html or (f"<p>{brief}</p>" if brief else "")},
    ]
    if state_cards:
        # ess:successor forms a real life-cycle sequence, not just a list — a
        # numbered, connected stepper makes that order visible instead of
        # showing identical stacked cards with no relation to each other.
        sections.append({"id": "toestanden", "h2": "Toestanden",
                          "section_kind": "stepper", "steps": state_cards})

    ctx = _base_ctx(g, root="../", data_prac="neutral", title=title, description=brief)
    ctx.update({
        "kicker":     "Alpha",
        "h1_pre":     title,
        "lede":       brief,
        "meta_pills": [domain["domain"].capitalize()] if domain.get("domain") else [],
        "sections":   sections,
        "breadcrumb": {
            "parent_href":  "../alphas.html",
            "parent_label": "Alphas",
            "current":      title,
        },
        "sidenav": _alpha_sidenav(g, alpha_uri, root="../"),
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

    # Downloadable resources referenced from the RDF via ess:content — copied
    # verbatim into docs/downloads/ so the ess:content path resolves. Which
    # files these are is driven entirely by the RDF: every ess:TypedResource of
    # kind type/template contributes the basename of its ess:content URL, which
    # is looked up in wptemplates/. The templates themselves are hand-maintained
    # and are never regenerated by this build.
    copy_downloads(g)

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

    # roles.html
    write_page(env, "roles.html.j2",
               build_roles_ctx(g),
               DOCS_DIR / "roles.html")

    # alphas.html
    write_page(env, "alphas.html.j2",
               build_alphas_ctx(g),
               DOCS_DIR / "alphas.html")

    # workproducts.html
    write_page(env, "workproducts.html.j2",
               build_workproducts_ctx(g),
               DOCS_DIR / "workproducts.html")

    # activiteiten.html
    write_page(env, "activiteiten.html.j2",
               build_activities_ctx(g),
               DOCS_DIR / "activiteiten.html")

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

    # Werkproductpagina's
    for wp in g.subjects(RDF.type, ESS.WorkProduct):
        ws = slug(wp)
        ctx = build_wp_ctx(g, wp)
        write_page(env, "wp.html.j2", ctx,
                   DOCS_DIR / "wp" / f"{ws}.html")

    # Role pages (roles are ess:TypedPattern individuals of kind type/role —
    # reuses wp.html.j2's generic hero + sections layout)
    for role in role_uris(g):
        rs = slug(role)
        ctx = build_role_ctx(g, role)
        write_page(env, "wp.html.j2", ctx,
                   DOCS_DIR / "role" / f"{rs}.html")

    # Alpha pages (method and Essence Kernel alphas alike — reuses wp.html.j2's
    # generic hero + sections layout, same as role pages)
    for alpha in g.subjects(RDF.type, ESS.Alpha):
        als = _alpha_key(alpha)
        ctx = build_alpha_ctx(g, alpha)
        write_page(env, "wp.html.j2", ctx,
                   DOCS_DIR / "alpha" / f"{als}.html")

    print("Done.")


if __name__ == "__main__":
    main()
