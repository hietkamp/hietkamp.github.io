workspace "Cliëntenregistratie" "System Landscape view, getransformeerd vanuit de container view: 'Cliëntenregistratie' is hier een group i.p.v. een software system." {

    model {

        # --- Persoon die buiten de group staat (externe aanvrager, zoals in het origineel) ---
        aanvrager = person "Aanvrager" "Cliënt, cliëntondersteuner of mantelzorger die zorg aanvraagt" "Customer"

        # --- Externe software systemen ---
        group "VECOZO" {
            cov = softwareSystem "COV" "Register van verzekerden en hun verzekeringsrecht."
            zorgkantoor = softwareSystem "Zorgkantoorsysteem" "Verantwoordelijk voor de registratie van een zorgtoewijzing en de wijzigingen daarop."
        }
        zd = softwareSystem "Zorgdomein" "Aanvraag vanuit een zorgverlener"

        # --- Voormalige containers + medewerkers, nu op landscape-niveau, ---
        # --- gegroepeerd binnen de group "Cliëntenregistratie" (was: software system) ---
        group "Cliëntenregistratie" {
            csb = person "Medewerker cliëntenbureau" "Verantwoordelijk voor aanmelding en registratie" "Staff"
            zorgbemiddelaar = person "Zorgbemiddelaar" "Verantwoordelijk voor de toetsing en matching van de aanmelding" "Staff"
            za = person "Medewerker zorgadministratie" "Verantwoordelijk voor de administratieve afhandeling." "Staff"

            website = softwareSystem "Website" "Biedt het online aanvraagformulier." 
            frontoffice = softwareSystem "Cliëntenplanning" "Beheer van aanmeldingen, wachtlijsten en beddencapaciteit." 
            ecd = softwareSystem "Elektronisch cliëntendossier" "Administratie en dossiervoering voor de verzorging van cliënten." 
            crm = softwareSystem "CRM" "Relatiebeheer." 
            bus = softwareSystem "Integratieplatform" "Platform voor de configuratie en uitvoering van integraties." "ServiceBus"
        }

        # --- Relaties (overgenomen van de container view, nu tussen software systemen) ---
        aanvrager -> csb "Meld cliënt aan voor verpleeghuiszorg via e-mail"
        aanvrager -> website "Meld cliënt aan voor verpleeghuiszorg"

        csb -> frontoffice "Ontvang, verifieer en registreer aanmelding"

        website -> bus "Publiceer aanmelding"
        bus -> frontoffice "Registreer aanmelding"

        frontoffice -> bus "Publiceer cliëntgegevens"
        bus -> ecd "Registreer cliëntgegevens"
        ecd -> cov "Controleer verzekeringsrecht"

        aanvrager -> zd "Meld cliënt aan voor verpleeghuiszorg"
        zd -> ecd "Registreer aanmelding"
        ecd -> zorgkantoor "Meld aanvang (AW35) of beëindiging (AW39) zorg"
        zorgkantoor -> ecd "Verstrek zorgtoewijzing (AW33)"

        ecd -> bus "Publiceer debiteurgegevens"
        bus -> crm "Registreer debiteurgegevens"

        zorgbemiddelaar -> frontoffice "Toets en match de zorgvraag met het aanbod"
        za -> ecd "Meld aanvang/beëindiging zorg"
    }

    views {

        systemLandscape "ClientenregistratieLandscape" {
            include *
        }

        styles {
          element "Element" {
                color #9a28f8
                stroke #9a28f8
                strokeWidth 7
                shape roundedbox
            }
            element "Person" {
                shape person
            }
            element "Database" {
                shape cylinder
            }
            element "Boundary" {
                strokeWidth 5
            }
            relationship "Relationship" {
                thickness 4
            }

            element "Customer" {
                color #08427b
                stroke #08427b
            }
            element "Staff" {
                color #006666
                stroke #006666
            }

            element "Software System" {
                shape RoundedBox
            }

            element "ServiceBus" {
                shape Pipe
            }
            element "Database" {
                shape Cylinder
                color #555555
                stroke #555555
            }

            relationship "Relationship" {
                style dashed
                color #555555
                thickness 4
            }
        }
    }
}
