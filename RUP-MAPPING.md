# Mapping: werkproducten methode ↔ RUP-templates

Bron RUP: <https://files.defcon.no/RUP/process/templates.htm> (RUP 2003.06.13, IBM Rational).
Bron methode: `essence/method/workproducts/*.rdf` (13 werkproducten, 4 practices).

Kolom **Fit**: `1:1` = zelfde artefact, `deel` = RUP dekt een deel of verspreidt het over meerdere templates, `gat` = geen RUP-template; alleen indirect af te leiden.

---

## 1. Overzichtstabel

| # | Werkproduct (NL) | Practice | RUP-template(s) | Fit |
|---|---|---|---|---|
| 1 | Architectuurvisie | Enterprise architectuur | [Vision](https://files.defcon.no/RUP/webtmpl/templates/req/rup_vision.htm) + [Business Architecture Document](https://files.defcon.no/RUP/webtmpl/templates/bm/rup_barchdoc.htm) §3 | deel |
| 2 | Paved road | Enterprise architectuur | [Design Guidelines](https://files.defcon.no/RUP/webtmpl/templates/environ/rup_desgd.htm) + [Programming Guidelines](https://files.defcon.no/RUP/webtmpl/templates/environ/rup_prggd.htm) | deel |
| 3 | Architectuurbeschrijving | Solution architectuur | [Software Architecture Document](https://files.defcon.no/RUP/webtmpl/templates/a_and_d/rup_sad.htm) | 1:1 |
| 4 | Architectuurbeslissingen | Solution architectuur | SAD §3 + §11; BAD §11 Architectural Trade-offs | gat |
| 5 | Migratiescenario | Solution architectuur | [Software Development Plan](https://files.defcon.no/RUP/webtmpl/templates/mgmnt/rup_sdpln.htm), [Deployment Plan](https://files.defcon.no/RUP/webtmpl/templates/deploy/rup_depln.htm) §3.2 | gat |
| 6 | Architectuurprincipes | Architectuursturing | [Design Guidelines](https://files.defcon.no/RUP/webtmpl/templates/environ/rup_desgd.htm) §2/§4; BAD §3 Architectural Drivers | deel |
| 7 | Architectuurrepository | Architectuursturing | [Configuration Management Plan](https://files.defcon.no/RUP/webtmpl/templates/cm_mgt/rup_cmpln.htm) (+ artefact Project Repository) | deel |
| 8 | Architectuur werkafspraken | Architectuursturing | [Development Case](https://files.defcon.no/RUP/webtmpl/templates/environ/wb_dvlcs.htm) | 1:1 |
| 9 | Reviewresultaten | Architectuursturing | Review Record (artefact, géén template); [Iteration Assessment](https://files.defcon.no/RUP/webtmpl/templates/mgmnt/rup_itass.htm), [Status Assessment](https://files.defcon.no/RUP/webtmpl/templates/mgmnt/rup_stass.htm) | deel |
| 10 | Architectuuropdracht | Architectuursturing | Vision §1.2, SDP, [Business Case](https://files.defcon.no/RUP/webtmpl/templates/mgmnt/rup_buscs.htm) | gat |
| 11 | Use-casemodel | Use cases | [SRS w/ Use-Cases](https://files.defcon.no/RUP/webtmpl/templates/req/rup_srsuc.htm) (Use-Case Model zelf heeft geen template) | deel |
| 12 | Use-casespecificatie | Use cases | [Use-Case Specification](https://files.defcon.no/RUP/webtmpl/templates/req/rup_ucspec.htm) (+ [informele variant](https://files.defcon.no/RUP/webtmpl/templates/req/ucspec_informal.htm)) | 1:1 |
| 13 | Aanvullende specificaties | Use cases | [Supplementary Specification](https://files.defcon.no/RUP/webtmpl/templates/req/rup_sspec.htm) | 1:1 |

---

## 2. Toelichting per werkproduct

### 1. Architectuurvisie → Vision + Business Architecture Document §3

RUP's **Vision** is productgericht: positioning, stakeholder-/userprofielen, product features, quality ranges. De architectuurvisie is richtinggevend: doel, scope, principes — vastgesteld vóór de keuzes. Bruikbare secties uit Vision: §2 Positioning (business opportunity, problem statement), §3.2 Stakeholder Summary, §6 Constraints, §7 Quality Ranges. Wat in Vision zit maar niet in de architectuurvisie hoort: §5 Product Features, §10 Documentation Requirements, appendix A Feature Attributes.

BAD **§3 Architectural Drivers** (goals vs. constraints) is inhoudelijk het dichtst bij het "gemotiveerde beeld van de gewenste richting".

### 2. Paved road → Design Guidelines + Programming Guidelines

**Design Guidelines** §2 (mapping design→implementatie, fault handling, persistence, transaction management, herbruikbare componenten/COTS) en §5 Mechanism Guidelines ("voor elk significant mechanisme een programmers' guide met interface en gebruiksinstructie") zijn functioneel wat de paved road doet: vooraf goedgekeurde bouwstenen met gebruiksaanwijzing.

Wat RUP mist: het **afwijkingspad**. De paved road heeft een expliciete route voor wie ervan afwijkt; RUP-guidelines kennen geen exception-mechanisme. Dichtstbijzijnde in RUP is Development Case §2.3.3 "Notes on Artifacts" (wat we níet gebruiken en waarom) — maar dat is procesniveau, geen technologiekeuze.

### 3. Architectuurbeschrijving → Software Architecture Document

Sterkste match van de hele set. SAD-structuur: §2 Architectural Representation, §4 Use-Case View, §5 Logical View (decompositie in subsystemen/packages, verantwoordelijkheden), §6 Process View, §7 Deployment View, §8 Implementation View (lagen), §9 Data View, §10 Size & Performance, §11 Quality.

"Bouwstenen, hun verantwoordelijkheden en grenzen, en hoe ze samenwerken" = SAD §5.1/§5.2 letterlijk. Let op: SAD is 4+1-views/UML; ons model is ArchiMate/C4. De sectiestructuur is overdraagbaar, de notatie niet.

### 4. Architectuurbeslissingen → gat

RUP kent geen ADR. Beslissingen zijn in RUP impliciet: de SAD *is* het vastleggen van "the significant architectural decisions which have been made" (SAD §1.1), maar zonder alternatieven, afweging of status per beslissing.

Deelbronnen:

- SAD §3 Architectural Goals and Constraints — de drivers waar de beslissing op antwoordt
- BAD §11 Architectural Trade-offs — "how the architecture supports each driver… pay special attention to conflicts"; het enige plek in RUP waar afweging expliciet wordt gevraagd
- [Risk List](https://files.defcon.no/RUP/webtmpl/templates/mgmnt/rup_rsklst.htm) — voor de risico's van een gekozen alternatief

ADR-elementen zonder RUP-tegenhanger: context, overwogen alternatieven, status (proposed/accepted/superseded), consequenties, datering per beslissing.

### 5. Migratiescenario → gat

RUP plant *iteraties van één project*, niet *stabiele tussentoestanden van een architectuur*. SDP en Iteration Plan geven cadans en mijlpalen; Deployment Plan §3.2 geeft een uitrolschema. Geen van drieën beschrijft een architectuurtoestand die op zichzelf houdbaar is.

Wel bruikbaar als bouwsteen: Deployment Plan §4 Resources (per tussentoestand: welke faciliteiten, hardware, deployment units nodig zijn).

### 6. Architectuurprincipes → Design Guidelines §2/§4 + BAD §3

**Design Guidelines §4 Architectural Design Guidelines**: "rules and recommendations for software architecture design… organized around the different architectural views. The rules mostly deal with decomposition." Dat is dichtbij, maar RUP-guidelines zijn prescriptief-technisch ("gebruik geen pointers in embedded real-time"), terwijl een principe richting geeft zonder detail voor te schrijven.

**BAD §3** onderscheidt goals (wens) en constraints (verplichting) — dat onderscheid is bruikbaar bij het formuleren van principes.

Wat RUP mist: rationale + implicaties per principe (TOGAF-vorm: statement / rationale / implications).

### 7. Architectuurrepository → Configuration Management Plan

RUP's **Project Repository** is een artefact zonder eigen template; het CM Plan beschrijft hem. Development Case §2.3.3 formuleert de vragen die de repository moet beantwoorden: "When do I release my artifact? Where do I put my newly created or modified artifact? Where do I find existing artifacts for the project?"

Verschil in scope: RUP's repository is projectgebonden, de architectuurrepository is organisatiebreed en langlevend.

### 8. Architectuur werkafspraken → Development Case

Verrassend sterke match. Development Case legt exact vast wat de werkafspraken vastleggen:

| Werkafspraken | Development Case |
|---|---|
| wie welke beslissing mag nemen | §4 Roles (mapping rollen ↔ functies in de organisatie) |
| welke review-zwaarte per geval | §2.3.2 kolom "Review Details" + §2.5 Review Procedures (Formal-External / Formal-Internal / Informal / None) |
| welk artefact wanneer verplicht is | §2.3.2 "How to use" per fase: Must / Should / Could / Won't |
| ritme van governance-interacties | §2.6 Sample Iteration Plans |
| escalatieroute | — (ontbreekt in RUP) |

De classificaties Must/Should/Could/Won't en de vier reviewniveaus zijn direct overneembaar.

### 9. Reviewresultaten → Review Record

RUP heeft het artefact [Review Record](https://files.defcon.no/RUP/process/artifact/ar_rvrec.htm) (Project Management-discipline) maar publiceert er géén template voor op de templates-pagina. Wel getemplate: **Iteration Assessment** en **Status Assessment** — beide periodiek/voortgangsgericht, niet per-geval-conformiteit.

Ons drieluik conform / met condities / toegestane uitzondering heeft geen RUP-equivalent; RUP-reviews zijn pass/fail per reviewniveau.

### 10. Architectuuropdracht → gat

TOGAF-begrip (Statement of Architecture Work), geen RUP-begrip. Verspreide dekking: Vision §1.2 Scope, Business Case (rechtvaardiging), SDP (aanpak, planning, resources), Development Case §4 (rollen/bevoegdheden). RUP heeft geen enkel document dat vóór het architectuurwerk scope + doel + beslissingsbevoegdheid samen vastlegt.

### 11. Use-casemodel → SRS w/ Use-Cases

RUP's **Use-Case Model** is een modelartefact (in Rose), geen document — vandaar geen template. Twee substituten:

- [SRS w/ Use-Cases](https://files.defcon.no/RUP/webtmpl/templates/req/rup_srsuc.htm) — bundelt use-caselijst + supplementary requirements
- Report [Use-Case Model Survey](https://files.defcon.no/RUP/process/reports/re_ucmsv.htm) — actoren + use cases met korte omschrijving; precies onze "naam + beoogd resultaat"

De systeemgrens-functie ("begrenst de omvang van het werk") komt in RUP terug via Vision §4.1 Product Perspective.

### 12. Use-casespecificatie → Use-Case Specification

1:1. RUP-structuur: §1 Brief Description, §2 Basic Flow of Events, §3 Alternative Flows (gegroepeerd per Area of Functionality), §4 Subflows, §5 Key Scenarios, §6 Preconditions, §7 Postconditions, §8 Extension Points, §9 Special Requirements, §10 Additional Information.

Dekt onze definitie volledig: hoofdscenario (§2), afwijkingen (§3/§4), voorwaarden (§6/§7), regels (§9). Er is ook een informele variant voor lichter gebruik.

### 13. Aanvullende specificaties → Supplementary Specification

1:1, inclusief de definitie: "captures the system requirements that are not readily captured in the use cases." RUP-indeling: §2 Functionality, §3 Usability, §4 Reliability, §5 Performance, §6 Supportability (= FURPS+), §7 Design Constraints, §8 Online Help, §9 Purchased Components, §10 Interfaces, §11 Licensing, §12 Legal, §13 Applicable Standards.

Onze drieslag kwaliteitseisen / wettelijke verplichtingen / ontwerpbeperkingen mapt op §3–§6 / §12–§13 / §7.

---

## 3. Omgekeerd: RUP-templates zonder tegenhanger in de methode

Relevant voor architectuurwerk, maar niet gemodelleerd:

| RUP-template | Waarom mogelijk relevant |
|---|---|
| [Glossary](https://files.defcon.no/RUP/webtmpl/templates/req/rup_gloss.htm) / [Business Glossary](https://files.defcon.no/RUP/webtmpl/templates/bm/rup_bgloss.htm) | begrippenkader ontbreekt als werkproduct |
| [Stakeholder Requests](https://files.defcon.no/RUP/webtmpl/templates/req/rup_stkreq.htm) | ruwe input vóór de architectuurvisie |
| [Risk List](https://files.defcon.no/RUP/webtmpl/templates/mgmnt/rup_rsklst.htm) | architectuurrisico's als eigen werkproduct |
| [Use-Case-Realization Specification](https://files.defcon.no/RUP/webtmpl/templates/a_and_d/rup_ucrs.htm) | brug use case → architectuurbeschrijving |
| [Business Architecture Document](https://files.defcon.no/RUP/webtmpl/templates/bm/rup_barchdoc.htm) | volledige EA-tegenhanger van de SAD; nu verdeeld over visie + model |
| [Target-Organization Assessment](https://files.defcon.no/RUP/webtmpl/templates/bm/rup_tarorgass.htm) | huidige-situatie-analyse vóór het migratiescenario |

---

## 4. Samenvatting

- **3 van 13** hebben een directe RUP-template: architectuurbeschrijving (SAD), architectuur werkafspraken (Development Case), use-casespecificatie + aanvullende specificaties (2 van de use-case-set) — feitelijk **4**.
- **6** zijn deels gedekt en kunnen sectiestructuur lenen.
- **3 gaten** zijn systematisch: architectuurbeslissingen, migratiescenario en architectuuropdracht zijn TOGAF/ADR-concepten die RUP niet kent. RUP legt de *uitkomst* van architectuurwerk vast (de SAD), niet de *besturing* ervan.
- Alle 4 werkproducten van de practice **Use cases** hebben goede RUP-dekking; de practice **Architectuursturing** het slechtst.
