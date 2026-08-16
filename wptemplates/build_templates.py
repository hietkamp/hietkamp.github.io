"""Genereert de werkproduct-sjablonen op basis van de RDF, TOGAF en RUP.

Bron van waarheid is `essence/method/**`: titel, practice, korte omschrijving en
de herkomst-en-gebruikrelaties komen daaruit. Werkproducten die niet in de RDF
staan, krijgen geen sjabloon.

Structuur overgenomen uit de TOGAF-deliverables
-----------------------------------------------
Elk TOGAF-deliverable opent op dezelfde manier: documentbeheer, het doel van het
document, en een Output/Input-tabel die laat zien uit welk proces het stuk komt
en waar het weer wordt gebruikt. Pas daarna volgt de inhoud, in genummerde
secties met lopende tekst.

Wat hier is overgenomen:

1.  Vaste opening: metadata, "niet meer dan nodig", en **Herkomst en gebruik** —
    de Nederlandse tegenhanger van Output/Input, gevuld vanuit de RDF.
2.  Narratief boven invulvelden. Tabellen blijven gereserveerd voor echte
    registers: herhalende rijen waarin elke rij hetzelfde soort ding beschrijft.
    Waar de inhoud uit zinnen bestaat — een rationale, een implicatie, de
    onderbouwing van een volgorde — komt een herhaalbaar blok met veldlabels in
    plaats van een kolom.
3.  Doelstellingen en criteria zijn toetsbaar: er staat bij waaraan je afleest
    dat iets gehaald is.
4.  Verschil vóór ontwerp: eerst wat er verandert, dan pas de invulling.
5.  Restrisico expliciet: wat na beheersing overblijft, wordt benoemd en aanvaard.
6.  Formele vaststelling sluit het document af.
7.  Niet meer dan nodig: secties die voor dit geval niets toevoegen vervallen.

Hoofdstukindeling overgenomen uit de RUP-templates
--------------------------------------------------
De RUP-sjablonen (IBM Rational, 2003; zie `RUP-MAPPING.md` in de projectroot)
zijn per werkproduct langsgelopen. Overgenomen is de *hoofdstukindeling* en de
*invulinstructie*; de inhoud is herschreven naar de context van de practice
waarin het werkproduct thuishoort. Waar RUP over UML, code en projectfasen
spreekt, staat hier de architectuur- of requirementscontext van deze werkwijze.

Per werkproduct de gebruikte RUP-bron:

| Werkproduct                | RUP-template                                    |
| -------------------------- | ----------------------------------------------- |
| Architectuuropdracht       | Software Development Plan §2–§4; Vision §1.2    |
| Architectuurvisie          | Vision §2, §3.5, §3.7, §3.8, §7, §8             |
| Architectuurprincipes      | Design Guidelines §2–§4; Programming Gl. §12    |
| Architectuur werkafspraken | Development Case §2.3, §2.5, §4                 |
| Paved road                 | Design Guidelines §5; Programming Gl. §7–§11    |
| Architectuurmodel          | Software Architecture Document §2–§11           |
| Architectuurbeslissingen   | SAD §3, §11; Business Architecture Doc. §11     |
| Migratiescenario           | Deployment Plan §3–§5                           |
| Reviewresultaten           | Iteration Assessment §7; CM Plan §3.1.1, §3.3.2 |
| Use-casemodel              | Use-Case Model Survey; Vision §4.1, bijlage A   |
| Use-casespecificatie       | Use-Case Specification §1–§10                   |
| Aanvullende specificaties  | Supplementary Specification §2–§13              |

Bewust *niet* overgenomen uit RUP
--------------------------------
Elke RUP-template opent met dezelfde blokken voorwerk: een Revision History en
een §1 Introduction met Purpose, Scope, Definitions, References en Overview.
Dat past bij documenten die als contractstuk circuleren, niet bij deze
werkwijze. Wat is weggelaten en waarom:

*   **Revision History** — de versiehistorie voegt niets toe boven het
    versienummer zelf, mits dat nummer betekenis heeft. Zie hieronder.
*   **References** — het aparte verwijzingenregister liep in de praktijk leeg
    of dubbelde met de verwijzingen in de tekst; verwijzen gebeurt op de plek
    waar het ertoe doet.
*   **Status, Eigenaar en Opgesteld door** in het metadatablok. Eigenaarschap
    staat in de RDF en dus in "Herkomst en gebruik"; de status zit in het
    versienummer.

De status wordt uitgedrukt met **semver** (major.minor.patch): 0.y.z is
concept, 1.0.0 is vastgesteld, de major verspringt bij een wijziging die een
eerder besluit raakt. Eén veld in plaats van twee, en het versienummer alleen
vertelt al of er iets is vastgesteld.

Eenmalige steiger, geen buildstap
---------------------------------
Dit script zet een sjabloon néér; daarna is het .docx-bestand van jou. Bestaande
bestanden worden nooit overschreven — handmatige aanpassingen blijven dus staan,
ook als je het script opnieuw draait. `python3 build.py` roept dit script niet
aan; die kopieert de sjablonen alleen naar `docs/downloads/`.

Wil je een sjabloon toch terugzetten naar de gegenereerde versie, dan moet dat
expliciet met --force. Wat je met de hand had aangepast, ben je dan kwijt.

Gebruik
-------
    python3 build_templates.py                    # alleen ontbrekende sjablonen
    python3 build_templates.py paved-road         # alleen dit werkproduct, als het ontbreekt
    python3 build_templates.py --force paved-road # overschrijf dit werkproduct
"""

from __future__ import annotations

import pathlib
import sys

import _method
from _builder import (build, checklist, content_table, guidance, heading,
                      meta_table, note, placeholder, provenance_table,
                      repeat_note, subheading, title_block)
from _builder import field as fld

HERE = pathlib.Path(__file__).parent
STYLE = HERE / "_style.docx"

JUST_ENOUGH = ("Beschrijf niet meer dan nodig is voor het doel van dit stuk. "
               "Laat een sectie leeg of verwijder haar wanneer ze in dit geval "
               "niets toevoegt.")

# Het versienummer draagt de status; een apart statusveld en een
# versiehistorietabel voegen daar niets aan toe. De opbouw volgt semver:
# major.minor.patch, met 0.y.z voor alles wat nog niet is vastgesteld.
SEMVER = ("Het versienummer geeft de status weer, volgens major.minor.patch. "
          "0.y.z is een concept dat nog niet is vastgesteld; 1.0.0 is de "
          "eerste vastgestelde versie. Verhoog de patch bij een tekstuele "
          "correctie, de minor bij een aanvulling die verenigbaar is met de "
          "vorige versie, en de major bij een wijziging die een eerder besluit "
          "raakt en dus opnieuw moet worden vastgesteld.")

META = ["Project", "Versie", "Datum"]


def preamble(wp: _method.WorkProduct, meta: list[str] = None) -> str:
    """Vaste opening: titel, metadata en herkomst uit de RDF."""
    return (
        title_block(wp.name, wp.practice, wp.brief)
        + meta_table(meta or META)
        + note(SEMVER)
        + note(JUST_ENOUGH)
        + heading("Herkomst en gebruik")
        + guidance("Waar dit werkproduct in de werkwijze vandaan komt en wie "
                   "het verderop gebruikt. Deze tabel komt uit de methode zelf "
                   "en hoeft niet te worden ingevuld.")
        + provenance_table(wp.created_by, wp.read_by, wp.updated_by)
    )


# ==========================================================================
# Architectuuropdracht
# TOGAF: Statement of Architecture Work (fase A)
# RUP:   Software Development Plan §2.2, §2.4, §3.2, §4.1, §4.6
# ==========================================================================
# TOGAF legt vóór aanvang vast wat de opdracht is, wat erbuiten valt, wie
# waarover beslist en waarop wordt afgerekend.
#
# RUP vult dat aan op vier punten die in de TOGAF-deliverable ontbreken: de
# aannames waarop de opdracht rust (§2.2), de externe partijen waar het werk van
# afhangt (§3.2), het moment waarop opnieuw wordt geraamd (§4.1) en de ordelijke
# afronding met archivering (§4.6). Alle vier komen ze uit de projectpraktijk en
# zijn precies de punten waarop een architectuuropdracht stilvalt.

def architectuuropdracht(wp):
    return (
        preamble(wp)
        + heading("Aanleiding en doel")
        + guidance("Welke vraag of welk knelpunt aanleiding geeft tot deze "
                   "architectuurinspanning, en wat ze moet opleveren.")
        + placeholder()

        + heading("Opdracht en scope")
        + guidance("Wat er binnen deze opdracht wordt uitgewerkt: welke "
                   "domeinen, organisatieonderdelen en systemen.")
        + placeholder()

        + heading("Wat buiten de opdracht valt")
        + guidance("Wat uitdrukkelijk niet wordt uitgewerkt. Even belangrijk "
                   "als de scope zelf — hier wordt later naar verwezen.")
        + placeholder()

        + heading("Aannames en beperkingen")
        + guidance("Waarop deze opdracht rust en wat haar inperkt: budget, "
                   "bezetting, doorlooptijd, beschikbaarheid van mensen, "
                   "bestaande contracten. Noteer per aanname wanneer ze "
                   "getoetst wordt — een aanname die niemand nagaat, is een "
                   "risico.")
        + placeholder()

        + heading("Toepasselijke architectuurprincipes")
        + guidance("Welke principes gelden binnen deze opdracht. Verwijs naar "
                   "de architectuurprincipes; herhaal ze hier niet.")
        + placeholder()

        + heading("Beslissingsbevoegdheden")
        + guidance("Wie binnen dit initiatief welke beslissing mag nemen, en "
                   "wanneer een keuze naar het Architectuurforum gaat.")
        + content_table(["Soort beslissing", "Wie beslist",
                         "Escalatie naar"], rows=4)

        + heading("Raakvlakken met andere partijen")
        + guidance("De partijen buiten het initiatief waar dit werk van "
                   "afhangt: systeemeigenaren, leveranciers, beheerorganisatie, "
                   "toezichthouders. Noem per partij wat er van hen nodig is, "
                   "wanneer, en wie het aanspreekpunt is.")
        + content_table(["Partij", "Wat er van hen nodig is", "Wanneer",
                         "Aanspreekpunt"], rows=4)

        + heading("Op te leveren werkproducten")
        + guidance("Welke werkproducten deze opdracht oplevert, wanneer ze "
                   "gereed zijn en wie ervoor tekent.")
        + content_table(["Werkproduct", "Gereed", "Eigenaar"], rows=4)

        + heading("Acceptatiecriteria")
        + guidance("Waaraan de opdrachtgever afleest dat de opdracht is "
                   "afgerond. Formuleer zo dat er achteraf geen discussie over "
                   "kan ontstaan.")
        + placeholder()

        + heading("Aanpak en doorlooptijd")
        + guidance("Op hoofdlijnen: welke stappen, welke doorlooptijd, welke "
                   "betrokkenheid van anderen nodig is. Benoem waarop de "
                   "inschatting rust en op welke momenten opnieuw wordt "
                   "geraamd — een raming die nooit wordt herzien, wordt op den "
                   "duur een fictie.")
        + placeholder()

        + heading("Wijziging en herijking van de opdracht")
        + guidance("Wat er gebeurt als de scope tijdens de uitvoering "
                   "verandert: wie meldt, wie besluit, wat wordt vastgelegd. "
                   "Benoem ook de omstandigheden die een tussentijdse "
                   "herziening van de opdracht zelf afdwingen.")
        + placeholder()

        + heading("Afronding en overdracht")
        + guidance("Hoe de opdracht ordelijk eindigt: wie decharge verleent, "
                   "wat er wordt overgedragen aan beheer, en waar de "
                   "opgeleverde werkproducten in de architectuurrepository "
                   "terechtkomen.")
        + placeholder()

        + heading("Vaststelling")
        + guidance("Wie geeft de opdracht, wanneer, en waar is dat vastgelegd. "
                   "Vanaf dat moment ligt de scope vast.")
        + placeholder()

        + heading("Gereed wanneer")
        + checklist([
            "De opdrachtgever heeft de opdracht bevestigd.",
            "Scope en uitsluitingen laten geen ruimte voor discussie.",
            "Elke aanname heeft een moment waarop ze getoetst wordt.",
            "De toepasselijke principes zijn benoemd.",
            "Van elke soort beslissing is bekend wie hem neemt.",
            "Van elke externe afhankelijkheid is een aanspreekpunt bekend.",
            "De acceptatiecriteria zijn toetsbaar geformuleerd.",
        ])
    )


