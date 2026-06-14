workspace "MVA — Architecture Definition" {

  model {
    gebruiker = person "Eindgebruiker" "Voert bedrijfsprocessen uit"
    beheerder = person "Beheerder" "Configureert het platform"

    systeem = softwareSystem "Systeem in scope" "COTS-platform" {
      portaal   = container "Portaal / UI" "Self-service voor eindgebruikers\n✔ Paved Road" "SaaS Web"
      cots_a    = container "COTS Pakket A" "Primaire functionaliteit\nbijv. ERP / Finance · ✔ Paved Road" "SaaS Enterprise"
      cots_b    = container "COTS Pakket B" "Ondersteunende functionaliteit\nbijv. CRM / Service · ✔ Paved Road" "SaaS"
      integratie = container "Integratie-laag" "Orkestreert berichten\ntussen containers en externe systemen\n✔ Paved Road" "API Gateway / iPaaS"

      portaal    -> cots_a    "Haalt data op" "REST API"
      cots_a     -> integratie "Publiceert events" "CloudEvents"
      cots_b     -> integratie "Ontvangt events" "CloudEvents"
    }

    idp = softwareSystem "Identity Provider" "SSO · bijv. Entra ID" "External,PavedRoad"
    obs = softwareSystem "Monitoring & Logging" "Datadog / Splunk · SLA-bewaking" "External,PavedRoad"
    bron = softwareSystem "Extern bronsysteem" "Levert of ontvangt data" "External"

    gebruiker  -> portaal    "Gebruikt" "HTTPS"
    beheerder  -> cots_a     "Configureert" "Admin-console"
    portaal    -> idp        "Authenticeert via" "OIDC"
    integratie -> bron       "Synchroniseert" "REST / Event"
    obs        -> cots_a     "Observeert" "Metrics / Logs"
    obs        -> cots_b     "Observeert" "Metrics / Logs"
  }

  views {
    container systeem "Containers" {
      include *
      autoLayout
    }
    
    styles {
      element "Person" {
        shape Person
        background #08427b
        color #ffffff
        fontSize 13
      }
      element "Software System" {
        background #1168bd
        color #ffffff
        fontSize 13
      }
      element "Container" {
        background #438dd5
        color #ffffff
        fontSize 12
      }
      element "External" {
        background #999999
        color #ffffff
        fontSize 12
      }
      element "PavedRoad" {
        background #0f6e63
        color #ffffff
        fontSize 12
      }
      element "Governance" {
        background #4b3f9e
        color #ffffff
        fontSize 12
      }
      element "Driver" {
        background #bb7a16
        color #ffffff
        fontSize 12
      }
      element "OffRoad" {
        background #c47d0e
        color #ffffff
        fontSize 12
      }
      element "Decision" {
        background #1a5698
        color #ffffff
        fontSize 12
      }
      relationship "Relationship" {
        fontSize 11
        color #524d42
      }
    }

  }
}