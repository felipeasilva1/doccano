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

from text_sweeper import to_sweep
from labels import LABELS_PROPERTIES

sys.path.append(os.path.abspath('../../app'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from server.models import Project, SequenceLabelingProject, Label

connection = Elasticsearch([{'host': 'aplcldrjvpr0017.acad.fgv.br', 'port': 9200}],
                           connection_class=RequestsHttpConnection,
                           http_auth=('admin', 'h1dr4!sen!2'),
                           use_ssl=True,
                           verify_certs=False,
                           timeout=180)

DATASET = 'data/df_14_mono_coleg.csv'

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

def create_project(owner, project_phase=None):
    """
    Creating an Project object using Doccano's assets.
    
    The Project is associated to an existing User. 
    
    This function returns the Project's id for the next step of the pipeline.
    """

    project_phase = project_phase if project_phase else 'Documentos'
    user = User.objects.all().filter(username=owner).first()
    admin = User.objects.all().filter(username='admin').first()

    payload = {
        'name': '{0} - {1}'.format(project_phase, owner),
        'description': 'Insert description here',
        'project_type': 'SequenceLabeling',
        'guideline': 'Insert guideline here',
    }

    project = SequenceLabelingProject.objects.create(name=payload['name'], description=payload['description'], 
                                     project_type=payload['project_type'], 
                                     guideline=payload['guideline'])

    project.users.add(user)
    project.users.add(admin)
    project.save()

    return project.id

def retrieve_documents_for_annotator(ids=None, annotator_id=None):
    """
    Query the elasticsearch and retrieve the documents separated for a given annotator.
    
    The data is returned in the proper format for the next stages of the pipeline.
    """
    
    urllib3.disable_warnings()

    resultset = []
    for id in ids:
        document = connection.get(index='stf_prod', doc_type='decisoes', id=id)
        resultset.append(document)

    doccano_documents = []
    for document in resultset:
        _, sigla, numero, _ = document['_id'].split('_')
        text = document['_source']['raw_text']
        is_monocratica = document['_source']['monocratica']
        text = to_sweep(text, sigla, numero, is_monocratica)[0]
        doccano_documents.append(text)

    return [{'text': document} for document in doccano_documents]

def create_documents_and_associate_to_project(project_id, owner, payload=None):
    """
    Receives an parsed payload and create a Document object associated to an existing
    Project.
    """
    project = get_object_or_404(Project, pk=project_id)
    storage = project.get_storage([payload])
    storage.save(owner)

def create_project_labels(project_id, project_type='Documento'):
    """
    Giving a certain set of properties, create Labels to an existing Project.
    """
    project = get_object_or_404(Project, pk=project_id)
    labels = LABELS_PROPERTIES[project_type]
    for key, value in labels.items():
        label = Label.objects.create(text=key, prefix_key=value[0], suffix_key=value[1], project=project, 
                                     background_color=value[2], text_color=value[3])
        label.save()

def run_pipeline_for(username):
    password = generate_password(password_length=6)
    print(username, password)
    user_id, user = create_user(username, password)
    project_id = create_project(owner=user)

    ids = read_csv(DATASET)
    payload = retrieve_documents_for_annotator(ids=ids, annotator_id=user)
    create_documents_and_associate_to_project(project_id, user, payload)
    create_project_labels(project_id)

def read_csv(filename):
    with open(filename, 'r') as fh:
        data = fh.readlines()
        data = [datum.split(',') for datum in data[1:]]
        data = [datum[1] for datum in data]

    return data

if __name__ == '__main__':
    # setup_environment()

    # from django.contrib.auth.models import User
    # from django.shortcuts import get_object_or_404
    # from server.models import Project, SequenceLabelingProject, Label

    cli = parse_command_line_arguments()
    username = cli.annotator
    run_pipeline_for(username)