# ==========================================================================
# Architectuurvisie
# TOGAF: Architecture Vision (fase A)
# RUP:   Vision §2.2, §3.5, §3.7, §3.8, §7, §8
# ==========================================================================
# RUP's Vision is productgericht, maar vier van zijn secties zijn rechtstreeks
# bruikbaar en scherper dan wat de TOGAF-vorm afdwingt:
#
# §2.2  Problem Statement — een vaste vierregelige vorm die het probleem, de
#       getroffenen, het gevolg en de gewenste uitkomst uit elkaar trekt. Dat
#       dwingt af dat er werkelijk een probleem staat en niet alvast een
#       oplossing.
# §3.5  Stakeholder Profiles — vraagt per belanghebbende naar zijn eigen
#       succescriterium, niet alleen naar zijn zorg.
# §3.7  Key Stakeholder Needs — zet naast elke behoefte hoe het nu gaat.
# §3.8  Alternatives and Competition — dwingt de status quo als volwaardig
#       alternatief op tafel.
# §7    Quality Ranges — marges voor prestaties, robuustheid en bruikbaarheid
#       die niet uit de functionaliteit volgen. Dit is het aanknopingspunt voor
#       de architectuurbepalende eisen.
# §8    Precedence and Priority — de doelstellingen zijn niet gelijkwaardig.

def architectuurvisie(wp):
    return (
        preamble(wp, ["Project", "Opdrachtgever", "Versie", "Datum"])
        + heading("Samenvatting")
        + guidance("De richting in maximaal tien regels, leesbaar voor wie de "
                   "rest niet leest. Schrijf deze sectie als laatste.")
        + placeholder()

        + heading("Aanleiding")
        + guidance("Welke gebeurtenis, doelstelling of ontwikkeling dwingt tot "
                   "verandering, en waarom nu.")
        + placeholder()

        + heading("Probleemstelling")
        + guidance("Vul de vier regels hieronder in. Door probleem, "
                   "getroffenen, gevolg en gewenste uitkomst uit elkaar te "
                   "trekken blijft er een probleem staan en geen verkapte "
                   "oplossing.")
        + fld("Het probleem van",
              "het knelpunt zelf, in één zin en zonder oplossingsrichting.")
        + fld("treft",
              "wie er last van heeft: welke afdelingen, teams, ketenpartners "
              "of eindgebruikers.")
        + fld("waarvan het gevolg is",
              "wat het kost of onmogelijk maakt — liefst met een getal.")
        + fld("een geslaagde aanpak zou",
              "de uitkomst waaraan te zien is dat het probleem weg is.")

        + heading("Doelstellingen")
        + guidance("Wat de verandering moet opleveren, in termen die achteraf "
                   "te toetsen zijn. Noem per doelstelling waaraan je afleest "
                   "dat ze gehaald is, en wanneer dat wordt vastgesteld. Zet ze "
                   "in volgorde van gewicht: bij schaarste wordt de onderste "
                   "als eerste losgelaten.")
        + placeholder()

        + heading("Afbakening")
        + guidance("Welke domeinen, organisatieonderdelen en systemen "
                   "hierbinnen vallen — en welke uitdrukkelijk niet. De "
                   "uitsluitingen zijn even belangrijk als wat er wel in zit.")
        + placeholder()

        + heading("Belanghebbenden en hun zorgen")
        + guidance("Alleen partijen die de vorm van de oplossing beïnvloeden "
                   "of erdoor geraakt worden. De zorg bepaalt wat er verderop "
                   "beschreven moet worden; invloed bepaalt hoeveel gewicht "
                   "die zorg krijgt. Vraag per partij ook wanneer het voor hém "
                   "geslaagd is — dat antwoord wijkt vaak af van het "
                   "projectdoel.")
        + content_table(["Belanghebbende", "Belang", "Zorg",
                         "Geslaagd wanneer", "Invloed"], rows=4)

        + heading("Behoeften en de huidige gang van zaken")
        + guidance("Per behoefte hoe het nu wordt opgelost. Zonder dat beeld "
                   "is niet te beoordelen of de verandering werkelijk iets "
                   "verbetert, en wordt bestaand werkend gedrag onbedoeld "
                   "weggeautomatiseerd.")
        + content_table(["Behoefte", "Gewicht", "Hoe het nu gaat",
                         "Wat er nodig is"], rows=4)

        + heading("Beoogde situatie")
        + guidance("Hoe het landschap eruitziet als de verandering is "
                   "geslaagd. Beschrijf gedrag en samenhang op hoofdlijnen — "
                   "nog geen ontwerp.")
        + placeholder(2)

        + heading("Alternatieven")
        + guidance("De richtingen die zijn overwogen en waarom ze afvallen. "
                   "Neem de status quo altijd op als alternatief: niets doen "
                   "is een keuze met eigen kosten, en die moeten hier staan.")
        + content_table(["Alternatief", "Pleit voor", "Pleit tegen",
                         "Waarom afgevallen"], rows=3)

        + heading("Kwaliteitsmarges")
        + guidance("De marges voor prestaties, beschikbaarheid, robuustheid, "
                   "beveiliging en bruikbaarheid die niet uit de "
                   "functionaliteit volgen. Geef per kenmerk de ondergrens "
                   "waaronder het niet acceptabel is en de waarde die wordt "
                   "nagestreefd; hieruit komen de architectuurbepalende eisen "
                   "voort.")
        + content_table(["Kenmerk", "Ondergrens", "Streefwaarde",
                         "Waarom deze grens"], rows=4)

        + heading("Uitgangspunten voor keuzes")
        + guidance("Welke principes en uitsluitingscriteria gelden bij het "
                   "kiezen tussen opties. Verwijs naar de "
                   "architectuurprincipes; herhaal ze hier niet.")
        + placeholder()

        + heading("Verschil met de huidige situatie")
        + guidance("Wat verdwijnt, wat verandert, wat komt erbij. Alleen het "
                   "verschil — de invulling volgt in het architectuurmodel.")
        + placeholder()

        + heading("Randvoorwaarden en aannames")
        + guidance("Wat waar moet zijn wil deze richting houdbaar blijven. "
                   "Benoem aannames die later getoetst worden, en wanneer dat "
                   "gebeurt.")
        + placeholder()

        + heading("Risico's")
        + guidance("Alleen risico's die de richting zelf raken, niet de "
                   "uitvoering. Het restrisico is wat na beheersing overblijft "
                   "en door de opdrachtgever wordt aanvaard.")
        + content_table(["Risico", "Gevolg", "Beheersing", "Restrisico"], rows=3)

        + heading("Vaststelling")
        + guidance("Wie stelt de visie vast, wanneer, en waar is dat besluit "
                   "vastgelegd. Vanaf dat moment is de visie het kompas voor "
                   "alle architectuurkeuzes die volgen.")
        + placeholder()

        + heading("Gereed wanneer")
        + checklist([
            "De opdrachtgever heeft de richting bevestigd.",
            "De probleemstelling bevat een probleem, geen oplossing.",
            "De afbakening laat geen ruimte voor discussie over scope.",
            "Belanghebbenden en hun zorgen zijn benoemd.",
            "Elke doelstelling heeft een criterium waaraan ze te toetsen is.",
            "De doelstellingen staan in volgorde van gewicht.",
            "De status quo is als alternatief afgewogen.",
            "Het restrisico is benoemd en aanvaard.",
            "Het besluit over de richting is vastgelegd in het Architectuurforum.",
        ])
    )


# ==========================================================================
# Architectuurprincipes
# TOGAF: Architecture Principles (voorbereidende fase)
# RUP:   Design Guidelines §2–§4; Programming Guidelines §12
# ==========================================================================
# TOGAF beschrijft een principe in vier vaste delen: naam, stelling, rationale
# en implicaties. Rationale en implicaties zijn alinea's, geen celinhoud — het
# oude viercolomsrooster is daarom vervangen door een herhaalbaar blok per
# principe.
#
# RUP's Design Guidelines voegen twee dingen toe. Ten eerste een indeling: die
# template ordent haar regels per gebied (§2 algemeen, §3 gegevens, §4
# architectuur) in plaats van als één lange lijst — dat maakt een set van tien
# principes doorzoekbaar. Ten tweede vraagt RUP overal naar de herkomst van een
# regel (§1.4): welke norm, wet of doelstelling erachter zit. Een principe
# zonder herkomst is een mening.
#
# Programming Guidelines §12 sluit af met "Annex: Summary of Guidelines; one
# line for each" — die samenvatting in één regel per principe is overgenomen,
# omdat dat het blad is dat mensen daadwerkelijk raadplegen.

