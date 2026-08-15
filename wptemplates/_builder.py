"""Bouwer voor de werkproduct-sjablonen (wptemplates/*.docx).

Reproduceert exact de bestaande notitie-stijl: Calibri, marineblauwe koppen
(#1F3864), grijze cursieve guidance-regels (#767676), [ … ]-plaatshouders,
lichtblauw gearceerde tabelkoppen (#EFF2F7) en een voettekst met paginanummer.

De opmaakrecepten hieronder zijn afgeleid uit de bestaande .docx-bestanden,
zodat nieuwe sjablonen naadloos naast de oude staan.

Gebruik:
    python3 _builder.py            # bouwt alle sjablonen in dit bestand
"""

from __future__ import annotations

import pathlib
import zipfile
from xml.sax.saxutils import escape

HERE = pathlib.Path(__file__).parent

# --- opmaakrecepten -------------------------------------------------------

CAL = ('<w:rFonts w:ascii="Calibri" w:cs="Calibri" '
       'w:eastAsia="Calibri" w:hAnsi="Calibri"/>')

NAVY = "1F3864"
GREY = "767676"
BODY = "404040"
RULE = "BFBFBF"
SHADE = "EFF2F7"

RPR = {
    # titel bovenaan de pagina
    "title": f'{CAL}<w:b/><w:bCs/><w:color w:val="{NAVY}"/>'
             '<w:sz w:val="30"/><w:szCs w:val="30"/>',
    # practice-aanduiding in kapitalen naast de titel
    "kicker": f'{CAL}<w:b/><w:bCs/><w:color w:val="{NAVY}"/>'
              '<w:sz w:val="15"/><w:szCs w:val="15"/>',
    # korte omschrijving achter de kicker
    "kicker_desc": f'{CAL}<w:i/><w:iCs/><w:color w:val="{GREY}"/>'
                   '<w:sz w:val="18"/><w:szCs w:val="18"/>',
    # label in de metadatatabel
    "meta_label": f'{CAL}<w:b/><w:bCs/><w:color w:val="{GREY}"/>'
                  '<w:sz w:val="18"/><w:szCs w:val="18"/>',
    # waarde in de metadatatabel
    "meta_value": f'{CAL}<w:color w:val="{BODY}"/>'
                  '<w:sz w:val="19"/><w:szCs w:val="19"/>',
    # sectiekop
    "h": f'{CAL}<w:b/><w:bCs/><w:color w:val="{NAVY}"/>'
         '<w:sz w:val="21"/><w:szCs w:val="21"/>',
    # cursieve invulinstructie onder een sectiekop
    "guide": f'{CAL}<w:i/><w:iCs/><w:color w:val="{GREY}"/>'
             '<w:sz w:val="17"/><w:szCs w:val="17"/>',
    # plaatshouder voor de schrijver
    "ph": f'{CAL}<w:color w:val="{BODY}"/>'
          '<w:sz w:val="20"/><w:szCs w:val="20"/>',
    # kopcel van een inhoudelijke tabel
    "th": f'{CAL}<w:b/><w:bCs/><w:i w:val="false"/><w:iCs w:val="false"/>'
          f'<w:color w:val="{NAVY}"/><w:sz w:val="19"/><w:szCs w:val="19"/>',
    # gewone cel van een inhoudelijke tabel
    "td": f'{CAL}<w:b w:val="false"/><w:bCs w:val="false"/>'
          '<w:i w:val="false"/><w:iCs w:val="false"/>'
          '<w:color w:val="000000"/><w:sz w:val="19"/><w:szCs w:val="19"/>',
    # opsommingsregel in "Gereed wanneer"
    "li": f'{CAL}<w:sz w:val="20"/><w:szCs w:val="20"/>',
    # subkop binnen een sectie, bv. "Principe 1"
    "sub": f'{CAL}<w:b/><w:bCs/><w:color w:val="{NAVY}"/>'
           '<w:sz w:val="19"/><w:szCs w:val="19"/>',
    # veldlabel binnen een herhaalbaar blok, bv. "Stelling"
    "field": f'{CAL}<w:b/><w:bCs/><w:color w:val="{BODY}"/>'
             '<w:sz w:val="18"/><w:szCs w:val="18"/>',
}

PLACEHOLDER = "[ … ]"
TABLE_WIDTH = 9638


