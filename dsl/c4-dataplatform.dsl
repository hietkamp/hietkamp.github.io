workspace "Health Data Platform" "Generiek C4-model voor een health data platform" {

    model {
        # Actoren (level 1)
        patient      = person "Patiënt" "Gebruikt apparatuur en app" "Customer"
        careProvider = person "Zorgverlener" "Verleent zorg" "Staff"
        dataUser     = person "Datagebruiker" "Vraagt data op voor secundair gebruik"

        # Externe systemen (level 1)
        connectedDevices = softwareSystem "Medische apparatuur" "Sensoren en therapie-apparatuur" "Extern Systeem"
        sourceEhr        = softwareSystem "Bron EHR-systeem" "Levert transactielogs" "Extern Systeem"

        healthDataPlatform = softwareSystem "Health Data Platform" "Ingestie, CDS, klinische opslag, interoperabiliteit en analytics" {

            ingestionLayer = container "Streaming Ingestion Layer" "Neemt real-time en batchdata op" "Ingestielaag" "ServiceBus"

            streamProcessing = container "Stream Processing & Decision Engine" "Real-time verwerking en CDS" "Apache Flink / Spark" {
                cdsTriggers = component "Clinical Decision Support Triggers" "Genereert alerts"
            }

            clinicalCore = container "Clinical Data Repository" "Persistente klinische kern" "openEHR" "Database" {
                cdr        = component "Clinical Data Repository (CDR)" "Opslag klinische data" "" "Database"
                archetypes = component "Archetypes & Templates" "Klinische modellen"
            }

            interoperabilityLayer = container "Interoperability Layer" "Ontsluit data via standaard-API" "FHIR API Facade"

            analyticsEtl = container "Analytics & Research Hub" "Transformeert data voor analytics" "ETL pipeline"
            omopStore    = container "OMOP Datastore" "Analytics-/onderzoeksdata" "OMOP CDM" "Database"

            dataAccessGateway = container "Data Access Gateway" "Catalogus, dataverzoeken en autorisatie" "Datastation-rol"

            secureProcessingEnvironment = container "Beveiligde Verwerkingsomgeving (BVO)" "Isoleert verwerking van datagebruikers" "SPE" "Boundary"
        }

        # Relaties - Level 1 (System Context)
        patient           -> healthDataPlatform "Gebruikt"
        careProvider      -> healthDataPlatform "Gebruikt"
        connectedDevices  -> healthDataPlatform "Stuurt metingen"
        sourceEhr         -> healthDataPlatform "Stuurt transactielogs"
        dataUser          -> healthDataPlatform "Vraagt data op"

        # Relaties - Level 2 (Containers)
        connectedDevices -> ingestionLayer "Streamt data"
        sourceEhr        -> ingestionLayer "Levert logs"

        ingestionLayer   -> streamProcessing "Voedt real-time data"
        streamProcessing -> clinicalCore "Schrijft klinische data"
        streamProcessing -> interoperabilityLayer "Stuurt alerts (primair gebruik)"

        clinicalCore -> interoperabilityLayer "Ontsluit FHIR resources"
        clinicalCore -> analyticsEtl "Voedt ETL"
        analyticsEtl -> omopStore "Schrijft naar"

        interoperabilityLayer -> careProvider "Levert FHIR resources en alerts (primair gebruik)"
        interoperabilityLayer -> patient "Levert FHIR resources (primair gebruik)"

        dataUser -> dataAccessGateway "Doet dataverzoek (secundair gebruik)"
        dataAccessGateway -> secureProcessingEnvironment "Autoriseert verwerking (secundair gebruik)"
        secureProcessingEnvironment -> clinicalCore "Query (read-only, secundair gebruik)"
        secureProcessingEnvironment -> omopStore "Query (read-only, secundair gebruik)"
        secureProcessingEnvironment -> dataAccessGateway "Levert resultaat"
        dataAccessGateway -> dataUser "Levert antwoord (secundair gebruik)"
    }

    views {
        systemContext healthDataPlatform "Level1_SystemContext" {
            include *
            description "C4 Level 1 - System Context van het generieke Health Data Platform"
        }

        container healthDataPlatform "Level2_Containers" {
            include *
            description "C4 Level 2 - Container diagram van het generieke Health Data Platform"
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
