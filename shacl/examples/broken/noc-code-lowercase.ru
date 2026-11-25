# expect: org:identifier
# An IOC code in lower case (row 22).
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX org: <http://www.w3.org/ns/org#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX eusex: <http://publications.europa.eu/resource/authority/human-sex/>
PREFIX oly: <https://w3id.org/olympic-lod/ontology#>

DELETE DATA { <https://w3id.org/olympic-lod/tokyo2020/id/noc/kor> org:identifier "KOR" } ;
INSERT DATA { <https://w3id.org/olympic-lod/tokyo2020/id/noc/kor> org:identifier "kor" }
