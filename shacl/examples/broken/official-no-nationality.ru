# expect: dbo:nationality
# An official without a nationality (row 8).
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX org: <http://www.w3.org/ns/org#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX eusex: <http://publications.europa.eu/resource/authority/human-sex/>
PREFIX oly: <https://w3id.org/olympic-lod/ontology#>

DELETE WHERE { <https://w3id.org/olympic-lod/tokyo2020/id/person/1510602> dbo:nationality ?c }
