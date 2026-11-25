# expect: dcterms:license
# The dataset under another licence than the inherited CC BY-NC-SA 4.0 (row 51).
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX org: <http://www.w3.org/ns/org#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX eusex: <http://publications.europa.eu/resource/authority/human-sex/>
PREFIX oly: <https://w3id.org/olympic-lod/ontology#>

DELETE WHERE { <https://w3id.org/olympic-lod/tokyo2020/dataset> dcterms:license ?l } ;
INSERT DATA { <https://w3id.org/olympic-lod/tokyo2020/dataset> dcterms:license <https://creativecommons.org/licenses/by/4.0/> }
