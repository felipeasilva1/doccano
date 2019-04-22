import os
import sys
import django

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

def retrieve_annotated_text(label):
    if label == 'Precedente':
        label_id = 18
    elif label == 'Doutrinador':
        label_id = 19
    else:
        raise Exception('There is no such label for 2nd phase')
    
    objects = SequenceAnnotation.objects.all().filter(label=label_id)

    return [{'text': parse_annotation_and_get_payload(obj)} for obj in objects]

def parse_annotation_and_get_payload(annotation):
    document = get_object_or_404(Document, pk=annotation.document.id)
    text = document.text[annotation.start_offset:annotation.end_offset]

    return text

if __name__ == '__main__':
    setup_environment()
    from server.models import SequenceAnnotation, Document

    annotations = retrieve_annotated_text(label='Precedente')

    project_id = create_project('felipe', project_type='Precedente')

    create_project_labels(project_id, project_type='Precedente')

    create_documents_and_associate_to_project(project_id, annotations)