def architectuurprincipes(wp):
    return (
        preamble(wp)
        + heading("Reikwijdte")
        + guidance("Voor welke organisatieonderdelen, domeinen en soorten "
                   "keuzes deze principes gelden.")
        + placeholder()

        + heading("Indeling")
        + guidance("In welke gebieden de principes hieronder zijn geordend — "
                   "bijvoorbeeld algemeen, gegevens, integratie, beveiliging, "
                   "infrastructuur. Een geordende set blijft doorzoekbaar; een "
                   "ongeordende lijst wordt na acht principes niet meer "
                   "gelezen.")
        + placeholder()

        + heading("Principes")
        + guidance("Houd de set bewust klein — vijf tot tien — zodat de "
                   "principes te onthouden, toe te passen en te handhaven "
                   "blijven. Herhaal het blok hieronder per principe.")
        + subheading("Principe 1 — [ naam ]")
        + fld("Gebied",
              "onder welk gebied uit de indeling dit principe valt.")
        + fld("Stelling",
              "de regel in één zin, in gebiedende wijs en zonder voorbehoud.")
        + fld("Rationale",
              "waarom dit de gewenste richting is, en wat er misgaat zonder.")
        + fld("Herkomst",
              "waar het principe vandaan komt: een wettelijke verplichting, "
              "een norm, een uitspraak van de directie of een geleerde les. "
              "Zonder herkomst is een principe een mening.")
        + fld("Implicaties",
              "wat dit betekent voor ontwerp- en technologiekeuzes, inclusief "
              "wat er níet meer mag.")
        + repeat_note("Herhaal dit blok per principe.")

        + heading("Toetsing")
        + guidance("Hoe het Architectuurforum een beslissing tegen deze "
                   "principes houdt: wat gaat ongehinderd door, wat krijgt een "
                   "review.")
        + placeholder()

        + heading("Afwijken")
        + guidance("Wat iemand doet die van een principe wil afwijken: wie "
                   "meldt, wie besluit, en hoe de uitzondering wordt "
                   "vastgelegd.")
        + placeholder()

        + heading("Spanning tussen principes")
        + guidance("Welke principes elkaar in de praktijk kunnen bijten, en "
                   "welk principe dan voorgaat.")
        + placeholder()

        + heading("Herziening en supersessie")
        + guidance("Wanneer de set wordt herzien en hoe een nieuwe versie de "
                   "oude zichtbaar vervangt. Een principe dat vaak wordt "
                   "omzeild, wordt aangescherpt of geschrapt.")
        + placeholder()

        + heading("Bijlage: alle principes in één regel")
        + guidance("Eén regel per principe, in de volgorde hierboven. Dit is "
                   "het blad dat in de praktijk wordt geraadpleegd; de "
                   "uitwerking wordt er alleen bij gepakt als er twijfel is.")
        + content_table(["Nr", "Gebied", "Principe in één regel"], rows=6)

        + heading("Gereed wanneer")
        + checklist([
            "Elk principe heeft een stelling, een rationale en implicaties.",
            "Van elk principe is de herkomst bekend.",
            "De set is beperkt gebleven tot wat te onthouden is.",
            "Bij tegenstrijdige principes is bekend welke voorgaat.",
            "De afwijkroute is beschreven.",
            "Vervangen principes zijn zichtbaar als vervangen gemarkeerd.",
            "De samenvatting in één regel is bijgewerkt.",
        ])
    )


# ==========================================================================
# Architectuur werkafspraken
# TOGAF: Organizational Model for Enterprise Architecture (voorbereidende fase)
#        + Implementation Governance Model (fase F)
# RUP:   Development Case §2.3.1, §2.3.2, §2.3.3, §2.5, §4
# ==========================================================================
# Van alle RUP-templates sluit de Development Case het dichtst aan op een van
# onze werkproducten: hij legt vast welk stuk in welke situatie verplicht is,
# hoe zwaar het wordt gereviewd, en welke rol in de methode bij welke functie in
# de organisatie hoort. Dat is precies wat werkafspraken moeten regelen.
#
# Rechtstreeks overgenomen:
#
# §2.3.2  de artefactentabel met per werkproduct een verplichtingsklasse
#         (must / should / could / won't) en een reviewniveau;
# §2.5    de vier reviewniveaus: formeel-extern, formeel-intern, informeel,
#         geen — met de eis dat per niveau vastligt wat het inhoudt;
# §2.3.3  "Notes on Artifacts": de lijst van werkproducten die bewust *niet*
#         worden gebruikt, mét reden. Zonder die lijst blijft een overgeslagen
#         werkproduct een omissie in plaats van een besluit;
# §2.3.1  "Workflow": welke activiteiten zijn toegevoegd of weggelaten ten
#         opzichte van de standaardwerkwijze;
# §4      "Roles": de mapping van methoderollen op functies in de organisatie,
#         met RUP's eigen waarschuwing dat rollen geen functies zijn.

def architectuur_werkafspraken(wp):
    return (
        preamble(wp)
        + heading("Reikwijdte")
        + guidance("Voor welke teams, domeinen en soorten beslissingen deze "
                   "afspraken gelden.")
        + placeholder()

        + heading("Afwijkingen op de standaardwerkwijze")
        + guidance("Welke activiteiten uit de werkwijze hier zijn toegevoegd, "
                   "samengevoegd of weggelaten, en waarom. Wat hier niet staat, "
                   "geldt zoals de methode het beschrijft.")
        + placeholder()

        + heading("Beslissingsbevoegdheid en escalatiegrens")
        + guidance("De grens tussen wat een team zelfstandig mag beslissen en "
                   "wat naar het Architectuurforum gaat. Beschrijf de grens zo "
                   "scherp dat een team hem zelf kan toepassen.")
        + content_table(["Soort beslissing", "Team beslist zelf",
                         "Naar het forum wanneer"], rows=4)

        + heading("Escalatieroute")
        + guidance("Wat er gebeurt als een keuze buiten de bevoegdheid valt: "
                   "wie meldt, wie beslist, binnen welke termijn, en wat er "
                   "gebeurt als die termijn niet wordt gehaald.")
        + placeholder()

        + heading("Reviewniveaus")
        + guidance("Wat de gebruikte niveaus hier betekenen: wie er aan tafel "
                   "zit, hoeveel doorlooptijd het kost en wat het oplevert. "
                   "Gebruik vier niveaus — formeel met externen, formeel "
                   "intern, informeel, en geen review — en beschrijf ze zo dat "
                   "een team vooraf weet waar het aan toe is.")
        + content_table(["Niveau", "Wie beoordeelt", "Doorlooptijd",
                         "Uitkomst"], rows=4)

        + heading("Werkproducten en hun gebruik")
        + guidance("Per werkproduct of het verplicht is, hoe zwaar het wordt "
                   "beoordeeld en welk sjabloon erbij hoort. Gebruik voor de "
                   "verplichting vier klassen: verplicht, verwacht, mag, en "
                   "niet. Zo weet een team zonder te vragen wat er van hem "
                   "wordt verlangd.")
        + content_table(["Werkproduct", "Verplichting", "Reviewniveau",
                         "Sjabloon of hulpmiddel"], rows=6)

        + heading("Werkproducten die we bewust niet gebruiken")
        + guidance("Wat uit de werkwijze hier niet wordt opgeleverd, met de "
                   "reden erbij. Zonder deze lijst blijft een overgeslagen "
                   "werkproduct een omissie; mét deze lijst is het een besluit "
                   "waarop iemand aanspreekbaar is.")
        + content_table(["Werkproduct", "Besluit", "Reden"], rows=3)

        + heading("Rollen en wie ze vervult")
        + guidance("Welke functie in de organisatie welke rol uit de werkwijze "
                   "vervult. Een rol is geen functie: één persoon kan meerdere "
                   "rollen dragen en één rol kan over meerdere mensen verdeeld "
                   "zijn. Juist daarom moet het hier staan.")
        + content_table(["Rol in de werkwijze", "Functie", "Wie",
                         "Vervanger"], rows=4)

        + heading("Cadans van het Architectuurforum")
        + guidance("Hoe vaak het forum bijeenkomt, wie er zitting in heeft, en "
                   "wanneer er tussentijds kan worden besloten.")
        + placeholder()

        + heading("Een onderwerp aanmelden")
        + guidance("De lichte route om iets op de agenda te krijgen: waar, met "
                   "welke informatie, en hoe lang van tevoren. Houd de drempel "
                   "laag.")
        + placeholder()

        + heading("Objectives voor de governance zelf")
        + guidance("Waaraan de governance zich later laat afrekenen — "
                   "bijvoorbeeld dat conforme beslissingen geen vertraging "
                   "ondervinden, of dat escalaties binnen een vaste termijn "
                   "zijn afgehandeld. Toets werking governance meet hierop.")
        + content_table(["Objective", "Waaraan af te lezen", "Norm"], rows=4)

        + heading("Wat bewust niet wordt getoetst")
        + guidance("Waar de governance zich buiten houdt. Dit voorkomt dat het "
                   "forum volloopt met keuzes die er niet thuishoren.")
        + placeholder()

        + heading("Herziening en supersessie")
        + guidance("Wanneer de afspraken worden herzien en hoe een nieuwe "
                   "versie de oude zichtbaar vervangt.")
        + placeholder()

        + heading("Gereed wanneer")
        + checklist([
            "Een team kan zelf bepalen of een beslissing naar het forum moet.",
            "Van elk werkproduct is bekend of het verplicht is en hoe zwaar "
            "het wordt beoordeeld.",
            "Wat bewust niet wordt opgeleverd, staat met reden vastgelegd.",
            "Elk reviewniveau heeft een doorlooptijd.",
            "Van elke rol is bekend wie hem vervult en wie invalt.",
            "De escalatieroute heeft een termijn.",
            "De cadans en de aanmeldroute liggen vast.",
            "Elke objective heeft een norm die te meten is.",
            "Vastgelegd is waar de governance zich buiten houdt.",
        ])
    )


# ==========================================================================
# Paved road
# TOGAF: Architecture Building Blocks (fase F) + Solution Building Blocks (G)
# RUP:   Design Guidelines §5; Programming Guidelines §7–§11
# ==========================================================================
# TOGAF levert de catalogusvorm: per bouwsteen de functie, de eigenschappen, de
# koppelvlakken en de afhankelijkheden.
#
# RUP levert wat een catalogus pas bruikbaar maakt. Design Guidelines §5
# ("Mechanism Guidelines") eist dat er voor elk aangeboden mechanisme een
# gebruikershandleiding is: wat het koppelvlak is en hoe je het gebruikt. Een
# paved road zonder die uitwerking is een lijst met merknamen — teams komen er
# niet mee vooruit en gaan alsnog off-road.
#
# Programming Guidelines §7–§11 geven de terugkerende onderwerpen die een route
# hoort af te dekken: foutafhandeling, geheugen- en resourcebeheer,
# overdraagbaarheid en hergebruik. Vertaald naar deze context zijn dat de zaken
# die de route standaard al regelt, zodat een team ze niet zelf hoeft te
# bedenken.

