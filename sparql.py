#!/usr/bin/env python3
"""Voer een SPARQL-query uit tegen de Essence-RDF-graph.

Gebruik:
    python3 sparql.py query.sparql
    python3 sparql.py < query.sparql
    echo "SELECT ..." | python3 sparql.py
"""
import pathlib
import sys

from rdflib import Graph


def load_graph() -> Graph:
    g = Graph()
    for rdf_file in sorted(pathlib.Path("essence").rglob("*.rdf")):
        g.parse(str(rdf_file), format="xml")
    return g


def print_table(headers: list, rows: list) -> None:
    widths = [
        max(len(h), *(len(r[i]) for r in rows)) if rows else len(h)
        for i, h in enumerate(headers)
    ]

    def fmt_row(cells: list) -> str:
        return " | ".join(c.ljust(w) for c, w in zip(cells, widths))

    print(fmt_row(headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(fmt_row(row))


def main() -> None:
    if len(sys.argv) > 1:
        query = pathlib.Path(sys.argv[1]).read_text()
    else:
        query = sys.stdin.read()

    g = load_graph()
    result = g.query(query)

    if not result.vars:
        for row in result:
            print(row)
        return

    headers = [str(v) for v in result.vars]
    rows = [["" if v is None else str(v) for v in row] for row in result]
    print_table(headers, rows)


if __name__ == "__main__":
    main()
