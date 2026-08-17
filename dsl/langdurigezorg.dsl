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

        # ==================================================================
        # DEPLOYMENT — Productie, on-premise private cloud op OpenStack
        # ==================================================================
        #
        # Alle eigen systemen draaien in een private cloud in eigen beheer,
        # opgebouwd uit uitsluitend open source componenten. De externe
        # systemen (COV, Zorgkantoorsysteem, Zorgdomein) zijn hier niet
        # geïnstantieerd: ze draaien bij derden en zijn alleen bereikbaar
        # via de egress-firewall, die als infrastructuurknoop is opgenomen.
        #
        # Modelleerkeuze: de Neutron-netwerkzones staan als broer van de
        # compute-nodes en niet eronder. Fysiek draaien de VM's uiteraard óp
        # de compute-nodes, maar de zone-indeling is wat het ontwerp stuurt;
        # het diagram volgt hier de logica van het netwerk, niet die van het
        # rack.

        productie = deploymentEnvironment "Productie" {

            deploymentNode "Datacenter Amersfoort" "Primaire locatie" "Eigen datacenter" {

                deploymentNode "OpenStack private cloud" "IaaS-laag in eigen beheer" "OpenStack 2024.1 (Caracal)" {

                    deploymentNode "Control plane" "Identiteit, netwerken, images en scheduling" "srv-ctrl-01 t/m srv-ctrl-03, Ubuntu 24.04 LTS" 3 {
                        openstackControl = infrastructureNode "Keystone / Neutron / Glance / Horizon" "OpenStack-besturing, in HA over drie nodes" "OpenStack 2024.1"
                    }

                    deploymentNode "Compute" "Draagt alle virtuele machines" "srv-comp-01 t/m srv-comp-08, Ubuntu 24.04 LTS + KVM" 8 {
                        novaCompute = infrastructureNode "Nova compute (KVM/libvirt)" "Hypervisorlaag" "QEMU/KVM"
                    }

                    # --- Netwerkzone: DMZ ---
                    deploymentNode "DMZ" "Van buiten bereikbare zone" "Neutron provider network" {

                        loadbalancer = infrastructureNode "HAProxy + Keepalived" "TLS-terminatie en verdeling over de webservers" "srv-lb-01 / srv-lb-02, Ubuntu 24.04 LTS"

                        deploymentNode "vm-web-01 / vm-web-02" "Webservers achter de load balancer" "Nova-instance, Ubuntu 24.04 LTS + nginx" 2 {
                            websiteInstance = softwareSystemInstance website
                        }
                    }

                    # --- Netwerkzone: applicatie ---
                    deploymentNode "Applicatiezone" "Interne zone, niet van buiten bereikbaar" "Neutron tenant network" {

                        deploymentNode "vm-planning-01 / vm-planning-02" "Cliëntenplanning" "Nova-instance, Ubuntu 24.04 LTS" 2 {
                            frontofficeInstance = softwareSystemInstance frontoffice
                        }

                        deploymentNode "vm-ecd-01 / vm-ecd-02" "Elektronisch cliëntendossier" "Nova-instance, Ubuntu 24.04 LTS" 2 {
                            ecdInstance = softwareSystemInstance ecd
                        }

                        deploymentNode "vm-crm-01" "Relatiebeheer" "Nova-instance, Ubuntu 24.04 LTS" {
                            crmInstance = softwareSystemInstance crm
                        }

                        deploymentNode "vm-bus-01 t/m vm-bus-03" "Integratieplatform, berichtenverwerking" "Nova-instance, Ubuntu 24.04 LTS + Apache Kafka + Apache Camel" 3 {
                            busInstance = softwareSystemInstance bus
                        }

                        deploymentNode "vm-idp-01 / vm-idp-02" "Authenticatie en autorisatie voor medewerkers" "Nova-instance, Ubuntu 24.04 LTS" 2 {
                            keycloak = infrastructureNode "Keycloak" "Identity provider, OIDC/SAML" "Keycloak 26"
                        }
                    }

                    # --- Netwerkzone: data ---
                    deploymentNode "Datazone" "Afgeschermde zone voor persistente opslag" "Neutron tenant network, geen egress" {

                        postgresCluster = infrastructureNode "PostgreSQL-cluster" "Eén primary en twee synchrone replica's, automatische failover via Patroni en etcd" "srv-pg-01 t/m srv-pg-03, Ubuntu 24.04 LTS, PostgreSQL 16 + Patroni" {
                            tags "Database"
                        }

                        backup = infrastructureNode "Back-up" "Continue WAL-archivering en dagelijkse volledige back-up" "srv-bck-01, pgBackRest"
                    }

                    # --- Netwerkzone: beheer ---
                    deploymentNode "Beheerzone" "Monitoring, logging en configuratiebeheer" "Neutron tenant network" {
                        monitoring = infrastructureNode "Prometheus / Grafana / Loki" "Metrieken, dashboards en logs" "vm-mon-01, Ubuntu 24.04 LTS"
                    }
                }

                cephCluster = infrastructureNode "Ceph-opslagcluster" "Blokopslag voor de Nova-instances en objectopslag voor documenten" "srv-ceph-01 t/m srv-ceph-05, Ubuntu 24.04 LTS, Ceph Reef" {
                    tags "Database"
                }

                egress = infrastructureNode "Egress-firewall" "Enige uitgaande route naar VECOZO en Zorgdomein, met mTLS" "srv-fw-01 / srv-fw-02, nftables + Suricata"
            }

            deploymentNode "Datacenter Apeldoorn" "Uitwijklocatie op 40 km afstand" "Eigen datacenter" {

                postgresStandby = infrastructureNode "PostgreSQL-standby" "Asynchrone streaming replica, handmatige promotie bij uitwijk" "srv-pg-dr-01, Ubuntu 24.04 LTS, PostgreSQL 16" {
                    tags "Database" "Failover"
                }

                cephMirror = infrastructureNode "Ceph-spiegel" "RBD-mirroring van de primaire opslag" "srv-ceph-dr-01 t/m srv-ceph-dr-03, Ceph Reef" {
                    tags "Database" "Failover"
                }
            }

            # --- Infrastructuurrelaties (niet afleidbaar uit de logische laag) ---
            loadbalancer -> websiteInstance "Verdeelt HTTPS-verkeer over" "HTTPS"

            frontofficeInstance -> postgresCluster "Leest en schrijft" "JDBC, poort 5432"
            ecdInstance         -> postgresCluster "Leest en schrijft" "JDBC, poort 5432"
            crmInstance         -> postgresCluster "Leest en schrijft" "JDBC, poort 5432"
            busInstance         -> postgresCluster "Leest en schrijft" "JDBC, poort 5432"

            ecdInstance -> egress "Koppelt uit naar VECOZO en Zorgdomein via" "mTLS"

            postgresCluster -> backup "Archiveert WAL en back-ups naar"
            postgresCluster -> postgresStandby "Repliceert naar" "PostgreSQL streaming replication"
            cephCluster     -> cephMirror      "Spiegelt naar" "Ceph RBD mirroring"
        }
    }

    views {

        systemLandscape "ClientenregistratieLandscape" {
            include *
        }

        # ==================================================================
        # DYNAMIC VIEW — use-caserealisatie op landschapsniveau
        # ==================================================================
        #
        # Scope is '*': de realisatie loopt dwars door meerdere systemen en
        # over de organisatiegrens heen, en past dus niet binnen één systeem.
        #
        # Structurizr nummert de interacties automatisch, in de volgorde
        # waarin ze hieronder staan. Die nummers verschijnen op de pijlen in
        # het GERENDERDE diagram, niet in deze DSL-tekst. Het commentaar boven
        # elke regel legt vast welk interactienummer bij welke stap uit de
        # use-casespecificatie hoort.

        dynamic * "UC01-Client-aanmelden" {
            title "Use-caserealisatie UC-01 - Cliënt aanmelden voor verpleeghuiszorg (online route)"

            # interactie 1 - stap 1: de aanvrager dient de aanmelding in
            aanvrager -> website "Meldt de cliënt aan via het online formulier"

            # interactie 2 - stap 2: de aanmelding komt op het integratieplatform
            website -> bus "Publiceert de aanmelding"

            # interactie 3 - stap 2
            bus -> frontoffice "Registreert de aanmelding"

            description "Realisatie van het hoofdscenario van UC-01 op landschapsniveau. De e-mailroute en de route via Zorgdomein zijn alternatieve scenario's en krijgen een eigen realisatie."
        }

        # ==================================================================
        # DEPLOYMENT VIEW — productie, on-premise OpenStack
        # ==================================================================

        deployment * "Productie" "Deployment-Productie" {
            include *
            description "Mapping van de eigen systemen op de on-premise private cloud: OpenStack over acht compute-nodes, PostgreSQL in een Patroni-cluster, Ceph als opslag en een uitwijklocatie in Apeldoorn."
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

            element "Deployment Node" {
                color #555555
                stroke #555555
                strokeWidth 4
            }
            element "Infrastructure Node" {
                shape RoundedBox
                color #555555
                stroke #555555
            }
            element "Failover" {
                opacity 60
            }
        }
    }
}
