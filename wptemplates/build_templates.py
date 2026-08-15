"""Genereert de werkproduct-sjablonen op basis van de RDF en de TOGAF-opbouw.

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

META = ["Onderwerp", "Opgesteld door", "Eigenaar", "Versie", "Datum", "Status"]


def preamble(wp: _method.WorkProduct, meta: list[str] = None) -> str:
    """Vaste opening: titel, metadata, en herkomst uit de RDF."""
    return (
        title_block(wp.name, wp.practice, wp.brief)
        + meta_table(meta or META)
        + note(JUST_ENOUGH)
        + heading("Herkomst en gebruik")
        + guidance("Waar dit werkproduct in de werkwijze vandaan komt en wie "
                   "het verderop gebruikt. Deze tabel komt uit de methode zelf "
                   "en hoeft niet te worden ingevuld.")
        + provenance_table(wp.created_by, wp.read_by, wp.updated_by)
    )


# ==========================================================================
# Architectuuropdracht — TOGAF: Statement of Architecture Work (fase A)
# ==========================================================================
# Die deliverable legt vóór aanvang vast wat de opdracht is, wat erbuiten valt,
# wie waarover beslist en waarop wordt afgerekend. Precies wat de RDF noemt:
# aanleiding en doel, scope en uitsluitingen, toepasselijke principes, en wie
# welke beslissing mag nemen.
#
# Tabellen: bevoegdheden en op te leveren werkproducten zijn echte registers.
# Aanleiding, acceptatie en aanpak blijven lopende tekst.

def statement_of_architecture_work(wp):
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

        + heading("Toepasselijke architectuurprincipes")
        + guidance("Welke principes gelden binnen deze opdracht. Verwijs naar "
                   "de architectuurprincipes; herhaal ze hier niet.")
        + placeholder()

        + heading("Beslissingsbevoegdheden")
        + guidance("Wie binnen dit initiatief welke beslissing mag nemen, en "
                   "wanneer een keuze naar het Architectuurforum gaat.")
        + content_table(["Soort beslissing", "Wie beslist",
                         "Escalatie naar"], rows=4)

        + heading("Op te leveren werkproducten")
        + guidance("Welke werkproducten deze opdracht oplevert, wanneer ze "
                   "gereed zijn en wie ervoor tekent.")
        + content_table(["Werkproduct", "Gereed", "Eigenaar"], rows=4)

        + heading("Acceptatiecriteria")
        + guidance("Waaraan de opdrachtgever afleest dat de opdracht is "
                   "afgerond. Formuleer zo dat er achteraf geen discussie over "
                   "kan ontstaan.")
        + placeholder()

        + heading("Wijziging van de scope")
        + guidance("Wat er gebeurt als de scope tijdens de uitvoering "
                   "verandert: wie meldt, wie besluit, wat wordt vastgelegd.")
        + placeholder()

        + heading("Aanpak en doorlooptijd")
        + guidance("Op hoofdlijnen: welke stappen, welke doorlooptijd, welke "
                   "betrokkenheid van anderen nodig is.")
        + placeholder()

        + heading("Vaststelling")
        + guidance("Wie geeft de opdracht, wanneer, en waar is dat vastgelegd. "
                   "Vanaf dat moment ligt de scope vast.")
        + placeholder()

        + heading("Gereed wanneer")
        + checklist([
            "De opdrachtgever heeft de opdracht bevestigd.",
            "Scope en uitsluitingen laten geen ruimte voor discussie.",
            "De toepasselijke principes zijn benoemd.",
            "Van elke soort beslissing is bekend wie hem neemt.",
            "De acceptatiecriteria zijn toetsbaar geformuleerd.",
        ])
    )


# ==========================================================================
# Architectuurvisie — TOGAF: Architecture Vision (fase A)
# ==========================================================================
# Opent met de probleemstelling en de belanghebbenden met hun zorgen, maakt de
# doelstellingen toetsbaar, en beschrijft de beoogde situatie op hoofdlijnen —
# zonder al te ontwerpen.
#
# Tabellen: belanghebbenden en risico's blijven registers. Doelstellingen en
# vaststelling zijn narratief geworden.

def architecture_vision(wp):
    return (
        preamble(wp, ["Onderwerp", "Opgesteld door", "Opdrachtgever",
                      "Versie", "Datum", "Status"])
        + heading("Samenvatting")
        + guidance("De richting in maximaal tien regels, leesbaar voor wie de "
                   "rest niet leest. Schrijf deze sectie als laatste.")
        + placeholder()

        + heading("Aanleiding en probleemstelling")
        + guidance("Welke gebeurtenis, doelstelling of knelpunt dwingt tot "
                   "verandering. Beschrijf het probleem, nog niet de oplossing.")
        + placeholder()

        + heading("Doelstellingen")
        + guidance("Wat de verandering moet opleveren, in termen die achteraf "
                   "te toetsen zijn. Noem per doelstelling waaraan je afleest "
                   "dat ze gehaald is, en wanneer dat wordt vastgesteld.")
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
                   "die zorg krijgt.")
        + content_table(["Belanghebbende", "Belang", "Zorg", "Invloed"], rows=4)

        + heading("Beoogde situatie")
        + guidance("Hoe het landschap eruitziet als de verandering is "
                   "geslaagd. Beschrijf gedrag en samenhang op hoofdlijnen — "
                   "nog geen ontwerp.")
        + placeholder(2)

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
            "De afbakening laat geen ruimte voor discussie over scope.",
            "Belanghebbenden en hun zorgen zijn benoemd.",
            "Elke doelstelling heeft een criterium waaraan ze te toetsen is.",
            "Het restrisico is benoemd en aanvaard.",
            "Het besluit over de richting is vastgelegd in het Architectuurforum.",
        ])
    )


# ==========================================================================
# Architectuurprincipes — TOGAF: Architecture Principles (voorbereidende fase)
# ==========================================================================
# TOGAF beschrijft een principe in vier vaste delen: naam, stelling, rationale
# en implicaties. Rationale en implicaties zijn alinea's, geen celinhoud — het
# oude viercolomsrooster is daarom vervangen door een herhaalbaar blok per
# principe. Dat is meteen de grootste stijlwinst van deze omzetting.
#
# De RDF schrijft daarnaast een beperkte set voor (richtlijn vijf tot tien) en
# herziening via expliciete supersessie; beide krijgen een eigen sectie.

def architecture_principles(wp):
    return (
        preamble(wp)
        + heading("Reikwijdte")
        + guidance("Voor welke organisatieonderdelen, domeinen en soorten "
                   "keuzes deze principes gelden.")
        + placeholder()

        + heading("Principes")
        + guidance("Houd de set bewust klein — vijf tot tien — zodat de "
                   "principes te onthouden, toe te passen en te handhaven "
                   "blijven. Herhaal het blok hieronder per principe.")
        + subheading("Principe 1 — [ naam ]")
        + fld("Stelling",
              "de regel in één zin, in gebiedende wijs en zonder voorbehoud.")
        + fld("Rationale",
              "waarom dit de gewenste richting is, en wat er misgaat zonder.")
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

        + heading("Gereed wanneer")
        + checklist([
            "Elk principe heeft een stelling, een rationale en implicaties.",
            "De set is beperkt gebleven tot wat te onthouden is.",
            "Bij tegenstrijdige principes is bekend welke voorgaat.",
            "De afwijkroute is beschreven.",
            "Vervangen principes zijn zichtbaar als vervangen gemarkeerd.",
        ])
    )


# ==========================================================================
# Architectuur werkafspraken
# TOGAF: Organizational Model for Enterprise Architecture (voorbereidende fase)
#        + Implementation Governance Model (fase F)
# ==========================================================================
# Dit is de governance-tegenhanger die TOGAF wél kent. Het organisatiemodel
# levert de rollen, bevoegdheden en de governance- en ondersteuningsstrategie;
# het governancemodel levert de processen, de checkpoints en de succes- en
# faalcriteria. Samen dekken ze precies wat de RDF noemt: escalatiegrens,
# vergadercadans en objectives waaraan de governance zichzelf laat toetsen.
#
# Tabellen: de escalatiegrens en de objectives zijn echte registers — korte
# termen per cel. De rest is lopende tekst; het stuk moet kort en operationeel
# blijven, geen beleidsstuk.

def architecture_working_agreement(wp):
    return (
        preamble(wp)
        + heading("Reikwijdte")
        + guidance("Voor welke teams, domeinen en soorten beslissingen deze "
                   "afspraken gelden.")
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
            "De escalatieroute heeft een termijn.",
            "De cadans en de aanmeldroute liggen vast.",
            "Elke objective heeft een norm die te meten is.",
            "Vastgelegd is waar de governance zich buiten houdt.",
        ])
    )


# ==========================================================================
# Paved road
# TOGAF: Architecture Building Blocks (fase F) + Solution Building Blocks (G)
# ==========================================================================
# De paved road is een catalogus van vooraf goedgekeurde bouwstenen — dat is
# precies wat de TOGAF-bouwsteentemplates beschrijven: per bouwsteen de functie,
# de eigenschappen, de koppelvlakken en de afhankelijkheden.
#
# Tabellen: de catalogus zelf is het register en blijft. De statussen zijn
# narratief geworden — hun betekenis vraagt uitleg, geen cel. De rationale hoort
# hier niet: die staat in de architectuurbeslissing.

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
            "Een team kan zelf bepalen of het on-road of off-road zit.",
            "De off-road-procedure is beschreven.",
            "Vastgelegd is welke toetsing vervalt bij on-road gebruik.",
        ])
    )


# ==========================================================================
# Architectuurmodel — TOGAF: Architecture Definition Document (fase A t/m D)
# ==========================================================================
# De ADD beschrijft afbakening, uitgangspunten, de modellen zelf, het verschil
# met de huidige situatie en de vindplaats in de repository — en houdt de
# onderbouwing eruit. Dat sluit precies aan op de RDF: het model beschrijft de
# structuur, de rationale staat in architectuurbeslissingen.
#
# De uitwerking volgt het C4-model; de sectievolgorde loopt daarom van context
# via containers naar componenten.
#
# Tabellen: bouwstenen en koppelingen zijn registers. De niveaus zelf zijn
# narratief, met ruimte voor een diagram.

def architecture_model(wp):
    return (
        preamble(wp)
        + heading("Afbakening en detailniveau")
        + guidance("Wat wel en niet in dit model zit, en tot welk C4-niveau is "
                   "uitgewerkt. Werk alleen uit wat nodig is om de verandering "
                   "te begrijpen; wat ongewijzigd blijft, wordt niet opnieuw "
                   "beschreven.")
        + placeholder()

        + heading("Uitgangspunten en beperkingen")
        + guidance("Welke principes, eisen en gegeven beperkingen de vorm van "
                   "dit model bepalen.")
        + placeholder()

        + heading("Context")
        + guidance("De grenzen van de solution en haar omgeving: gebruikers, "
                   "aangrenzende systemen en externe partijen. Voeg het "
                   "contextdiagram hier in.")
        + placeholder(2)

        + heading("Containers")
        + guidance("De bouwstenen waaruit de solution bestaat en hun onderlinge "
                   "gegevensuitwisseling. Voor de meeste solutions is dit het "
                   "niveau waarop governance haar oordeel vormt. Voeg het "
                   "containerdiagram hier in.")
        + placeholder(2)

        + heading("Componenten")
        + guidance("Alleen uitwerken waar een architectuurbepalende eis, een "
                   "risico of een beslissing dat vereist. Laat deze sectie "
                   "anders leeg.")
        + placeholder()

        + heading("Bouwstenen")
        + guidance("Per bouwsteen waar hij verantwoordelijk voor is, waar zijn "
                   "grens ligt en wie hem bezit.")
        + content_table(["Bouwsteen", "Verantwoordelijkheid", "Grens",
                         "Eigenaar"], rows=5)

        + heading("Koppelingen")
        + guidance("Per koppeling wat er wordt uitgewisseld en wat er gebeurt "
                   "als de andere kant wegvalt.")
        + content_table(["Koppeling", "Met", "Wat wordt uitgewisseld",
                         "Gedrag bij uitval"], rows=4)

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
            "De systeemgrenzen zijn eenduidig.",
            "Elke bouwsteen heeft een verantwoordelijkheid en een eigenaar.",
            "Van elke koppeling is het gedrag bij uitval bekend.",
            "Het verschil met de huidige situatie is zichtbaar.",
            "De onderbouwing staat in architectuurbeslissingen, niet hier.",
            "Het model is opgenomen in de architectuurrepository.",
        ])
    )


# ==========================================================================
# Architectuurbeslissingen — traditie van Architecture Decision Records
# ==========================================================================
# TOGAF kent hiervoor geen eigen deliverable; de RDF zegt dat zelf ook expliciet.
# De opbouw volgt daarom de ADR-praktijk — context, opties, besluit, gevolgen —
# aangevuld met de koppeling aan de paved road, die in deze werkwijze bepaalt of
# een beslissing licht of volledig wordt uitgewerkt.
#
# Tabellen: de optievergelijking is een echt register en blijft. De rest is
# lopende tekst; een ADR is een leesstuk.

def architecture_decisions(wp):
    return (
        preamble(wp, ["Nummer en titel", "Opgesteld door", "Beslisser",
                      "Versie", "Datum", "Status"])
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
            "Het aanvaarde nadeel is benoemd.",
            "Duidelijk is of de keuze on-road of off-road is.",
            "De beslisser is bevoegd volgens de werkafspraken.",
        ])
    )


# ==========================================================================
# Migratiescenario
# TOGAF: Architecture Roadmap (fase B) + Implementation and Migration Plan (E)
# ==========================================================================
# De roadmap ordent de verandering in transitiearchitecturen; het migratieplan
# onderbouwt de volgorde en de afhankelijkheden. De RDF scherpt dat aan: elk
# plateau is operationeel verdedigbaar, en de volgorde wordt langs vier lijnen
# onderbouwd — data, techniek, risico en niet-technische realiteit.
#
# Tabellen: een compacte plateau-overzichtstabel blijft, omdat een volgorde in
# één oogopslag afleesbaar moet zijn. De uitwerking per plateau is een
# herhaalbaar blok geworden: wat er werkt en wat tijdelijk parallel loopt vraagt
# zinnen, geen cellen. De onderbouwing van de volgorde is een eigen sectie met
# vier vaste velden.

def roadmap(wp):
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
            "De volgorde is onderbouwd, niet impliciet.",
            "Van elke tijdelijke voorziening staat vast wanneer ze verdwijnt.",
            "De afhankelijkheden tussen plateaus zijn benoemd.",
            "Het scenario sluit aan op de enterprise-brede horizons.",
        ])
    )


# ==========================================================================
# Reviewresultaten — TOGAF: Compliance Assessment (fase G)
# ==========================================================================
# De compliance assessment legt per geval vast wat is getoetst, waartegen, en
# met welk oordeel. De RDF vult in welke oordelen mogelijk zijn — conform, met
# condities, afgekeurd, of uitzondering toegestaan — en dat de resultaten over
# een periode worden opgeteld als signaal voor het bijstellen van de governance.
#
# Tabellen: bevindingen en acties zijn samengevoegd tot één register, zodat een
# bevinding en haar opvolging op één regel staan. De rest is lopende tekst.

def review_records(wp):
    return (
        preamble(wp, ["Getoetst object", "Getoetst door", "Beslisser",
                      "Versie", "Datum", "Status"])
        + heading("Wat is getoetst")
        + guidance("Het systeem, product, de leverancier, interface of het "
                   "besluit dat is beoordeeld. Benoem het zo dat er geen "
                   "verwarring over kan bestaan welk geval dit betreft.")
        + placeholder()

        + heading("Waaraan is getoetst")
        + guidance("Tegen welke paved-road-items, principes en drivers is "
                   "gehouden. Alleen de criteria die daadwerkelijk zijn "
                   "toegepast.")
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

        + heading("Gereed wanneer")
        + checklist([
            "Het getoetste object is eenduidig benoemd.",
            "De toegepaste criteria staan erbij.",
            "Er is één oordeel, met onderbouwing.",
            "Elke bevinding heeft een eigenaar en een termijn.",
            "De herbeoordelingsdatum ligt vast.",
        ])
    )


BUILDERS = {
    "statement-of-architecture-work": statement_of_architecture_work,
    "architecture-vision": architecture_vision,
    "architecture-principles": architecture_principles,
    "architecture-working-agreement": architecture_working_agreement,
    "paved-road": paved_road,
    "architecture-model": architecture_model,
    "architecture-decisions": architecture_decisions,
    "roadmap": roadmap,
    "review-records": review_records,
}

# Werkproducten uit de RDF die bewust geen Word-sjabloon krijgen.
NO_TEMPLATE = {
    "architecture-repository": "een vindplaats, geen document",
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
