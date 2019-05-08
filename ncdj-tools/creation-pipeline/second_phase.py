import os
import sys
import django
import argparse

from django.shortcuts import get_object_or_404

from first_phase import create_project, create_project_labels, \
        create_documents_and_associate_to_project 

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

def retrieve_annotated_text(label, annotator):
    user = User.objects.filter(username=annotator).first()
    project = Project.objects.all().filter(users__username=user).first()
    documents = Document.objects.all().filter(project=project)
    label = Label.objects.all().filter(text=label, project=project).first()
    objects = SequenceAnnotation.objects.all().filter(document__in=documents, label=label)

    return [{'text': parse_annotation_and_get_payload(obj)} for obj in objects]

def parse_annotation_and_get_payload(annotation):
    document = get_object_or_404(Document, pk=annotation.document.id)
    text = document.text[annotation.start_offset:annotation.end_offset]

    return text

if __name__ == '__main__':
    setup_environment()
    from server.models import SequenceAnnotation, Document, Label, User, Project

    annotator = parse_command_line_arguments().annotator

    annotations_p = retrieve_annotated_text(label='Precedente', annotator=annotator)
    project_id_p = create_project(annotator, project_phase='Precedente')
    create_project_labels(project_id_p, project_type='Precedente')
    
    annotations_d = retrieve_annotated_text(label='Doutrinador', annotator=annotator)
    project_id_d = create_project(annotator, project_phase='Doutrinador')
    create_project_labels(project_id_d, project_type='Doutrinador')

    create_documents_and_associate_to_project(project_id_p, annotator, annotations_p)
    create_documents_and_associate_to_project(project_id_d, annotator, annotations_d)
