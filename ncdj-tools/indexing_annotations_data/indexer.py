import os
import sys
import json
import django
import hashlib
import urllib3


sys.path.append(os.path.abspath('../../app'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from server.models import Project, SequenceLabelingProject,\
Label, SequenceAnnotation, Document

from elasticsearch import Elasticsearch, RequestsHttpConnection

def parse_id_elasticsearch_from_text(text):
    last_line = text.split('\n')[-1]
    id_ = last_line.split(': ')[-1]

    return id_

def update_data_structure(annotations):
    data = {}
    for annotation in annotations:

        document = annotation.document
        project = document.project
        user = project.users.exclude(username__in=['admin', 'carla']).first()

        text = annotation.document.text
        term = text[annotation.start_offset:annotation.end_offset]
        term = term.strip()

        id_ = hashlib.sha256(term.encode('utf-8')).hexdigest()
        id_elasticsearch = parse_id_elasticsearch_from_text(document.text)

        if id_ not in data:
            data[id_] = {'present_in': [(user.username, id_elasticsearch, (str(annotation.start_offset), str(annotation.end_offset)))],
                       'label': annotation.label.text,
                       'text': term,
                       'version': 1}
        else:
            data[id_]['present_in'].append((user.username, id_elasticsearch, (str(annotation.start_offset), str(annotation.end_offset))))
    return data

def update_elasticsearch_index(data):
    urllib3.disable_warnings()

    connection = Elasticsearch([{'host': 'aplcldrjvpr0017.acad.fgv.br', 'port': 9200}],
                               connection_class=RequestsHttpConnection,
                               http_auth=('admin', 'h1dr4!sen!2'),
                               use_ssl=True,
                               verify_certs=False,
                               timeout=180)

    for id_, payload in data.items():
        payload['label'] = payload['label'].lower()
        connection.index(index='annotations', doc_type='_doc', id=id_, body=payload)

if __name__ == '__main__':

    projects = Project.objects.all().filter(name__startswith='Documentos', name__endswith='[PRATICA_ETAPA1]')

    documents = Document.objects.all().filter(project__in=projects)

    labels = Label.objects.filter(project__in=projects, text__in=['Precedente', 'Doutrina'])

    annotations = SequenceAnnotation.objects.all().filter(document__in=documents, label__in=labels)

    data = update_data_structure(annotations)

    update_elasticsearch_index(data)

