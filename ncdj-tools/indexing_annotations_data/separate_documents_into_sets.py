
import json
import urllib3
import numpy as np

from elasticsearch.helpers import scan
from elasticsearch import Elasticsearch, RequestsHttpConnection

def scan_index_for_documents_given_label(label):
    urllib3.disable_warnings()

    connection = Elasticsearch([{'host': 'aplcldrjvpr0017.acad.fgv.br', 'port': 9200}],
                               connection_class=RequestsHttpConnection,
                               http_auth=('admin', 'h1dr4!sen!2'),
                               use_ssl=True,
                               verify_certs=False,
                               timeout=180)

    results = scan(connection, query={"query": {"match": {"label": label}}}, index="annotations")

    output = []
    for datum in results:
        id_ = datum['_id']
        document = datum['_source']
        output.append((id_, document))

    return output

def create_tuple_of_sets(sets):
    output = []
    for i in range(52):
        output.append(sets[i:i+2])
    
    return output

def apply_transformation_to_sets_documets(sets):
    output = []
    for set_ in sets:
        transformed = [parse_document_and_extract_payload(document) for document in set_]
        output.append(transformed)

    return output

def parse_document_and_extract_payload(document):
    id_ = document[0]
    text = document[1]['text']

    return id_, text


if __name__ == '__main__':

    precedentes = scan_index_for_documents_given_label(label="precedente")
    precedentes = np.array(precedentes)
    offset = len(precedentes) - (len(precedentes) % 53)
    precedentes, remaining_set = precedentes[:offset], precedentes[offset:]
    precedentes_set = np.split(precedentes, 53)
    precedentes_set = create_tuple_of_sets(precedentes_set)
    precedentes_set = [apply_transformation_to_sets_documets(sets) for sets in precedentes_set]
    precedentes_set.append([precedentes_set[0][0], precedentes_set[-1][0]])

    with open('data/precedentes.json', 'w') as fh:
        json.dump(precedentes_set, fh)

    doutrinas = scan_index_for_documents_given_label(label="doutrina")
    doutrinas = np.array(doutrinas)
    offset = len(doutrinas) - (len(doutrinas) % 53)
    doutrinas, remaining_set = doutrinas[:offset], doutrinas[offset:]
    doutrinas_set = np.split(doutrinas, 53)
    doutrinas_set = create_tuple_of_sets(doutrinas_set)
    doutrinas_set = [apply_transformation_to_sets_documets(sets) for sets in doutrinas_set]
    doutrinas_set.append([doutrinas_set[0][0], doutrinas_set[-1][0]])
    with open('data/doutrinas.json', 'w') as fh:
        json.dump(doutrinas_set, fh)