def paved_road(wp):
    return (
        preamble(wp)
        + heading("Reikwijdte")
        + guidance("Welke architectuurlagen en domeinen deze route dekt, en "
                   "voor welke teams ze bedoeld is.")
        + placeholder()

        + heading("On-road en off-road")
        + guidance("Wat het betekent om de route te volgen: on-road is gewoon "
                   "gebruiken zonder review, off-road vraagt een "
                   "architectuurbeslissing vóór gebruik.")
        + placeholder()

        + heading("Catalogus")
        + guidance("Per item het goedgekeurde product, patroon of protocol, "
                   "met de voorwaarden waaronder het geldt. De onderbouwing "
                   "staat niet hier maar in de bijbehorende "
                   "architectuurbeslissing.")
        + content_table(["Item", "Laag", "Status", "Voorwaarden en beperkingen",
                         "Onderhouden door"], rows=5)

        + heading("Statussen")
        + guidance("Wat de gebruikte statussen betekenen en wat een team eraan "
                   "heeft — bijvoorbeeld hoeveel ondersteuning erbij hoort en "
                   "hoe stabiel een item is.")
        + placeholder()

        + heading("Uitwerking per item")
        + guidance("Een catalogusregel vertelt een team nog niet hoe het iets "
                   "gebruikt. Werk elk item hieronder uit tot het punt waarop "
                   "iemand er zonder overleg mee aan de slag kan; dat is het "
                   "verschil tussen een route en een lijst.")
        + subheading("Item 1 — [ naam ]")
        + fld("Waarvoor bedoeld",
              "welk probleem dit item oplost, en in welke situaties het de "
              "aangewezen keuze is.")
        + fld("Hoe te gebruiken",
              "de kortste weg naar werkend gebruik: waar het vandaan komt, hoe "
              "het wordt aangesloten, waar het voorbeeld staat.")
        + fld("Standaardinstellingen",
              "de instellingen die al goedgekeurd zijn, zodat een team ze niet "
              "zelf hoeft af te leiden.")
        + fld("Wat het niet dekt",
              "de gevallen waarvoor dit item níet bedoeld is. Zonder deze "
              "grens wordt het item vroeg of laat verkeerd ingezet.")
        + fld("Aanspreekpunt",
              "wie helpt als het niet lukt, en waar de vragen binnenkomen.")
        + repeat_note("Herhaal dit blok per item dat toelichting nodig heeft.")

        + heading("Wat de route standaard al regelt")
        + guidance("De terugkerende onderwerpen waarvoor de route een "
                   "vastgestelde invulling kent — foutafhandeling en "
                   "herstelgedrag, logging en herleidbaarheid, geheimen en "
                   "sleutels, overdraagbaarheid tussen omgevingen, hergebruik. "
                   "Wat hier staat, hoeft een team niet zelf te bedenken en "
                   "wordt ook niet opnieuw beoordeeld.")
        + content_table(["Onderwerp", "Wat de route regelt", "Waar het staat"],
                        rows=5)

        + heading("Ondersteuning")
        + guidance("Wat een team krijgt bij het volgen van de route: "
                   "voorbeelden, standaardinstellingen, sjablonen, "
                   "aanspreekpunt.")
        + placeholder()

        + heading("Afwijken van de route")
        + guidance("De off-road-procedure: wie meldt, wat er wordt vastgelegd, "
                   "wie besluit, en hoe lang de afwijking geldt.")
        + placeholder()

        + heading("Wat hiermee aan toetsing vervalt")
        + guidance("Welke reviews een team niet meer hoeft te doorlopen zolang "
                   "het on-road blijft. Dit is de winst van de route; maak "
                   "hem expliciet.")
        + placeholder()

        + heading("Onderhoud en levenscyclus")
        + guidance("Wie de catalogus bijhoudt, hoe vaak, en hoe een item "
                   "wordt toegevoegd, van status verandert of verdwijnt.")
        + placeholder()

        + heading("Gereed wanneer")
        + checklist([
            "Elk item heeft een status en een eigenaar.",
            "Bij elk item staan de voorwaarden en beperkingen.",
            "Van elk item is bekend waarvoor het níet bedoeld is.",
            "Een team kan een item gebruiken zonder eerst te overleggen.",
            "Een team kan zelf bepalen of het on-road of off-road zit.",
            "De off-road-procedure is beschreven.",
            "Vastgelegd is welke toetsing vervalt bij on-road gebruik.",
        ])
    )


# ==========================================================================
# Architectuurmodel
# TOGAF: Architecture Definition Document (fase A t/m D)
# RUP:   Software Architecture Document §2, §3, §4, §7, §9, §10, §11
# ==========================================================================
# Dit is de sterkste overeenkomst van de hele set: de SAD ís het
# architectuurmodel.
#
# De sectievolgorde volgt het C4-model, en wel strikt: per niveau één hoofdstuk
# met daarin zowel het diagram als het register. Eerder stonden diagram en
# register los van elkaar — "Containers" met de tekening, "Bouwstenen" met de
# tabel — terwijl de RDF beide woorden voor hetzelfde gebruikt: "containerniveau
# (de bouwstenen en hun onderlinge gegevensuitwisseling)". Een bouwsteen ís een
# C4-container. Die dubbeling is opgeheven; het woord bouwsteen blijft in de
# lopende tekst staan omdat de RDF het gebruikt, maar als kop en kolomnaam
# staat er nu het C4-begrip. Koppelingen blijft wél een eigen hoofdstuk: dat
# register beslaat alle drie de niveaus, en het is voor governance het blad
# waar het oordeel op rust.
#
# Vijf SAD-secties zijn overgenomen omdat ze in de TOGAF-vorm ontbraken:
#
# §2   Architectural Representation — welke weergaven worden gebruikt, voor
#      welke lezer, en wat erin staat. RUP begint hier bewust mee: wie de
#      leeswijzer overslaat, leest de diagrammen verkeerd.
# §3   Architectural Goals and Constraints — de eisen die de vorm van de
#      architectuur bepalen (veiligheid, privacy, hergebruik, aangeschafte
#      producten) én de opgelegde beperkingen (hulpmiddelen, teamsamenstelling,
#      planning, bestaande systemen). Dat tweede rijtje is wat RUP toevoegt:
#      niet alle vorm komt uit eisen, veel komt uit omstandigheden.
# §4   Use-Case View — de use cases die de structuur bepalen. Dit is de
#      koppeling met de practice Use cases.
# §7   Deployment View — waar het draait.
# §9   Data View — de gegevensopslag, als die niet triviaal is.
# §10  Size and Performance — de omvangskenmerken die de architectuur raken.
# §11  Quality — hoe de architectuur de niet-functionele eigenschappen waarmaakt.

def architectuurmodel(wp):
    return (
        preamble(wp)
        + heading("Afbakening en detailniveau")
        + guidance("Wat wel en niet in dit model zit, en tot welk C4-niveau is "
                   "uitgewerkt. Werk alleen uit wat nodig is om de verandering "
                   "te begrijpen; wat ongewijzigd blijft, wordt niet opnieuw "
                   "beschreven.")
        + placeholder()

        + heading("Weergaven in dit model")
        + guidance("Welke weergaven dit model bevat, voor welke lezer ze "
                   "bedoeld zijn en welke soort elementen erin staan. Deze "
                   "leeswijzer voorkomt dat een diagram wordt gelezen als "
                   "antwoord op een vraag die het niet beantwoordt.")
        + content_table(["Weergave", "Voor wie", "Wat erin staat"], rows=4)

        + heading("Architectuurdoelen en beperkingen")
        + guidance("Twee soorten krachten bepalen de vorm van dit model. "
                   "Doelen komen uit eisen: beveiliging, privacy, "
                   "beschikbaarheid, hergebruik, verplichte aangeschafte "
                   "producten. Beperkingen komen uit omstandigheden: bestaande "
                   "systemen, beschikbare hulpmiddelen, samenstelling van het "
                   "team, planning, contracten. Benoem ze allebei — veel van de "
                   "vorm komt niet uit de eisen maar uit de omstandigheden.")
        + placeholder()

        + heading("Structuurbepalende use cases")
        + guidance("De use cases en scenario's die de opbouw van de solution "
                   "bepalen: omdat ze veel bouwstenen raken, omdat ze het "
                   "meeste volume dragen, of omdat ze een gevoelig punt in de "
                   "architectuur blootleggen. Verwijs naar het use-casemodel; "
                   "schrijf ze hier niet opnieuw uit.")
        + content_table(["Use case", "Waarom structuurbepalend",
                         "Welke containers geraakt"], rows=4)

        + heading("Context")
        + guidance("De grenzen van de solution en haar omgeving: gebruikers, "
                   "aangrenzende systemen en externe partijen. Voeg het "
                   "contextdiagram hier in en zet daarna in het register wie "
                   "er aan de andere kant van elke grens staat — die eigenaren "
                   "heb je nodig zodra er aan een koppeling iets verandert.")
        + placeholder(2)
        + content_table(["Partij of systeem", "Relatie tot de solution",
                         "Eigenaar"], rows=4)

        + heading("Containers")
        + guidance("De bouwstenen waaruit de solution bestaat: elk onderdeel "
                   "dat zelfstandig draait of gegevens vasthoudt. Voor de "
                   "meeste solutions is dit het niveau waarop governance haar "
                   "oordeel vormt. Voeg het containerdiagram hier in en werk "
                   "het uit in het register: waar de container "
                   "verantwoordelijk voor is, waar zijn grens ligt en wie hem "
                   "bezit.")
        + placeholder(2)
        + content_table(["Container", "Verantwoordelijkheid", "Grens",
                         "Eigenaar"], rows=5)

        + heading("Componenten")
        + guidance("Alleen uitwerken waar een architectuurbepalende eis, een "
                   "risico of een beslissing dat vereist — en dan alleen voor "
                   "de container waar dat speelt. Laat dit hoofdstuk anders "
                   "leeg: een volledig uitgewerkt componentniveau veroudert "
                   "sneller dan het wordt gelezen.")
        + placeholder(2)
        + content_table(["Component", "In welke container",
                         "Verantwoordelijkheid", "Waarom uitgewerkt"], rows=4)

        + heading("Koppelingen")
        + guidance("Per koppeling wat er wordt uitgewisseld en wat er gebeurt "
                   "als de andere kant wegvalt. Dit register beslaat de drie "
                   "niveaus hierboven — koppelingen over de systeemgrens heen "
                   "én tussen containers onderling — en staat daarom apart. "
                   "Voor governance is het doorgaans het belangrijkste blad "
                   "van het document.")
        + content_table(["Koppeling", "Van", "Naar", "Wat wordt uitgewisseld",
                         "Gedrag bij uitval"], rows=5)

        + heading("Plaatsing")
        + guidance("Waarop de bouwstenen draaien: omgevingen, knooppunten en "
                   "de verbindingen ertussen, met de afbeelding van containers "
                   "op die knooppunten. Voeg het deploymentdiagram hier in. "
                   "Laat weg wat standaard uit de paved road volgt.")
        + placeholder(2)

        + heading("Gegevens")
        + guidance("Welke gegevens waar worden vastgelegd, wie eigenaar is en "
                   "hoe lang ze bewaard blijven. Sla deze sectie over als de "
                   "opslag triviaal is of geheel uit de bouwstenen volgt.")
        + placeholder()

        + heading("Omvang en prestaties")
        + guidance("De omvangskenmerken die de vorm van de architectuur raken: "
                   "aantallen gebruikers, volumes, groei, piekbelasting, en de "
                   "prestatiegrenzen waarbinnen dat moet passen.")
        + placeholder()

        + heading("Kwaliteitseigenschappen")
        + guidance("Hoe deze architectuur de eigenschappen waarmaakt die niet "
                   "in functionaliteit zijn uit te drukken: beschikbaarheid, "
                   "herstelbaarheid, beveiliging, uitbreidbaarheid, "
                   "onderhoudbaarheid. Zeg per eigenschap wélke keuze in dit "
                   "model haar levert, niet dát de architectuur eraan voldoet.")
        + placeholder()

        + heading("Verschil met de huidige situatie")
        + guidance("Wat verdwijnt, wat verandert, wat komt erbij. Beschrijf de "
                   "huidige situatie alleen voor zover ze geraakt wordt.")
        + placeholder()

        + heading("Onderbouwing van de keuzes")
        + guidance("Niet hier uitschrijven. Verwijs naar de "
                   "architectuurbeslissingen waarin de afwegingen zijn "
                   "vastgelegd.")
        + placeholder()

        + heading("Vindplaats in de architectuurrepository")
        + guidance("Waar de componenten van dit model zijn opgenomen, zodat ze "
                   "op dezelfde autoritatieve plek staan als de overige "
                   "artefacten.")
        + placeholder()

        + heading("Gereed wanneer")
        + checklist([
            "De leeswijzer benoemt elke weergave en haar lezer.",
            "De systeemgrenzen zijn eenduidig.",
            "Van elke partij aan de andere kant van een grens is de eigenaar "
            "bekend.",
            "Doelen én opgelegde beperkingen zijn benoemd.",
            "De structuurbepalende use cases staan erbij.",
            "Elke container heeft een verantwoordelijkheid, een grens en een "
            "eigenaar.",
            "Componenten zijn alleen uitgewerkt waar een eis, risico of "
            "beslissing dat vroeg.",
            "Van elke koppeling is het gedrag bij uitval bekend.",
            "Bij elke kwaliteitseigenschap staat welke keuze haar levert.",
            "Het verschil met de huidige situatie is zichtbaar.",
            "De onderbouwing staat in architectuurbeslissingen, niet hier.",
            "Het model is opgenomen in de architectuurrepository.",
        ])
    )


