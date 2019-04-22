import os
import sys
import django
import requests

from requests.auth import HTTPBasicAuth

sys.path.append(os.path.abspath('../../app'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from server.models import Project
from django.shortcuts import get_object_or_404

# {{ [...text].slice(r.start_offset, r.end_offset).join(\'\') }}

BASEURL = 'http://localhost:8000'
API_VERSION = 'v1'

def create_project():
    endpoint = 'projects'

    payload = {
        'name': 'API_Project 2',
        'description': 'Automate project creation',
        'project_type': 'SequenceLabeling',
        'guideline': 'Im lazy...',
        'resourcetype': 'SequenceLabelingProject',
        'users': ['admin']
    }

    r = requests.post('{0}/{1}/{2}'.format(BASEURL, API_VERSION, endpoint),
                      data=payload, auth=HTTPBasicAuth('admin', 'na05bi98'))
    # print(r.text)  # the respone contains the id of the created resource

def create_documents_into_project(project_id, payload=None):
    project = get_object_or_404(Project, pk=project_id)
    storage = project.get_storage(payload)
    storage.save('admin')
    print('did it work?')
    
if __name__ == '__main__':
    
    # payload = [[{'text': 'Links'}, {'text': 'https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html'}, {'text': 'https://docs.aws.amazon.com/pt_br/AWSCloudFormation/latest/UserGuide/aws-properties-dynamodb-keyschema.html'}, {'text': 'https://docs.aws.amazon.com/pt_br/AWSCloudFormation/latest/UserGuide/aws-properties-dynamodb-keyschema.html'}, {'text': 'https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GettingStarted.Python.html'}, {'text': 'https://gist.githubusercontent.com/ServerlessBot/7618156b8671840a539f405dea2704c8/raw/bfc213d5b20ad0192217d5035ff526792535bdab/IAMCredentials.json'}]]
    
    # create_documents_into_project(project_id=4, payload=payload)
    create_project()
