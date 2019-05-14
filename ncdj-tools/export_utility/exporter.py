
import os
import sys
import json
import django
import argparse

# SETUP DJANGO ENVIRONMENT AND APP
sys.path.append(os.path.abspath('../../app'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.contrib.auth.models import User
from server.models import Document, Project, Label, SequenceAnnotation

BASEDIR='data/'

def parse_command_line_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotator', help='annotator id', required=True)
    parser.add_argument('--prefix', help='identification of doc type', required=True)
    parser.add_argument('--suffix', help='identification of phase', required=False)
    cli = parser.parse_args()

    return cli

def get_user(annotator_id):
    user = User.objects.filter(username=annotator_id).first()
    if not user:
        return None
    return user

def get_user_project(user, doc_type, phase=None):
    if phase:
        # retrieve project by the phase name
        project = Project.objects.filter(users__username=user, name__startswith=doc_type, name__endswith=phase)
    else:
        # retrieve project with no phase name
        project = Project.objects.filter(users__username=user, name__startswith=doc_type, name__endswith=user.username)

    return project.first() if project.count() == 1 else None  # no project or ambiguity in name

def get_documents_for_project(project):
    return Document.objects.filter(project=project).all()

def get_annotations_for_document(project, document):
    labels = Label.objects.filter(project=project)
    annotations = SequenceAnnotation.objects.filter(document=document, label__in=labels)

    return annotations

def parse_phase_from_project_name(name):
    components = name.split(' - ')
    if len(components) < 3:
        phase = 'original'
    else:
        _, _, phase = components

    return phase

def parse_id_from_document_text(text):
    last_line = text.split('\n')[-1]
    id_ = last_line.replace('id: ', '')

    return id_

def parse_annotation_and_get_payload(annotation):
    document = Document.objects.get(pk=annotation.document.id)
    text = document.text[annotation.start_offset:annotation.end_offset]

    return (annotation.label.text, annotation.start_offset, annotation.end_offset, text)

def run(id_, doc_type, phase=None):
    user = get_user(id_)
    project = get_user_project(user, doc_type=doc_type, phase=phase)
    phase = parse_phase_from_project_name(project.name)
    documents = get_documents_for_project(project)
    
    data = merge_documents_and_annotations(project, documents, doc_type)
    create_directories_structure(user, phase, project, data)

def merge_documents_and_annotations(project, documents, doc_type=None):
    output = {}
    for document in documents:
        annotations = get_annotations_for_document(project, document)
        document_payload = document.text
        if doc_type in ['Doutrinador', 'Precedente']:
            deserialized_meta = json.loads(document.meta)
            parent_document_id = deserialized_meta['parent_doc_id']
            parent_document = Document.objects.get(pk=parent_document_id)
            document_id = parse_id_from_document_text(parent_document.text)
        else:
            document_id = parse_id_from_document_text(document_payload)
        output[document_id] = {'text': document_payload, 'annotations': {}}
        parsed_annotations = [parse_annotation_and_get_payload(a) for a in annotations]
        for ann in parsed_annotations:
            label = ann[0]
            if label not in output[document_id]['annotations']:
                output[document_id]['annotations'][label] = []
            output[document_id]['annotations'][label].append(ann[1:])

    return output

def create_directories_structure(user, phase, project, data):
    for id_, payload in data.items():
        top_dir = os.path.join(BASEDIR, user.username, phase)
        fname = '{0}.json'.format(id_)
        if 'annotations' not in payload:
            return None
        annotations = payload['annotations']
        for annotation_type in annotations:
            filtered_annotations = annotations[annotation_type]
            dir_ = os.path.join(top_dir, annotation_type.lower())
            if not os.path.exists(dir_):
                os.makedirs(dir_)
            fullname = os.path.join(dir_, fname)
            with open(fullname, 'w') as fh:
                content = {'text': payload['text'], 'annotations': filtered_annotations}
                json.dump(content, fh)

if __name__ == '__main__':
    cli = parse_command_line_arguments()
    run(cli.annotator, cli.prefix, cli.suffix)