# ==========================================================================
# Architectuurbeslissingen
# Traditie: Architecture Decision Records
# RUP:      SAD §3 en §11; Business Architecture Document §11
# ==========================================================================
# TOGAF kent hiervoor geen eigen deliverable en RUP evenmin: de SAD zegt zelf
# dat hij "the significant architectural decisions" vastlegt, maar zonder
# alternatieven, afweging of status per beslissing. De opbouw volgt daarom de
# ADR-praktijk — context, opties, besluit, gevolgen.
#
# Eén RUP-element is wél overgenomen. Het Business Architecture Document sluit
# af met §11 Architectural Trade-offs: loop elke driver en beperking langs en
# zeg hoe de gekozen architectuur die ondersteunt, "pay special attention to
# conflicts, because the architecture is an optimal solution to many conflicting
# forces". Dat is de enige plek in de hele RUP-set waar de afweging expliciet
# wordt afgedwongen, en het is precies wat een ADR moet doen.

def architectuurbeslissingen(wp):
    return (
        preamble(wp, ["Project", "Nummer en titel", "Beslisser",
                      "Versie", "Datum"])
        + note("Eén beslissing per document. Voor dagelijkse keuzes die binnen "
               "de paved road vallen volstaan de secties Beslissing, Status en "
               "Onderbouwing; de volledige uitwerking is voor off-road "
               "gevallen.")

        + heading("Beslissing")
        + guidance("De keuze in één zin, zo geformuleerd dat iemand die het "
                   "dossier niet kent hem begrijpt.")
        + placeholder()

        + heading("Status")
        + guidance("Voorgesteld, aanvaard, vervangen of ingetrokken. Bij "
                   "vervangen: door welke beslissing.")
        + placeholder()

        + heading("Aanleiding")
        + guidance("Welke architectuurbepalende eis om deze keuze vraagt, en "
                   "waarom die eis de structuur, samenhang of kwaliteit van de "
                   "solution raakt.")
        + placeholder()

        + heading("Context")
        + guidance("Wat er speelt, welke beperkingen gelden en wat er al "
                   "vastligt. Genoeg voor een lezer die er later bij komt.")
        + placeholder()

        + heading("Overwogen opties")
        + guidance("Ook de opties die zijn afgevallen. Een beslissing zonder "
                   "alternatieven is geen beslissing.")
        + content_table(["Optie", "Pleit voor", "Pleit tegen"], rows=3)

        + heading("Afweging tegen de drivers")
        + guidance("Loop elke driver en beperking langs en zeg hoe deze keuze "
                   "die ondersteunt. Besteed vooral aandacht aan de plekken "
                   "waar het schuurt: een architectuur is een optimum tussen "
                   "krachten die elkaar tegenwerken, en die spanning hoort "
                   "zichtbaar te zijn in plaats van weggeschreven.")
        + content_table(["Driver of beperking", "Hoe deze keuze eraan bijdraagt",
                         "Waar het schuurt"], rows=4)

        + heading("Onderbouwing")
        + guidance("Waarom deze optie en niet de andere. Benoem de afweging "
                   "die de doorslag gaf.")
        + placeholder()

        + heading("Gevolgen")
        + guidance("Wat deze keuze oplevert én wat ze kost: welk nadeel is "
                   "bewust aanvaard, en wat wordt er hierdoor moeilijker.")
        + placeholder()

        + heading("Relatie tot de paved road")
        + guidance("On-road of off-road. Bij off-road: van welk catalogusitem "
                   "wordt afgeweken, en voor hoe lang.")
        + placeholder()

        + heading("Vervolg")
        + guidance("Wat er moet gebeuren om de beslissing door te voeren, en "
                   "wanneer ze opnieuw tegen het licht wordt gehouden.")
        + placeholder()

        + heading("Gereed wanneer")
        + checklist([
            "Het document beschrijft precies één keuze.",
            "De afgevallen alternatieven staan erbij.",
            "Van elke driver is te zien hoe deze keuze eraan bijdraagt.",
            "Waar de keuze schuurt met een driver, staat dat er.",
            "Het aanvaarde nadeel is benoemd.",
            "Duidelijk is of de keuze on-road of off-road is.",
            "De beslisser is bevoegd volgens de werkafspraken.",
        ])
    )


# ==========================================================================
# Migratiescenario
# TOGAF: Architecture Roadmap (fase B) + Implementation and Migration Plan (E)
# RUP:   Deployment Plan §3.1, §3.2, §4, §5
# ==========================================================================
# De roadmap ordent de verandering in transitiearchitecturen; het migratieplan
# onderbouwt de volgorde en de afhankelijkheden. De RDF scherpt dat aan: elk
# plateau is operationeel verdedigbaar, en de volgorde wordt langs vier lijnen
# onderbouwd — data, techniek, risico en niet-technische realiteit.
#
# RUP's Deployment Plan gaat over één uitrol, maar stelt drie vragen die per
# plateau net zo hard gelden en in de TOGAF-vorm ontbreken:
#
# §3.1  wie waarvoor verantwoordelijk is bij de overgang, inclusief de rol van
#       de ontvangende kant bij de acceptatie en wat er gebeurt bij afwijkingen;
# §4    welke mensen en middelen de overgang vraagt — omgevingen, licenties,
#       beheercapaciteit, ondersteunende software;
# §5    wat gebruikers en beheer moeten leren voordat het plateau echt draait.
#
# Zonder die drie blijft een plateau een tekening; mét die drie is het een
# toestand waarin iemand daadwerkelijk kan werken.

def migratiescenario(wp):
    return (
        preamble(wp)
        + heading("Uitgangspunt en einddoel")
        + guidance("Waar de solution nu staat en waar ze uitkomt. Beschrijf "
                   "het einddoel zo dat te bepalen is wanneer het bereikt is.")
        + placeholder()

        + heading("Detailniveau van dit scenario")
        + guidance("Op welk niveau dit scenario is uitgewerkt — strategisch, "
                   "tactisch, solution-specifiek of operationeel — en welke "
                   "plateaus daarom scherp zijn en welke bewust globaal "
                   "blijven.")
        + placeholder()

        + heading("Plateaus in volgorde")
        + guidance("Elk plateau is een toestand waarin de solution als geheel "
                   "werkt. Tussen plateaus mag nooit een half werkende "
                   "toestand ontstaan.")
        + content_table(["Plateau", "Wat er dan werkt", "Periode"], rows=4)

        + heading("Uitwerking per plateau")
        + subheading("Plateau 1 — [ naam ]")
        + fld("Wat werkt en is operationeel",
              "welke functionaliteit op dit punt in productie is.")
        + fld("Wat loopt tijdelijk parallel",
              "wat er naast elkaar blijft draaien, en tot wanneer.")
        + fld("Integraties",
              "welke koppelingen bestaan, en welke daarvan tijdelijk zijn.")
        + fld("Afhankelijkheden",
              "wat er klaar moet zijn voordat dit plateau haalbaar is.")
        + fld("Mensen en middelen",
              "wat de overgang nodig heeft: omgevingen, licenties, "
              "beheercapaciteit, ondersteunende software, externe inzet.")
        + fld("Vastgesteld stabiel wanneer",
              "waaraan de ontvangende kant afleest dat dit plateau werkelijk "
              "draait — niet dat het is opgeleverd, maar dat ermee gewerkt "
              "wordt.")
        + fld("Risico's",
              "wat er misgaat als dit plateau niet stabiel blijkt.")
        + repeat_note("Herhaal dit blok per plateau.")

        + heading("Onderbouwing van de volgorde")
        + guidance("Waarom deze volgorde en geen andere. Loop de vier lijnen "
                   "langs; laat een lijn leeg als ze hier niet speelt.")
        + fld("Data-afhankelijkheid",
              "welke gegevens er eerst moeten zijn voordat een volgende stap kan.")
        + fld("Technische afhankelijkheid",
              "welke integratiepunten een vaste volgorde afdwingen.")
        + fld("Risico",
              "welke stap eerst gaat omdat uitstel het risico vergroot.")
        + fld("Niet-technische realiteit",
              "budget, contracten, leveranciers of organisatorische gereedheid.")

        + heading("Verantwoordelijkheden bij een overgang")
        + guidance("Wie wat doet op het moment dat een plateau in gebruik "
                   "wordt genomen — aan de kant van het realisatieteam én aan "
                   "de ontvangende kant. Leg vast wat er gebeurt als bij de "
                   "ingebruikname blijkt dat iets niet werkt zoals afgesproken.")
        + content_table(["Wie", "Waarvoor verantwoordelijk",
                         "Bij afwijking"], rows=4)

        + heading("Opleiding en gewenning")
        + guidance("Wat gebruikers en beheer moeten kennen of kunnen voordat "
                   "een plateau werkelijk draait, en wanneer dat geregeld is. "
                   "Een plateau dat technisch klaar is maar waar niemand mee "
                   "overweg kan, is niet stabiel.")
        + content_table(["Plateau", "Wie", "Wat ze moeten kunnen",
                         "Wanneer geregeld"], rows=3)

        + heading("Tijdelijke voorzieningen")
        + guidance("Wat er alleen bestaat om de overgang mogelijk te maken. "
                   "Zonder afbouwmoment blijft een tijdelijke voorziening "
                   "permanent.")
        + content_table(["Voorziening", "Waarom nodig", "Afbouw uiterlijk"],
                        rows=3)

        + heading("Beslismomenten")
        + guidance("Waar tijdens de uitvoering opnieuw wordt besloten of het "
                   "scenario nog klopt, en wie dat besluit neemt.")
        + placeholder()

        + heading("Gereed wanneer")
        + checklist([
            "Elk plateau is een toestand waarin de solution als geheel werkt.",
            "Van elk plateau staat vast waaraan stabiliteit wordt afgelezen.",
            "De volgorde is onderbouwd, niet impliciet.",
            "Van elke overgang is bekend wie waarvoor verantwoordelijk is.",
            "Wat gebruikers en beheer moeten leren, is belegd.",
            "Van elke tijdelijke voorziening staat vast wanneer ze verdwijnt.",
            "De afhankelijkheden tussen plateaus zijn benoemd.",
            "Het scenario sluit aan op de enterprise-brede horizons.",
        ])
    )


