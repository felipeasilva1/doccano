import os
import sys
import json
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
    parser.add_argument('--annotators', help='annotators file', required=True)
    parser.add_argument('--suffix', help='identification of phase', required=False)
    cli = parser.parse_args()

    return cli

def retrieve_annotated_text(label, annotator):
    user = User.objects.filter(username=annotator).first()
    if not suffix:
        project = Project.objects.all().filter(users__username=user,
                                               name='Documentos - {0}'.format(user.username)).first()
    else:
        project = Project.objects.all().filter(users__username=user,
                                               name='Documentos - {0} - {1}'.format(user.username, suffix)).first()

    documents = Document.objects.all().filter(project=project)
    label = Label.objects.all().filter(text=label, project=project).first()
    objects = SequenceAnnotation.objects.all().filter(document__in=documents, label=label)

    return [{'text': parse_annotation_and_get_payload(obj), 'meta': json.dumps({'parent_doc_id': obj.document.id})} for obj in objects]

def retrieve_annotated_text_from_parsed_content(annotator, sets_file):
    set1, set2 = sets_file.pop()
    set1.extend(set2)

    return [{'text': doc[1] or 'empty annotation', 'meta': json.dumps({'parent_doc_id': doc[0]})} for doc in set1]

def parse_annotation_and_get_payload(annotation):
    document = get_object_or_404(Document, pk=annotation.document.id)
    text = document.text[annotation.start_offset:annotation.end_offset]

    return text

def get_username_from(file_):
    with open(file_, 'r') as fh:
        data = fh.readlines()
        data = [datum[:-1] for datum in data[1:]]
        data = [datum.split(',') for datum in data if datum]
        data = [datum[1] for datum in data if datum]

    return data

if __name__ == '__main__':
    setup_environment()
    from server.models import SequenceAnnotation, Document, Label, User, Project

    cli = parse_command_line_arguments()
    annotators = cli.annotators
    suffix = cli.suffix

    with open('../indexing_annotations_data/data/doutrinas.json', 'r') as fh:
        d_sets = json.load(fh)

    with open('../indexing_annotations_data/data/precedentes.json', 'r') as fh:
        p_sets = json.load(fh)

    for annotator in get_username_from(annotators):
        # annotations_p = retrieve_annotated_text(label='Precedente', annotator=annotator)
        print('Creating projects for %s' % (annotator))
        annotations_p = retrieve_annotated_text_from_parsed_content(annotator=annotator, sets_file=p_sets)
        project_id_p = create_project(annotator, project_phase='Precedente', suffix=suffix)
        create_project_labels(project_id_p, project_type='Precedente')
        create_documents_and_associate_to_project(project_id_p, annotator, annotations_p)

        # annotations_d = retrieve_annotated_text(label='Doutrina', annotator=annotator)
        annotations_d = retrieve_annotated_text_from_parsed_content(annotator=annotator, sets_file=d_sets)
        project_id_d = create_project(annotator, project_phase='Doutrinador', suffix=suffix)
        create_project_labels(project_id_d, project_type='Doutrinador')
        create_documents_and_associate_to_project(project_id_d, annotator, annotations_d)
