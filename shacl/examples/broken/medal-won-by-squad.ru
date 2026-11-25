# expect: oly:wonBy
# A medal counted for a Squad instead of the Team (row 39).
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX org: <http://www.w3.org/ns/org#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX eusex: <http://publications.europa.eu/resource/authority/human-sex/>
PREFIX oly: <https://w3id.org/olympic-lod/ontology#>

DELETE WHERE { <https://w3id.org/olympic-lod/tokyo2020/id/medal/1440267-arc-mixed-team> oly:wonBy ?t } ;
INSERT DATA { <https://w3id.org/olympic-lod/tokyo2020/id/medal/1440267-arc-mixed-team> oly:wonBy <https://w3id.org/olympic-lod/tokyo2020/id/team/kor-arc-men> }