# ==========================================================================
# Reviewresultaten
# TOGAF: Compliance Assessment (fase G)
# RUP:   Iteration Assessment §7; Configuration Management Plan §3.1.1, §3.3.2
# ==========================================================================
# De compliance assessment legt per geval vast wat is getoetst, waartegen, en
# met welk oordeel — conform, met condities, afgekeurd, of uitzondering
# toegestaan — en telt de resultaten over een periode op als signaal voor het
# bijstellen van de governance.
#
# RUP voegt drie dingen toe:
#
# CM Plan §3.1.1  identificatie: benoem exact welke versie of baseline is
#                 beoordeeld. Een oordeel over "de architectuur" zonder
#                 versienummer is een week later niet meer te plaatsen.
# IA §7           "External Changes Occurred": wat er buiten het geval om is
#                 veranderd sinds de vorige toetsing — gewijzigde eisen, nieuwe
#                 regelgeving, een verschoven paved road.
# CM Plan §3.3.2  rapportage over een periode langs drie vaste lijnen:
#                 doorlooptijd, verdeling en trend. Dat is precies de optelling
#                 die "Toets werking governance" nodig heeft.

def reviewresultaten(wp):
    return (
        preamble(wp, ["Project", "Getoetst object", "Versie getoetst object",
                      "Getoetst door", "Beslisser", "Versie", "Datum"])
        + heading("Wat is getoetst")
        + guidance("Het systeem, product, de leverancier, interface of het "
                   "besluit dat is beoordeeld. Benoem het zo dat er geen "
                   "verwarring over kan bestaan welk geval dit betreft, en zet "
                   "erbij welke versie of baseline op tafel lag — een oordeel "
                   "zonder versie is later niet meer te plaatsen.")
        + placeholder()

        + heading("Waaraan is getoetst")
        + guidance("Tegen welke paved-road-items, principes en drivers is "
                   "gehouden. Alleen de criteria die daadwerkelijk zijn "
                   "toegepast, met de versie waarin ze golden.")
        + placeholder()

        + heading("Wat er sinds de vorige toetsing is veranderd")
        + guidance("Wat er buiten dit geval om is verschoven: gewijzigde eisen, "
                   "nieuwe regelgeving, een aangepast principe, een "
                   "paved-road-item met een andere status. Laat leeg bij een "
                   "eerste toetsing.")
        + placeholder()

        + heading("Bevindingen")
        + guidance("Per bevinding waar ze op slaat, hoe zwaar ze weegt en wat "
                   "ermee gebeurt. Bevindingen zonder eigenaar verdwijnen.")
        + content_table(["Nr", "Bevinding", "Ernst", "Actie", "Eigenaar",
                         "Uiterlijk"], rows=4)

        + heading("Oordeel")
        + guidance("Conform, conform met condities, afgekeurd, of uitzondering "
                   "toegestaan. Eén oordeel, met de onderbouwing erbij.")
        + placeholder()

        + heading("Condities")
        + guidance("Als het oordeel condities kent: welke, en wat er gebeurt "
                   "als er niet aan wordt voldaan. Laat leeg bij een "
                   "onvoorwaardelijk oordeel.")
        + placeholder()

        + heading("Geldigheid en herbeoordeling")
        + guidance("Tot wanneer dit oordeel geldt en op welke datum opnieuw "
                   "moet worden beoordeeld.")
        + placeholder()

        + heading("Signaal voor de governance")
        + guidance("Wat dit geval zegt over de werkwijze zelf — een principe "
                   "dat vaak wordt omzeild, een paved-road-item dat niet "
                   "voldoet. Toets werking governance telt deze signalen op.")
        + placeholder()

        + heading("Optelling over de periode")
        + guidance("Alleen invullen bij een periodieke rapportage over meerdere "
                   "toetsingen. Eén geval zegt weinig; de drie lijnen hieronder "
                   "laten zien of de governance zelf nog werkt.")
        + fld("Doorlooptijd",
              "hoe lang een toetsing gemiddeld openstond, en waar de "
              "uitschieters zaten.")
        + fld("Verdeling",
              "hoeveel gevallen per oordeel, per domein en per team — waar "
              "stapelen de afwijkingen zich op.")
        + fld("Trend",
              "of het beeld beter of slechter wordt ten opzichte van de vorige "
              "periode, en wat die beweging verklaart.")

        + heading("Gereed wanneer")
        + checklist([
            "Het getoetste object en de getoetste versie zijn eenduidig.",
            "De toegepaste criteria staan erbij, met hun versie.",
            "Er is één oordeel, met onderbouwing.",
            "Elke bevinding heeft een eigenaar en een termijn.",
            "De herbeoordelingsdatum ligt vast.",
        ])
    )


# ==========================================================================
# Use-casemodel
# RUP: Use-Case Model Survey; Vision §4.1; Vision bijlage A
# ==========================================================================
# RUP publiceert geen sjabloon voor het Use-Case Model zelf: het is daar een
# modelartefact in een tekentool, en wat op papier komt is de Use-Case Model
# Survey — actoren en use cases met per use case niet meer dan een naam en een
# korte omschrijving. Dat is exact wat de RDF van dit werkproduct vraagt.
#
# Twee dingen zijn erbij gehaald:
#
# Vision §4.1   Product Perspective — het systeem in zijn omgeving, met de
#               grens erin getekend. Zonder die grens is een use-caselijst niet
#               te beoordelen op volledigheid.
# Vision bij-   Feature Attributes: benefit, effort, risk, stability. RUP zet
# lage A        die attributen op features om de uitwerkingsvolgorde te bepalen.
#               Hier staan ze op use cases, omdat de activiteit "Specificeer use
#               cases" precies op die vier gronden kiest wat als eerste wordt
#               uitgeschreven.
#
# De RUP-instructie dat een woordenlijst onmisbaar is om use cases beheersbaar
# te houden ("A Glossary of Terms is essential to keep the complexity of the use
# case manageable") is overgenomen als eigen sectie.

def use_casemodel(wp):
    return (
        preamble(wp, ["Project", "Systeem", "Opdrachtgever",
                      "Versie", "Datum"])
        + heading("Het systeem en zijn grens")
        + guidance("Waar dit model over gaat en waar het systeem ophoudt. "
                   "Alles wat een actor doet valt buiten de grens, alles wat "
                   "het systeem als antwoord daarop doet valt erbinnen. Zet er "
                   "de aangrenzende systemen bij waarmee wordt uitgewisseld.")
        + placeholder()

        + heading("Wat buiten de grens valt")
        + guidance("Wat uitdrukkelijk niet door dit systeem wordt gedaan, ook "
                   "al zou men dat kunnen verwachten. Deze lijst begrenst de "
                   "omvang van het werk net zo hard als de use cases zelf.")
        + placeholder()

        + heading("Actoren")
        + guidance("Wie of wat met het systeem communiceert: rollen van mensen "
                   "en andere systemen die het aanroepen of erdoor worden "
                   "aangeroepen. Wie belang heeft bij de uitkomst maar het "
                   "systeem niet bedient, is belanghebbende en geen actor — dat "
                   "onderscheid houdt het model klein.")
        + content_table(["Actor", "Mens of systeem", "Wat deze doet",
                         "Vertegenwoordigd door"], rows=5)

        + heading("Use cases")
        + guidance("Per use case een naam in de vorm werkwoord met lijdend "
                   "voorwerp, plus het afgeronde resultaat waarna de actor "
                   "tevreden weg kan lopen. 'Aanvraag indienen' is een use "
                   "case; 'inloggen' of 'formulier valideren' is dat niet, hoe "
                   "noodzakelijk ook. Meer dan een naam en een resultaat hoort "
                   "hier niet: het detail staat in de use-casespecificatie.")
        + content_table(["Nr", "Use case", "Primaire actor",
                         "Beoogd resultaat"], rows=8)

        + heading("Groepering")
        + guidance("Waar het verheldert: welke use cases bij elkaar horen, per "
                   "actor of per samenhangend gebruik. Sla over bij een "
                   "overzichtelijk aantal use cases.")
        + placeholder()

        + heading("Use-casediagram")
        + guidance("Alleen zinvol wanneer het aantal actoren groot is, wanneer "
                   "meerdere actoren dezelfde use case delen, of wanneer de "
                   "systeemgrens zelf onderwerp van discussie is en visueel "
                   "bevestigd moet worden. Voeg het diagram hier in.")
        + placeholder(2)

        + heading("Uitwerkingsvolgorde")
        + guidance("Per use case vier inschattingen die samen bepalen wat als "
                   "eerste wordt uitgeschreven: hoeveel de use case oplevert, "
                   "hoeveel werk hij is, hoeveel risico eraan zit, en hoe "
                   "stabiel het beeld ervan is. Een use case met veel risico en "
                   "weinig stabiliteit gaat eerst, ook als hij weinig oplevert "
                   "— daar zit de onzekerheid die weg moet.")
        + content_table(["Use case", "Waarde", "Omvang", "Risico", "Stabiliteit",
                         "Uitwerken in"], rows=6)

        + heading("Begrippen")
        + guidance("De termen die in de use cases terugkomen en die niet voor "
                   "iedereen hetzelfde betekenen. Zonder deze lijst verzuipen "
                   "de scenario's in uitleg, of erger: lezen twee partijen "
                   "hetzelfde woord verschillend.")
        + content_table(["Term", "Betekenis hier"], rows=5)

        + heading("Openstaande vragen")
        + guidance("Wat nog onbeslist is en wie het beslist. Een use case "
                   "waarover de opdrachtgever en de gebruikersvertegenwoordiger "
                   "het oneens zijn, hoort hier te staan en niet stilzwijgend "
                   "in de lijst.")
        + content_table(["Vraag", "Raakt welke use case", "Wie beslist",
                         "Uiterlijk"], rows=3)

        + heading("Vaststelling")
        + guidance("Wie het model heeft bevestigd en wanneer. Zolang de "
                   "opdrachtgever en de gebruikersvertegenwoordigers de use "
                   "cases niet herkennen als iets waar zij waarde aan hechten, "
                   "is de omvang van het werk niet werkelijk begrensd.")
        + placeholder()

        + heading("Gereed wanneer")
        + checklist([
            "Elke use case levert een afgerond resultaat op voor een actor.",
            "Elke use case heeft een primaire actor.",
            "De systeemgrens is eenduidig, inclusief wat erbuiten valt.",
            "Actoren en belanghebbenden zijn niet door elkaar gehaald.",
            "Per use case is ingeschat hoe risicovol en hoe stabiel hij is.",
            "De begrippenlijst dekt de termen die in de use cases voorkomen.",
            "De stakeholders herkennen de use cases als hun eigen werk.",
        ])
    )


