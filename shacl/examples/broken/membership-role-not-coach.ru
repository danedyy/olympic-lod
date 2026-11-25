# expect: org:role
# A coaching role with an official's function, Judge (row 19).
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX org: <http://www.w3.org/ns/org#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX eusex: <http://publications.europa.eu/resource/authority/human-sex/>
PREFIX oly: <https://w3id.org/olympic-lod/ontology#>

DELETE WHERE { <https://w3id.org/olympic-lod/tokyo2020/id/membership/1378828-egy-fbl> org:role ?r } ;
INSERT DATA { <https://w3id.org/olympic-lod/tokyo2020/id/membership/1378828-egy-fbl> org:role <https://w3id.org/olympic-lod/scheme/function/judge> }
