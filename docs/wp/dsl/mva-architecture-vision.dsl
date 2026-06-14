workspace "MVA — Architecture Vision" {

  model {
    gebruiker  = person "Eindgebruiker" "Voert primaire bedrijfsprocessen uit"
    beheerder  = person "Beheerder" "Configureert en beheert het platform"

    systeem = softwareSystem "Systeem in scope" "Het te configureren COTS-platform\n[Software System]"

    idp      = softwareSystem "Identity Provider" "SSO · bijv. Entra ID / Okta" "External,PavedRoad"
    bron     = softwareSystem "Bronsysteem" "Levert of ontvangt data" "External"
    platform = softwareSystem "Cloud Platform" "Paved Road · bijv. Azure / AWS · EU-regio" "External,PavedRoad"

    gebruiker -> systeem "Gebruikt" "HTTPS / SSO"
    beheerder -> systeem "Configureert" "Admin-console"
    systeem   -> idp     "Authenticeert via" "OIDC / SAML 2.0"
    systeem   -> bron    "Wisselt data uit met" "REST / Event"
    platform  -> systeem "Host" "Cloud-infra"
  }

  views {
    systemContext systeem "Context" {
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