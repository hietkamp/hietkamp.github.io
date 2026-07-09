workspace "Essence Architecture Method — Pages Generator" "C4 container-diagram van de RDF-naar-GitHub-Pages build- en publicatiepijplijn." {

    model {

        auteur = person "Methode-auteur" "Beheert de Essence-methode: past RDF-bestanden aan (practices, activiteiten, werkproducten, alphas, rollen, patronen)." "Person"
        bezoeker = person "Sitebezoeker" "Raadpleegt de Way-of-Working-website." "Person"

        pipeline = softwareSystem "Pages Generator" "Genereert een statische website uit RDF-bronbestanden die de Essence-methode beschrijven." {

            rdf = container "RDF-bronbestanden" "Ontologie (essence-language.owl), Essence Kernel en de method zelf: practices, activiteiten, werkproducten, alphas, rollen, patronen. Enige bron van waarheid voor inhoud." "essence/*.rdf, essence/method/**/*.rdf" "RDFStore"

            buildScript = container "Build-script" "Laadt alle RDF-bestanden in één rdflib.Graph, leidt per pagina een Jinja2-context af (naam, beschrijving, volgorde, in-/outputs, rollen) en rendert de HTML-pagina's." "Python 3.12 / rdflib / Jinja2" "BuildScript"

            templates = container "Templates" "Jinja2-sjablonen die uitsluitend de door build.py aangeleverde context-variabelen weergeven; bevatten geen methode-inhoud." "Jinja2 (.html.j2)" "Templates"

            site = container "Gegenereerde site" "Statische HTML/CSS/JS-output: index, practice-, activiteit- en werkproductpagina's. Wordt bij elke build volledig herbouwd." "Static HTML/CSS/JS (docs/)" "GeneratedSite"

            ciPipeline = container "CI/CD-pipeline" "Bouwt de site bij elke push naar main en publiceert het resultaat naar GitHub Pages." "GitHub Actions workflow (.github/workflows/build.yml)" "Pipeline"
        }

        repo = softwareSystem "GitHub-repository" "Versiebeheer van RDF, build-script, templates en workflow-configuratie." "External"
        pages = softwareSystem "GitHub Pages" "Hosting van de statische website." "External"

        # --- Relaties ---
        auteur -> rdf "Bewerkt practices, activiteiten, werkproducten, alphas, rollen, patronen"
        auteur -> repo "Commit & push wijzigingen naar main"

        repo -> ciPipeline "Triggert workflow bij push naar main / workflow_dispatch"

        ciPipeline -> rdf "Checkt repository-inhoud uit (incl. RDF)"
        ciPipeline -> buildScript "Installeert dependencies (rdflib, jinja2) en voert 'python build.py' uit"

        buildScript -> rdf "Leest en parsed alle .rdf-bestanden (rdflib.Graph)"
        buildScript -> templates "Rendert elke pagina met de bijpassende context-dict"
        buildScript -> site "Schrijft gegenereerde HTML naar docs/"

        ciPipeline -> site "Uploadt docs/ als Pages-artifact"
        ciPipeline -> pages "Deployt artifact (actions/deploy-pages)"

        bezoeker -> pages "Bekijkt de Way-of-Working-website"
        pages -> site "Serveert statische bestanden"
    }

    views {

        container pipeline "PipelineContainerView" {
            include *
            autoLayout lr
            description "Container-niveau overzicht: van RDF-bronbestanden tot gepubliceerde GitHub Pages-site."
        }

        styles {
            element "Element" {
                shape roundedbox
                color #ffffff
            }
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1a2f5a
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "RDFStore" {
                background #b45309
                shape cylinder
            }
            element "BuildScript" {
                background #27406b
            }
            element "Templates" {
                background #0f6e63
            }
            element "GeneratedSite" {
                background #4f46e5
            }
            element "Pipeline" {
                background #4f46e5
                shape pipe
            }
            relationship "Relationship" {
                thickness 2
            }
        }
    }
}