def _run(text: str, rpr_key: str) -> str:
    return (f'<w:r><w:rPr>{RPR[rpr_key]}</w:rPr>'
            f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r>')


def _p(runs: str, ppr: str = "") -> str:
    return f'<w:p>{f"<w:pPr>{ppr}</w:pPr>" if ppr else ""}{runs}</w:p>'


# --- bouwstenen -----------------------------------------------------------

def title_block(title: str, practice: str, brief: str) -> str:
    """Titel met onderstreping, daaronder practice + korte omschrijving."""
    head = _p(
        _run(title, "title"),
        f'<w:pBdr><w:bottom w:val="single" w:color="{NAVY}" '
        'w:sz="6" w:space="4"/></w:pBdr><w:spacing w:after="40"/>',
    )
    kicker = _p(
        _run(f"{practice.upper()}  ·  ", "kicker") + _run(brief, "kicker_desc"),
        '<w:spacing w:after="200" w:before="80"/>',
    )
    return head + kicker


def meta_table(labels: list[str]) -> str:
    """Randloze label/waarde-tabel direct onder de titel."""
    grid = '<w:gridCol w:w="2600"/><w:gridCol w:w="7038"/>'
    no_border = ('<w:tcBorders>'
                 + "".join(f'<w:{s} w:val="none" w:color="FFFFFF" w:sz="0"/>'
                           for s in ("top", "left", "bottom", "right"))
                 + '</w:tcBorders>')

    def cell(width: int, right_margin: int, run: str) -> str:
        return (f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{width}"/>'
                f'{no_border}<w:tcMar>'
                '<w:top w:type="dxa" w:w="40"/><w:left w:type="dxa" w:w="0"/>'
                '<w:bottom w:type="dxa" w:w="40"/>'
                f'<w:right w:type="dxa" w:w="{right_margin}"/>'
                f'</w:tcMar></w:tcPr><w:p>{run}</w:p></w:tc>')

    rows = "".join(
        f'<w:tr>{cell(2600, 100, _run(lbl, "meta_label"))}'
        f'{cell(7038, 0, _run(PLACEHOLDER, "meta_value"))}</w:tr>'
        for lbl in labels
    )
    return (f'<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="{TABLE_WIDTH}"/>'
            '<w:tblBorders>'
            + "".join(f'<w:{s} w:val="single" w:color="auto" w:sz="4"/>'
                      for s in ("top", "left", "bottom", "right",
                                "insideH", "insideV"))
            + f'</w:tblBorders></w:tblPr><w:tblGrid>{grid}</w:tblGrid>'
            + rows + '</w:tbl>')


def note(text: str) -> str:
    """Losse cursieve notitie, bijvoorbeeld de 'schrijf niet meer dan nodig'-regel."""
    return _p(_run(text, "guide"), '<w:spacing w:after="200" w:before="120"/>')


def heading(text: str) -> str:
    return _p(_run(text, "h"), '<w:spacing w:after="20" w:before="260"/>')


def guidance(text: str) -> str:
    return _p(_run(text, "guide"), '<w:spacing w:after="60"/>')


def placeholder(count: int = 1) -> str:
    return "".join(_p(_run(PLACEHOLDER, "ph"), '<w:spacing w:after="40"/>')
                   for _ in range(count))


def content_table(headers: list[str], rows: int = 3) -> str:
    """Inhoudelijke tabel met gearceerde, herhalende kopregel."""
    n = len(headers)
    widths = [TABLE_WIDTH // n] * n
    widths[-1] += TABLE_WIDTH - sum(widths)
    borders = ('<w:tcBorders>'
               + "".join(f'<w:{s} w:val="single" w:color="{RULE}" w:sz="2"/>'
                         for s in ("top", "left", "bottom", "right"))
               + '</w:tcBorders>')
    margins = ('<w:tcMar><w:top w:type="dxa" w:w="60"/>'
               '<w:left w:type="dxa" w:w="100"/>'
               '<w:bottom w:type="dxa" w:w="60"/>'
               '<w:right w:type="dxa" w:w="100"/></w:tcMar>')

    def cell(width: int, run: str, shaded: bool) -> str:
        shd = (f'<w:shd w:fill="{SHADE}" w:color="auto" w:val="clear"/>'
               if shaded else "")
        return (f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{width}"/>'
                f'{borders}{shd}{margins}</w:tcPr><w:p>{run}</w:p></w:tc>')

    head = ('<w:tr><w:trPr><w:tblHeader/></w:trPr>'
            + "".join(cell(w, _run(h, "th"), True)
                      for w, h in zip(widths, headers))
            + '</w:tr>')
    body = "".join(
        '<w:tr>' + "".join(cell(w, _run("", "td"), False) for w in widths)
        + '</w:tr>' for _ in range(rows)
    )
    return (f'<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="{TABLE_WIDTH}"/>'
            '<w:tblBorders>'
            + "".join(f'<w:{s} w:val="single" w:color="auto" w:sz="4"/>'
                      for s in ("top", "left", "bottom", "right",
                                "insideH", "insideV"))
            + '</w:tblBorders></w:tblPr><w:tblGrid>'
            + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
            + '</w:tblGrid>' + head + body + '</w:tbl>')


def checklist(items: list[str]) -> str:
    ppr = ('<w:pStyle w:val="ListParagraph"/><w:numPr>'
           '<w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr>'
           '<w:spacing w:after="20"/>')
    return "".join(_p(_run(i, "li"), ppr) for i in items)


def subheading(text: str) -> str:
    """Subkop binnen een sectie, voor een herhaalbaar blok."""
    return _p(_run(text, "sub"), '<w:spacing w:after="20" w:before="200"/>')


def field(label: str, guide: str) -> str:
    """Veldlabel met invulinstructie op één regel, gevolgd door een plaatshouder.

    Vervangt de kolom van een tabel op plekken waar de inhoud uit zinnen
    bestaat in plaats van uit losse termen.
    """
    line = _p(
        _run(f"{label}  ", "field") + _run(guide, "guide"),
        '<w:spacing w:after="20" w:before="80"/>',
    )
    return line + placeholder()


def repeat_note(text: str) -> str:
    """Regel die aangeeft dat het voorgaande blok per item herhaald wordt."""
    return _p(_run(text, "guide"), '<w:spacing w:after="40" w:before="140"/>')


def provenance_table(created_by: list[str], read_by: list[str],
                     updated_by: list[str]) -> str:
    """Herkomst en gebruik: uit welke activiteiten dit werkproduct komt en gaat.

    Tegenhanger van de Output/Input-tabel die elk TOGAF-deliverable opent.
    De inhoud komt uit de RDF en wordt niet met de hand onderhouden.
    """
    def joined(names: list[str]) -> str:
        return ", ".join(sorted(set(names))) if names else "—"

    rows = [
        ("Ontstaat bij", joined(created_by)),
        ("Wordt bijgewerkt door", joined(updated_by)),
        ("Wordt gelezen door", joined(read_by)),
    ]
    borders = ('<w:tcBorders>'
               + "".join(f'<w:{s} w:val="single" w:color="{RULE}" w:sz="2"/>'
                         for s in ("top", "left", "bottom", "right"))
               + '</w:tcBorders>')
    margins = ('<w:tcMar><w:top w:type="dxa" w:w="60"/>'
               '<w:left w:type="dxa" w:w="100"/>'
               '<w:bottom w:type="dxa" w:w="60"/>'
               '<w:right w:type="dxa" w:w="100"/></w:tcMar>')

    def cell(width: int, run: str, shaded: bool) -> str:
        shd = (f'<w:shd w:fill="{SHADE}" w:color="auto" w:val="clear"/>'
               if shaded else "")
        return (f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{width}"/>'
                f'{borders}{shd}{margins}</w:tcPr><w:p>{run}</w:p></w:tc>')

    body = "".join(
        f'<w:tr>{cell(2600, _run(lbl, "th"), True)}'
        f'{cell(7038, _run(val, "td"), False)}</w:tr>'
        for lbl, val in rows
    )
    return (f'<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="{TABLE_WIDTH}"/>'
            '<w:tblBorders>'
            + "".join(f'<w:{s} w:val="single" w:color="auto" w:sz="4"/>'
                      for s in ("top", "left", "bottom", "right",
                                "insideH", "insideV"))
            + '</w:tblBorders></w:tblPr><w:tblGrid>'
            '<w:gridCol w:w="2600"/><w:gridCol w:w="7038"/></w:tblGrid>'
            + body + '</w:tbl>')


# --- verpakking -----------------------------------------------------------

SECT_PR = (
    '<w:sectPr><w:footerReference w:type="default" r:id="rId7"/>'
    '<w:pgSz w:w="11906" w:h="16838" w:orient="portrait"/>'
    '<w:pgMar w:top="1133" w:right="1133" w:bottom="1020" w:left="1133" '
    'w:header="708" w:footer="708" w:gutter="0"/>'
    '<w:pgNumType/><w:docGrid w:linePitch="360"/></w:sectPr>'
)


def build(source: pathlib.Path, target: pathlib.Path,
          body_xml: str, footer_label: str) -> None:
    """Schrijf een nieuw .docx door document.xml en footer1.xml te vervangen.

    Alle overige onderdelen (styles, numbering, settings, relaties) worden
    ongewijzigd uit het bronbestand overgenomen, zodat de opmaak identiek blijft.
    """
    with zipfile.ZipFile(source) as zin:
        parts = {n: zin.read(n) for n in zin.namelist()}

    doc = parts["word/document.xml"].decode("utf-8")
    head = doc[: doc.index("<w:body>") + len("<w:body>")]
    parts["word/document.xml"] = (head + body_xml + SECT_PR
                                  + "</w:body></w:document>").encode("utf-8")

    ftr = parts["word/footer1.xml"].decode("utf-8")
    old = ftr[ftr.index("<w:t xml:space=\"preserve\">") + 26:]
    old_label = old[: old.index("</w:t>")]
    parts["word/footer1.xml"] = ftr.replace(
        old_label, escape(f"{footer_label}  ·  sjabloon  ·  ")
    ).encode("utf-8")

    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in parts.items():
            zout.writestr(name, data)