# ==========================================================================
# Use-casespecificatie
# RUP: Use-Case Specification §1–§10
# ==========================================================================
# Dit is de meest letterlijke overname van de hele set: de RUP-template dekt de
# definitie uit de RDF volledig — hoofdscenario (§2), afwijkingen (§3, §4),
# voorwaarden (§6, §7), regels en bijzondere eisen (§9).
#
# De RUP-instructies zijn overgenomen omdat ze bijna allemaal een concrete
# schrijffout voorkomen:
#
# §2   schrijf als een dialoog tussen actor en systeem; beschrijf wát er
#      gebeurt, niet hoe of waarom; wees specifiek over de uitgewisselde
#      gegevens ("de actor voert de naam en het adres in", niet "de actor voert
#      klantgegevens in");
# §3   begin elk alternatief met waar en onder welke voorwaarde het optreedt,
#      en eindig met waar het hoofdscenario wordt hervat — expliciet, want
#      anders loopt het alternatief dood;
# §4   subscenario's zijn atomair: je doet alle stappen of geen;
# §5   benoem de scenario's die er werkelijk toe doen, want het aantal
#      mogelijke combinaties is onbeperkt;
# §9   bijzondere eisen zijn eisen die alleen voor déze use case gelden — de
#      rest hoort in de aanvullende specificaties.
#
# RUP's §8 Extension Points is meegenomen maar met de aantekening dat hij pas
# nodig is bij hergebruik tussen use cases.

def use_casespecificatie(wp):
    return (
        preamble(wp, ["Project", "Use case", "Nummer", "Versie", "Datum"])
        + note("Eén use case per document. Voor een herkenbare, goed begrepen "
               "use case volstaan de secties Korte beschrijving, Hoofdscenario "
               "en Resultaat na afloop; de volledige uitwerking is voor use "
               "cases die de structuur bepalen, technisch risico dragen, zwaar "
               "onder regelgeving vallen of waarover de stakeholders het nog "
               "niet eens zijn.")

        + heading("Korte beschrijving")
        + guidance("Waartoe deze use case dient, in één alinea. Eindig met het "
                   "resultaat waarna de actor tevreden weg kan lopen.")
        + placeholder()

        + heading("Actoren")
        + guidance("De primaire actor die de use case start, en de overige "
                   "actoren die eraan meedoen — inclusief aangrenzende "
                   "systemen.")
        + content_table(["Actor", "Rol in deze use case"], rows=3)

        + heading("Voorwaarden vooraf")
        + guidance("In welke toestand het systeem moet zijn voordat deze use "
                   "case kan beginnen. Noem alleen wat werkelijk vereist is; "
                   "'de gebruiker is ingelogd' is vaak de enige.")
        + placeholder()

        + heading("Hoofdscenario")
        + guidance("Genummerde stappen waarin actor en systeem elkaar "
                   "afwisselen, tot het beoogde resultaat is bereikt. Schrijf "
                   "als een dialoog: wat de actor doet en wat het systeem "
                   "daarop antwoordt. Beschrijf wát er gebeurt, niet hoe of "
                   "waarom. Wees specifiek over de uitgewisselde gegevens — "
                   "'de actor voert naam en adres in' zegt iets, 'de actor "
                   "voert klantgegevens in' niets. Houd de uitzonderingen "
                   "eruit: een hoofdscenario dat is doorspekt met afwijkingen "
                   "leest niemand meer.")
        + placeholder(4)

        + heading("Alternatieve scenario's")
        + guidance("Elke afwijking krijgt een eigen blok. Begin met de stap "
                   "waar de afwijking optreedt en de voorwaarde waaronder, en "
                   "eindig met waar het hoofdscenario wordt hervat — of dat de "
                   "use case hier eindigt. Dat laatste expliciet vermelden, "
                   "anders loopt het alternatief dood. Groepeer bij elkaar wat "
                   "over hetzelfde onderwerp gaat.")
        + subheading("A1 — [ naam van de afwijking ]")
        + fld("Treedt op bij stap",
              "het stapnummer in het hoofdscenario en de voorwaarde waaronder "
              "deze afwijking optreedt.")
        + fld("Verloop",
              "de stappen van de afwijking, in dezelfde dialoogvorm als het "
              "hoofdscenario.")
        + fld("Afloop",
              "waar het hoofdscenario wordt hervat, of dat de use case hier "
              "eindigt en met welk resultaat.")
        + repeat_note("Herhaal dit blok per alternatief scenario.")

        + heading("Subscenario's")
        + guidance("Stukken verloop die vanuit meerdere plekken worden "
                   "aangeroepen. Een subscenario is atomair: alle stappen of "
                   "geen. Vermijd meerdere lagen — dat maakt de tekst juist "
                   "moeilijker. Laat leeg als er niets terugkeert.")
        + placeholder()

        + heading("Belangrijkste scenario's")
        + guidance("Welke doorlopen er werkelijk toe doen: het meest "
                   "voorkomende, het gevoeligste, en de combinaties die de "
                   "betrokken actoren zorgen baren. Het aantal mogelijke "
                   "doorlopen is onbeperkt; benoem hier de doorlopen die "
                   "getest en besproken moeten worden.")
        + content_table(["Scenario", "Welke stappen", "Waarom van belang"],
                        rows=3)

        + heading("Resultaat na afloop")
        + guidance("In welke toestand het systeem achterblijft. Noem zowel de "
                   "toestand na een geslaagd verloop als na de afwijkingen die "
                   "de use case voortijdig beëindigen.")
        + placeholder()

        + heading("Uitgewisselde gegevens en regels")
        + guidance("Welke gegevens tussen actor en systeem heen en weer gaan, "
                   "en welke regels daarop gelden: verplicht of niet, "
                   "toegestane waarden, afleidingen, controles. Verwijs naar de "
                   "begrippenlijst in het use-casemodel in plaats van termen "
                   "hier opnieuw uit te leggen.")
        + content_table(["Gegeven", "Van wie naar wie", "Regel"], rows=5)

        + heading("Uitbreidingspunten")
        + guidance("Alleen invullen als een andere use case op een vast punt "
                   "in dit verloop inhaakt. Benoem het punt en waar het in het "
                   "hoofdscenario zit. Sla over bij een op zichzelf staande "
                   "use case.")
        + placeholder()

        + heading("Bijzondere eisen")
        + guidance("Eisen die alleen voor déze use case gelden en die niet in "
                   "het verloop passen: een responstijd voor juist deze "
                   "handeling, een wettelijke bewaarplicht op dit gegeven. Wat "
                   "voor meerdere use cases geldt, hoort niet hier maar in de "
                   "aanvullende specificaties.")
        + content_table(["Eis", "Norm en omstandigheden", "Herkomst"], rows=3)

        + heading("Openstaande vragen en aannames")
        + guidance("Wat nog bevestigd moet worden, door wie, en voor wanneer. "
                   "Een aanname die in de tekst verstopt zit, wordt nooit "
                   "getoetst.")
        + content_table(["Vraag of aanname", "Wie bevestigt", "Uiterlijk"],
                        rows=3)

        + heading("Aanvullende informatie")
        + guidance("Schermschetsen, een stroomschema bij een ingewikkeld "
                   "beslispad, een voorbeeld met echte waarden. Alleen als het "
                   "verheldert; een plaatje dat uitleg nodig heeft, verheldert "
                   "niet.")
        + placeholder()

        + heading("Toetsing bij de betrokkenen")
        + guidance("Wie het scenario heeft doorgenomen en wanneer. Pas als de "
                   "betrokken actoren hun eigen werkwijze erin herkennen — of "
                   "bewust voor een andere kiezen — is de specificatie af.")
        + placeholder()

        + heading("Gereed wanneer")
        + checklist([
            "Het hoofdscenario eindigt bij het resultaat waarvoor de use case "
            "bestaat.",
            "Per stap is duidelijk wie handelt: de actor of het systeem.",
            "De uitgewisselde gegevens zijn benoemd, niet samengevat.",
            "Elk alternatief scenario heeft een aanleiding en een afloop.",
            "Voorwaarden vooraf en resultaat na afloop staan er allebei.",
            "Eisen die breder gelden staan in de aanvullende specificaties.",
            "De betrokken actoren herkennen hun eigen werkwijze.",
        ])
    )


# ==========================================================================
# Aanvullende specificaties
# RUP: Supplementary Specification §2–§13
# ==========================================================================
# Ook hier dekt RUP het werkproduct volledig, inclusief de definitie: "captures
# the system requirements that are not readily captured in the use cases of the
# use-case model".
#
# De hoofdstukindeling is één op één overgenomen, omdat juist de vaste volgorde
# het werk doet. De RDF zegt het zo: er wordt een vaste indeling naar
# kwaliteitskenmerken aangehouden "zodat systematisch kan worden nagegaan of er
# niets ontbreekt in plaats van af te wachten wat stakeholders uit zichzelf
# noemen". De koppen zijn daarmee geen inhoudsopgave maar een checklist.
#
# Afwijkingen van RUP:
#
# *   Beveiliging heeft een eigen sectie. RUP schuift die onder §2
#     Functionality; in deze werkwijze is beveiliging een kwaliteitskenmerk met
#     een eigen kader en hoort ze naast beschikbaarheid en prestaties.
# *   Elke sectie is een register in plaats van lopende tekst, met vaste
#     kolommen voor norm, herkomst en reikwijdte. De RDF eist dat elke eis
#     toetsbaar is en dat per eis vastligt voor welke use cases hij geldt; dat
#     laat zich niet in proza afdwingen.
# *   RUP's §9 Purchased Components en §11 Licensing zijn samengevoegd, evenals
#     §12 Legal en §13 Applicable Standards.
# *   Twee secties zijn toegevoegd die RUP niet kent maar die in deze werkwijze
#     onmisbaar zijn: de relatie tot de paved road en de architectuurprincipes,
#     en de tegenstrijdigheden tussen eisen onderling.

