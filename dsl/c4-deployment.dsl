workspace "Voorbeeld – Aanvraagplatform" "Voorbeeld C4-deploymentdiagram conform Structurizr DSL, ter illustratie van Low-Level Design" {

    model {
        klant = person "Klant" "Vraagt een product of dienst aan via het portaal"

        aanvraagplatform = softwareSystem "Aanvraagplatform" "Verwerkt aanvragen van klanten" {
            webapp = container "Web Applicatie" "Levert de UI voor het aanvraagproces" "Node.js / React" {
                tags "Web"
            }
            api = container "API" "Verwerkt aanvraaglogica en validatie" "Java / Spring Boot" {
                tags "API"
            }
            database = container "Database" "Slaat aanvragen en klantgegevens op" "PostgreSQL" {
                tags "Database"
            }
        }

        # Logische relaties (container-niveau, C4 Level 2 — komen uit het High-/Low-Level Design)
        klant -> webapp "Gebruikt" "HTTPS"
        webapp -> api "Doet requests naar" "JSON/HTTPS"
        api -> database "Leest van en schrijft naar" "JDBC"

        # --- Deployment: Productie-omgeving ---
        productie = deploymentEnvironment "Productie" {

            # Client-zijde: hoort ook bij het deployment-diagram, net als in het officiële
            # Structurizr-voorbeeld (Big Bank plc, view "Deployment-Live") — het laat de volledige
            # keten zien van gebruikersapparaat tot en met de backend-infrastructuur.
            deploymentNode "Klant's computer" "" "Windows of macOS" {
                deploymentNode "Webbrowser" "" "Chrome, Firefox, Safari of Edge" {
                    webappBrowserInstance = containerInstance webapp
                }
            }

            deploymentNode "Azure" "" "Microsoft Azure – regio West Europe" {

                deploymentNode "Front-end zone" "Gedemilitariseerde netwerkzone (DMZ)" {
                    firewall = infrastructureNode "Firewall / WAF" "Filtert inkomend verkeer, blokkeert ongeautoriseerde toegang" "Azure Application Gateway + WAF" {
                        tags "Microsoft Azure - Application Gateways"
                    }
                }

                deploymentNode "Applicatiezone" "Interne netwerkzone" {

                    deploymentNode "App Service Plan" "Draait de webapplicatie en API" "Azure App Service, Premium v3" {
                        tags "Microsoft Azure - App Service Plans"

                        deploymentNode "app-web-***" "Web-instances achter de load balancer" "Azure App Service" 2 {
                            tags "Microsoft Azure - App Services"
                            webappInstance = containerInstance webapp
                        }

                        deploymentNode "app-api-***" "API-instances achter de load balancer" "Azure App Service" 3 {
                            tags "Microsoft Azure - App Services"
                            apiInstance = containerInstance api
                            properties {
                                "Autoscale" "2-6 instances, CPU > 70%"
                            }
                        }
                    }
                }

                deploymentNode "Data zone" "Afgeschermde netwerkzone voor dataopslag" {
                    primaryDatabaseServer = deploymentNode "Azure SQL Database – Primary" "Actieve, schrijfbare database" "Azure SQL Database" {
                        tags "Microsoft Azure - SQL Database"
                        databaseInstance = containerInstance database
                        properties {
                            "Regio" "West Europe"
                        }
                    }
                    secondaryDatabaseServer = deploymentNode "Azure SQL Database – Secondary" "Alleen-lezen geo-replica, voor failover" "Azure SQL Database" {
                        tags "Microsoft Azure - SQL Database" "Failover"
                        databaseFailoverInstance = containerInstance database {
                            tags "Failover"
                        }
                        properties {
                            "Regio" "North Europe"
                        }
                    }
                }
            }

            # Expliciete infrastructuurrelaties (niet automatisch afgeleid uit de logische laag)
            webappBrowserInstance -> firewall "Stuurt HTTPS-verkeer naar" "HTTPS"
            firewall -> webappInstance "Routeert toegestaan verkeer naar" "HTTPS"
            primaryDatabaseServer -> secondaryDatabaseServer "Repliceert data naar" "Azure SQL geo-replication"
        }

        # --- Deployment: Test-omgeving ---
        # Losse omgeving omdat de topologie afwijkt van productie: single-instance, geen WAF, geen geo-replicatie.
        test = deploymentEnvironment "Test" {

            deploymentNode "Azure" "" "Microsoft Azure – regio West Europe" {

                deploymentNode "App Service Plan" "Draait webapplicatie en API in één instance per container" "Azure App Service, Standard" {
                    tags "Microsoft Azure - App Service Plans"
                    webappInstanceTest = containerInstance webapp {
                        tags "Microsoft Azure - App Services"
                    }
                    apiInstanceTest = containerInstance api {
                        tags "Microsoft Azure - App Services"
                    }
                }

                deploymentNode "Azure SQL Database" "Single-instance, geen geo-replicatie" "Azure SQL Database, Basic tier" {
                    tags "Microsoft Azure - SQL Database"
                    databaseInstanceTest = containerInstance database
                }
            }
        }
    }

    views {
        deployment aanvraagplatform "Productie" "Deployment-Productie" {
            include *
            description "C4 deployment-diagram: mapping van de containers van het Aanvraagplatform op de Azure-infrastructuur in productie, inclusief client-zijde en database-failover."
        }

        deployment aanvraagplatform "Test" "Deployment-Test" {
            include *
            description "C4 deployment-diagram: vereenvoudigde topologie van de testomgeving, zonder WAF en zonder geo-replicatie."
        }

        styles {
            element "Web" {
                background #1168bd
                color #ffffff
            }
            element "API" {
                background #1168bd
                color #ffffff
            }
            element "Database" {
                shape cylinder
                background #1168bd
                color #ffffff
            }
            element "Infrastructure Node" {
                shape roundedbox
                background #999999
                color #ffffff
            }
            element "Failover" {
                background #6c6c6c
                color #ffffff
                opacity 60
            }
        }

        # Officiële Microsoft Azure-icon-theme (gebaseerd op de Azure Architecture Icons van Microsoft).
        # Elementen met een "Microsoft Azure - ..."-tag krijgen automatisch het bijbehorende icoon.
        # Eigen stijlen hierboven (Web/API/Database/Failover) blijven leidend voor tags die niet in de theme voorkomen.
        theme https://static.structurizr.com/themes/microsoft-azure-2021.01.26/theme.json
    }
}
