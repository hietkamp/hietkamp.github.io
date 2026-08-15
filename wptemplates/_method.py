"""Leest de Essence-RDF uit, zodat de sjablonen geen inhoud dupliceren.

Titel, practice, korte omschrijving en de herkomst-en-gebruikrelaties van elk
werkproduct staan in `essence/method/**` en worden hier opgehaald. Wijzigt de
RDF, dan wijzigen de sjablonen mee zodra ze opnieuw worden gebouwd.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

from rdflib import RDF, Graph, Namespace

ESS = Namespace("https://www.hietkamp.nl/ontologies/essence-language#")
ESSENCE_DIR = pathlib.Path(__file__).resolve().parent.parent / "essence"


@dataclass
class WorkProduct:
    """Een werkproduct zoals het in de RDF staat."""

    slug: str
    name: str
    brief: str
    practice: str
    created_by: list[str] = field(default_factory=list)
    read_by: list[str] = field(default_factory=list)
    updated_by: list[str] = field(default_factory=list)


def _nl(graph: Graph, subject, predicate) -> str:
    """Nederlandse literal, met Engels als terugvaloptie."""
    for obj in graph.objects(subject, predicate):
        if getattr(obj, "language", None) == "nl":
            return str(obj)
    for obj in graph.objects(subject, predicate):
        return str(obj)
    return ""


def load(essence_dir: pathlib.Path = ESSENCE_DIR) -> dict[str, WorkProduct]:
    """Laad alle werkproducten uit de RDF, gesleuteld op slug."""
    graph = Graph()
    for rdf_file in sorted(essence_dir.rglob("*.rdf")):
        graph.parse(rdf_file, format="xml")

    products: dict[str, WorkProduct] = {}
    for uri in graph.subjects(RDF.type, ESS.WorkProduct):
        slug = str(uri).rstrip("/").split("/")[-1]
        owner = next(graph.objects(uri, ESS.owner), None)
        products[slug] = WorkProduct(
            slug=slug,
            name=_nl(graph, uri, ESS.name),
            brief=_nl(graph, uri, ESS.briefDescription),
            practice=_nl(graph, owner, ESS.name) if owner else "",
        )

    # Koppel de activiteiten die het werkproduct maken, lezen of bijwerken.
    for activity in graph.subjects(RDF.type, ESS.Activity):
        activity_name = _nl(graph, activity, ESS.name)
        for action in graph.objects(activity, ESS.action):
            target = next(graph.objects(action, ESS.workProduct), None)
            if target is None:
                continue
            slug = str(target).rstrip("/").split("/")[-1]
            product = products.get(slug)
            if product is None:
                continue
            kind = str(next(graph.objects(action, ESS.kind), "")).split("#")[-1]
            bucket = {"create": product.created_by,
                      "read": product.read_by,
                      "update": product.updated_by}.get(kind)
            if bucket is not None and activity_name not in bucket:
                bucket.append(activity_name)

    return products