EIS_KOLOMMEN = ["Nr", "Eis", "Norm en omstandigheden", "Geldt voor", "Herkomst"]


def aanvullende_specificaties(wp):
    return (
        preamble(wp, ["Project", "Systeem", "Opdrachtgever",
                      "Versie", "Datum"])
        + heading("Reikwijdte")
        + guidance("Voor welk systeem deze eisen gelden en hoe ze zich "
                   "verhouden tot het use-casemodel. Wat aan één use case is "
                   "toe te wijzen hoort daar en niet hier.")
        + placeholder()

        + heading("Hoe een eis hier is geformuleerd")
        + guidance("Elke eis is een meetbare uitspraak met de omstandigheden "
                   "erbij: welke gebeurtenis zich voordoet, welk deel van het "
                   "systeem het betreft, welke reactie wordt verwacht en binnen "
                   "welke marge. 'Het systeem is snel' is geen eis; 'een "
                   "zoekopdracht over maximaal tienduizend dossiers levert bij "
                   "vijftig gelijktijdige gebruikers binnen twee seconden "
                   "resultaat' wel. In de kolom Herkomst staat waar de eis "
                   "vandaan komt — een wet, een norm, een besluit of een "
                   "stakeholder; in de kolom Geldt voor staat op welke use "
                   "cases of onderdelen hij van toepassing is.")
        + placeholder()

        + heading("Functionaliteit buiten de use cases")
        + guidance("Functionele eisen die zich niet in één use case laten "
                   "vangen omdat ze systeembreed gelden: beheerfuncties, "
                   "signalering, gegevensbewaring, rapportage. Laat leeg als "
                   "alles in de use cases past.")
        + content_table(EIS_KOLOMMEN, rows=3)

        + heading("Bruikbaarheid")
        + guidance("Wat het systeem bruikbaar maakt voor wie ermee werkt: hoe "
                   "lang een nieuwe gebruiker erover mag doen om zelfstandig te "
                   "werken, hoeveel tijd een veelvoorkomende taak mag kosten, "
                   "welke richtlijn voor toegankelijkheid geldt.")
        + content_table(EIS_KOLOMMEN, rows=3)

        + heading("Betrouwbaarheid en beschikbaarheid")
        + guidance("Beschikbaarheid in percentage en binnen welke venstertijden, "
                   "toegestane uitvaltijd, hersteltijd na een storing, "
                   "gedegradeerde werking, maximaal gegevensverlies bij "
                   "herstel, en de nauwkeurigheid die het systeem moet halen.")
        + content_table(EIS_KOLOMMEN, rows=3)

        + heading("Prestaties")
        + guidance("Responstijd per soort handeling — gemiddeld én bij piek — "
                   "doorvoer, capaciteit in aantallen gebruikers of "
                   "transacties, gedrag bij overbelasting, en het "
                   "resourcegebruik dat daarbij is toegestaan. Verwijs waar "
                   "mogelijk naar de use case waarop de eis slaat.")
        + content_table(EIS_KOLOMMEN, rows=3)

        + heading("Beveiliging")
        + guidance("Authenticatie, autorisatie, versleuteling in rust en "
                   "onderweg, herleidbaarheid van handelingen, en de "
                   "classificatie van de verwerkte gegevens. Verwijs naar het "
                   "geldende beveiligingskader in plaats van het over te "
                   "schrijven; benoem hier alleen wat voor dit systeem "
                   "bijzonder is.")
        + content_table(EIS_KOLOMMEN, rows=3)

        + heading("Onderhoudbaarheid en ondersteuning")
        + guidance("Wat het systeem beheerbaar houdt: logging en monitoring, "
                   "diagnosemogelijkheden, doorlooptijd van een wijziging, "
                   "onderhoudsvensters, en wat het beheer moet kunnen zonder "
                   "de leverancier.")
        + content_table(EIS_KOLOMMEN, rows=3)

        + heading("Ontwerpbeperkingen")
        + guidance("Keuzes die al vastliggen en waaraan het ontwerp zich moet "
                   "houden: een voorgeschreven platform, taal, "
                   "gegevensstandaard, hostinglocatie of te hergebruiken "
                   "component. Zet erbij wie de beperking heeft opgelegd — een "
                   "beperking zonder bron blijkt bij navraag vaak geen "
                   "beperking.")
        + content_table(EIS_KOLOMMEN, rows=3)

        + heading("Koppelvlakken")
        + guidance("De koppelvlakken die het systeem moet ondersteunen, met "
                   "genoeg detail om ertegen te kunnen bouwen en toetsen: "
                   "koppelvlakken met gebruikers, met apparatuur, met andere "
                   "software en met netwerkvoorzieningen.")
        + content_table(["Nr", "Koppelvlak", "Soort", "Eis en standaard",
                         "Wederpartij"], rows=4)

        + heading("Aangeschafte componenten en licenties")
        + guidance("Producten van derden die worden gebruikt, met de "
                   "gebruiksbeperkingen, licentievorm en de eisen die daaruit "
                   "volgen voor uitwisselbaarheid en versiebeheer.")
        + content_table(["Component", "Waarvoor", "Licentie en beperking",
                         "Gevolg voor het ontwerp"], rows=3)

        + heading("Wettelijk kader en normen")
        + guidance("Wet- en regelgeving, sectornormen en interne standaarden "
                   "waaraan het systeem moet voldoen. Benoem per bron het "
                   "specifieke artikel of hoofdstuk dat van toepassing is — een "
                   "verwijzing naar een hele wet is geen eis.")
        + content_table(["Bron", "Welk onderdeel", "Wat het verplicht",
                         "Geldt voor"], rows=4)

        + heading("Documentatie en hulp bij gebruik")
        + guidance("Welke handleiding, ingebouwde hulp of "
                   "installatiedocumentatie wordt verlangd, voor wie en in "
                   "welke vorm. Laat leeg als er niets bijzonders geldt.")
        + placeholder()

        + heading("Relatie tot de paved road en de architectuurprincipes")
        + guidance("Welke eisen hierboven al volgen uit de paved road, de "
                   "architectuurprincipes of geldende regelgeving. Verwijs "
                   "ernaar in plaats van ze over te schrijven: wat je "
                   "overschrijft, veroudert hier.")
        + content_table(["Eis", "Volgt uit", "Verwijzing"], rows=3)

        + heading("Afwijkingen van bestaande kaders")
        + guidance("Waar een eis niet strookt met de paved road of een "
                   "principe. Elke afwijking hier moet leiden tot een "
                   "architectuurbeslissing of een vastgelegde uitzondering — "
                   "benoem welke.")
        + content_table(["Eis", "Wijkt af van", "Waarom nodig",
                         "Beslissing of uitzondering"], rows=3)

        + heading("Tegenstrijdigheden tussen eisen")
        + guidance("Eisen die elkaar in de weg zitten — een prestatie-eis "
                   "tegenover een beveiligingseis, een beschikbaarheidseis "
                   "tegenover een kostenkader. Strijk ze niet glad: leg de "
                   "afweging voor aan de stakeholders en noteer wie hem heeft "
                   "gemaakt.")
        + content_table(["Eis", "Botst met", "Afweging", "Wie besliste"],
                        rows=3)

        + heading("Openstaande punten")
        + guidance("Kwaliteitskenmerken waarvoor de norm nog niet bekend is, "
                   "met de partij die hem moet leveren en de datum waarop dat "
                   "moet lukken. Een lege sectie hierboven zonder vermelding "
                   "hier leest als 'geen eisen', en dat is zelden waar.")
        + content_table(["Onderwerp", "Wat ontbreekt", "Wie levert",
                         "Uiterlijk"], rows=3)

        + heading("Gereed wanneer")
        + checklist([
            "Elke eis is meetbaar, met de omstandigheden erbij.",
            "Van elke eis is de herkomst bekend.",
            "Van elke eis staat vast voor welke use cases of onderdelen hij "
            "geldt.",
            "Alle kwaliteitskenmerken zijn langsgelopen; wat niet geldt, staat "
            "als openstaand of is bewust weggelaten.",
            "Wat al uit de paved road of de principes volgt, is een verwijzing "
            "en geen herhaling.",
            "Elke afwijking van een bestaand kader leidt tot een beslissing of "
            "een uitzondering.",
            "Tegenstrijdigheden zijn voorgelegd en belegd, niet gladgestreken.",
        ])
    )


BUILDERS = {
    "architectuuropdracht": architectuuropdracht,
    "architectuurvisie": architectuurvisie,
    "architectuurprincipes": architectuurprincipes,
    "architectuur-werkafspraken": architectuur_werkafspraken,
    "paved-road": paved_road,
    "architectuurmodel": architectuurmodel,
    "architectuurbeslissingen": architectuurbeslissingen,
    "migratiescenario": migratiescenario,
    "reviewresultaten": reviewresultaten,
    "use-casemodel": use_casemodel,
    "use-casespecificatie": use_casespecificatie,
    "aanvullende-specificaties": aanvullende_specificaties,
}

# Werkproducten uit de RDF die bewust geen Word-sjabloon krijgen.
NO_TEMPLATE = {
    "architectuurrepository": "een vindplaats, geen document",
}


def main(argv: list[str]) -> None:
    force = "--force" in argv
    wanted = [a for a in argv if not a.startswith("-")]

    products = _method.load()

    missing = set(BUILDERS) - set(products)
    if missing:
        raise SystemExit(f"niet in de RDF gevonden: {sorted(missing)}")

    unknown = set(wanted) - set(BUILDERS)
    if unknown:
        raise SystemExit(f"onbekend werkproduct: {sorted(unknown)}")

    extra = set(products) - set(BUILDERS) - set(NO_TEMPLATE)
    if extra:
        print(f"let op: werkproduct zonder sjabloon: {sorted(extra)}")

    created, skipped = 0, 0
    for slug in wanted or BUILDERS:
        target = HERE / f"{slug}.docx"
        if target.exists() and not force:
            skipped += 1
            continue
        wp = products[slug]
        build(
            source=STYLE,
            target=target,
            body_xml=BUILDERS[slug](wp),
            footer_label=wp.name,
        )
        action = "overschreven" if force else "aangemaakt"
        print(f"{action}: {slug}.docx  ({wp.name})")
        created += 1

    if skipped:
        print(f"{skipped} sjabloon(en) overgeslagen omdat ze al bestaan; "
              f"gebruik --force om ze terug te zetten naar de gegenereerde versie.")
    if not created and not skipped:
        print("niets te doen")


if __name__ == "__main__":
    main(sys.argv[1:])
