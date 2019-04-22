import os
import sys
import django
import random
import urllib3
import argparse
import requests
import configparser
import elasticsearch.helpers

from requests.auth import HTTPBasicAuth
from string import ascii_letters, digits
from elasticsearch import Elasticsearch, RequestsHttpConnection


BASEURL = 'http://localhost:8000'
API_VERSION = 'v1'
API_USER = 'admin'
API_PASS = 'na05bi98'

LABELS_PROPERTIES = {
        'Documento': {
            'Precedente': (None, 'p', '#e5c494', '#ffffff'),
            'Doutrinador': (None, 'd', '#ee3720', '#ffffff'),
            'Ref. Legislativa': (None, 'r', '#2ca014', '#ffffff'),
            'Pessoa': ('shift', 'p', '#eea420', '#ffffff')
        },
        'Precedente': {
            'Número': (None, 'n', '#9b59b6', '#ffffff'),
            'Origem': (None, 'o', '#3498db', '#ffffff'),
            'Tipo': (None, 't', '#95a5a6', '#ffffff'),
            'Relator': (None, 'r', '#e74c3c', '#ffffff'),
            'Data de Julgamento': (None, 'd', '#34495e', '#ffffff'),
            'Data de Publicação': (None, 'p', '#2ecc71', '#ffffff'),
            'Corte': (None, 'c', '#dbc256', '#ffffff'),
            'Classe - Recursal': ('shift', 'r', '#890f63', '#ffffff'),
            'Classe - Constitucional': ('shift', 'c', '#890f63', '#ffffff'),
            'Classe - Writ': ('shift', 'w', '#890f63', '#ffffff'),
            'Classe - Penal originária': ('shift', 'p', '#890f63', '#ffffff'),
            'Classe - Súmula': ('shift', 's', '#890f63', '#ffffff'),
            'Classe - Outros': ('shift', 'o', '#890f63', '#ffffff'),
        },
        'Doutrinador': {
            'Autor principal': (None, 'a', '#66c2a5', '#ffffff'),
            'Coautor': (None, 'c', '#fc8d62', '#ffffff'),
            'Título da obra': (None, 't', '#8da0cb', '#ffffff'),
            'Ano de publicação': (None, 'n', '#e78ac3', '#ffffff'),
            'Editora': (None, 'e', '#a6d854', '#ffffff'),
            'Veículo': (None, 'v', '#ffd92f', '#ffffff'),
            'Não-autor': ('shift', 'a', '#e5c494', '#ffffff'),
        }
}

connection = Elasticsearch([{'host': 'aplcldrjvpr0017.acad.fgv.br', 'port': 9200}],
                           connection_class=RequestsHttpConnection,
                           http_auth=('admin', 'h1dr4!sen!2'),
                           use_ssl=True,
                           verify_certs=False,
                           timeout=180)

def setup_environment():
    """
    Setup the module path for proper import as well as the Django's environment
    configurations.
    """
    sys.path.append(os.path.abspath('../../app'))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    django.setup()

def parse_command_line_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotator', help='annotator unique identifier', required=True)
    cli = parser.parse_args()

    return cli

def create_user(username, password):
    """
    Create Django User and return the tuple containing the name and it's id
    """
    from django.contrib.auth.models import User
    user = User.objects.create_user(username, password=password)
    user.is_superuser=True
    user.is_staff=True
    user.save()

    return (user.id, user.username)

def generate_password(password_length=12):
    """
    Generate random password given a desired length.
    """
    chars = ascii_letters + digits
    
    return ''.join(random.choice(chars) for _ in range(password_length))

def create_project(owner, project_type=None):
    """
    Making an API call to the /projects endpoint to create a Project resource.
    
    The Project is associated to an existing User. 
    
    This function returns the Project's id for the next step of the pipeline.
    """
    endpoint = '{0}/{1}/{2}'.format(BASEURL, API_VERSION, 'projects')

    project_type = project_type if project_type else 'Documentos'

    payload = {
        'name': '{0} - {1}'.format(project_type, owner),
        'description': 'Insert description here',
        'project_type': 'SequenceLabeling',
        'guideline': 'Insert guideline here',
        'resourcetype': 'SequenceLabelingProject',
        'users': [owner]
    }
   
    response = requests.post(endpoint, data=payload, auth=HTTPBasicAuth(API_USER, API_PASS))

    if response.status_code >= 400:
        print(response.status_code)
        raise Exception('an error has ocurred when processing the request')
    else:
        response_as_json = response.json()
        project_id = response_as_json.get('id')

    return project_id

def retrieve_documents_for_annotator(annotator_id=None):
    """
    Query the elasticsearch and retrieve the documents separated for a given annotator.
    
    The data is returned in the proper format for the next stages of the pipeline.
    """
    if annotator_id:
        query = { "query": { "match_all": {}}}  # we need to decide how we're gonna query for this
    else:
        query = { "query": { "match_all": {}}}
    
    urllib3.disable_warnings()

    resultset = elasticsearch.helpers.scan(connection, query, 
                                            index='annotation_test_index', request_timeout=60)
    
    return [{'text': document['_source']['raw_text']} for document in resultset]

def create_documents_and_associate_to_project(project_id, payload=None):
    """
    Receives an parsed payload and create a Document object associated to an existing
    Project.
    """
    from server.models import Project
    from django.shortcuts import get_object_or_404
    project = get_object_or_404(Project, pk=project_id)
    storage = project.get_storage([payload])
    storage.save('felipe')  # what's the point of the user being passed as well?

def create_project_labels(project_id, project_type='Documento'):
    """
    Giving a certain set of properties, create Labels to an existing Project.
    """
    from server.models import Project, Label
    from django.shortcuts import get_object_or_404
    project = get_object_or_404(Project, pk=project_id)
    labels = LABELS_PROPERTIES[project_type]
    for key, value in labels.items():
        label = Label.objects.create(text=key, prefix_key=value[0], suffix_key=value[1], project=project, 
                                     background_color=value[2], text_color=value[3])
        label.save()

def run_pipeline_for(username):
    password = generate_password(password_length=6)
    print(username, password)
    _, user = create_user(username, password)
    project_id = create_project(owner=user)

    payload = retrieve_documents_for_annotator(annotator_id=user)
    create_documents_and_associate_to_project(project_id, payload)
    create_project_labels(project_id)

if __name__ == '__main__':
    setup_environment()
    cli = parse_command_line_arguments()
    username = cli.annotator
    run_pipeline_for(username)
