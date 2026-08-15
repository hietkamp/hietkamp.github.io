# NOTICE — licenties en herkomst

Dit project bestaat uit twee soorten materiaal met elk hun eigen rechten. De `LICENSE` (GPLv3) in de root dekt **niet alles** in deze repository — dit bestand maakt het onderscheid expliciet.

## 1. Eigen werk (GPLv3)

Het build-script (`build.py`), de Jinja2-templates (`templates/`), de statische assets (`static/`), de werkproduct-sjabloongenerator (`wptemplates/`), en de inhoud van de **Essence Architecture Method** zelf (`essence/method/**` — de practices, activiteiten, werkproducten, rollen en patronen zoals wij die hebben ontworpen) zijn oorspronkelijk werk van dit project en vallen onder de [GNU General Public License v3.0](LICENSE).

De Essence Architecture Method is **onze eigen implementatie/toepassing**, gebouwd bovenop de Essence-taal en -kernel. Het is niet de OMG Essence-standaard zelf en claimt dat ook niet te zijn.

## 2. Essence Kernel en -taal (OMG-specificatie, niet GPL)

`essence/essence-language.owl` (de ontologie) en `essence/essence-kernel.rdf` (de Kernel: alpha's, states, activity spaces, competenties, checklist-items) implementeren het model uit clausule 8 van:

> **Essence – Kernel and Language for Engineering Methods**, versie 2.0 beta 2, OMG-documentnummer **ptc/25-05-01**, Object Management Group. Officiële specificatie: <https://www.omg.org/spec/Essence/>

Het model zelf — welke alpha's, states, activity spaces, competenties en checklist-items er zijn, en hoe die zich tot elkaar verhouden — is auteursrechtelijk beschermd door de Object Management Group en de overige rechthebbenden die in de specificatie staan vermeld (Copyright © 1997–2025 Object Management Group en anderen). De OMG-specificatie verleent zelf een licentie om er software op te baseren:

> *"...the owners of the copyright in this specification hereby grant you a fully-paid up, non-exclusive, nontransferable, perpetual, worldwide license (...) to use this specification to create and distribute software (...) that are based upon this specification..."*

Onder die voorwaarden bouwen wij `essence-kernel.rdf` en `essence-language.owl` als software die het Kernel-model in RDF uitdrukt. De herkomst staat ook machineleesbaar in het RDF-bestand zelf via `dcterms:source`.

**De omschrijvingsteksten zijn eigen werk, geen vertaling.** Alle namen en omschrijvingen in `essence-kernel.rdf` (`ess:name`, `ess:briefDescription`, `ess:description`) zijn in eigen Nederlandse bewoordingen geschreven — geen woordelijke vertaling van de Engelse specificatietekst. De Engelse brontekst van OMG staat niet (meer) in dit bestand; alleen het onderliggende model volgt de structuur van de specificatie. Deze teksten vallen daarom, net als de rest van ons eigen werk, onder GPLv3.

**De specificatie-PDF zelf wordt niet in deze repository gedistribueerd.** OMG's eigen voorwaarden staan herdistributie van het documentbestand alleen toe voor informatief gebruik en expliciet *niet* via plaatsing op een netwerkcomputer. Raadpleeg de volledige, actuele specificatie op <https://www.omg.org/spec/Essence/>.

## Samengevat

| Onderdeel | Licentie | Bron |
|---|---|---|
| `build.py`, `templates/`, `static/`, `wptemplates/` | GPLv3 | Dit project |
| `essence/method/**` (de Essence Architecture Method) | GPLv3 | Dit project — eigen implementatie, niet de OMG-standaard |
| `essence/essence-kernel.rdf`, `essence/essence-language.owl` — model/structuur | OMG-specificatielicentie (zie boven) | Model geïmplementeerd naar OMG ptc/25-05-01 |
| `essence/essence-kernel.rdf` — namen en omschrijvingsteksten (NL) | GPLv3 | Eigen bewoordingen, geen vertaling van de OMG-brontekst |
