
import os
import re
import sys
import csv
import json
import django
import argparse
import pandas as pd

# SETUP DJANGO ENVIRONMENT AND APP
sys.path.append(os.path.abspath('../../app'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.contrib.auth.models import User
from server.models import Document, Project, Label, SequenceAnnotation

PATTERNS = [
    r'\-(?!\d)',  # '-' only if not succeded by a digit
    r'\.(?!\d)',  # '.' only if not succeded by a digit. thousands delimiter
    r'\,(?!\d)',  # ',' only if not succeded by a digit. units delimiter
    r'\/(?!\d{1,2})',  # '/' only if not preceded and succeded by digits. date delimiter
    r'\:',
    r'\s',  # whitespace delimiter
    r'\n',  # newline delimiter
    r'\(',
    r'\)'
]

BASEDIR='data/'

def parse_command_line_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--doctype', help='identification of doc type', required=True)
    parser.add_argument('--phase', help='identification of phase', required=False)
    parser.add_argument('--outdir', help='base directory for exports', required=True)
    cli = parser.parse_args()

    return cli

def parse_id(phase, document):

    if phase == 'treino_1' or phase == 'treino_2':
        id_ = document.id
    elif phase == '[PRATICA_ETAPA_1]':
        id_ = document.text.split('\n')[-1].split(': ')[-1]
    elif phase == 'PRATICA_ETAPA1':
        id_ = document.text.split('\n')[-1].split(': ')[-1]

    return id_

def build_pattern():
    whole_pattern = r'|'.join(PATTERNS)
    whole_pattern = r'(%s)' % whole_pattern
    
    pattern = re.compile(whole_pattern)

    return pattern

def process(text, offsets):
    
    # splitted text preserving the delimiter characters, so the offset stays the same
    splitted = re.split(COMPILED_PATTERN, text)
    
    # initial list with the same length assuming all items are outside tags ('O')
    output = ['O' for _ in range(len(splitted))]
    
    # sorting the offsets because doccano doesn't care to do so
    offsets = sorted(offsets, key=lambda x: x[0])

    total_len_so_far = 0
    for index, token in enumerate(splitted):
        # after add the length of token we do not know where the token starts
        before_increment = total_len_so_far
        total_len_so_far += len(token)
        for start_offset, end_offset, label in offsets:
            if total_len_so_far >= start_offset + 1 \
                    and total_len_so_far <= end_offset + 1:
                
                output[index] = 'B_' + label if before_increment == start_offset else 'I_' + label

    zipped = zip(splitted, output)

    # filtering unwanted chars (improve regex later, maybe?)
    zipped = [(token, label) for token, label in zipped if token not in [r'', r' ', r'\n']]

    return zipped

def save(username, doctype, phase, data):
    id_, payload = data
    dirname = os.path.join(BASEDIR, username, phase, doc_type)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    fullname = os.path.join(dirname, '%s.ner.csv' % (id_))
    with open(fullname, 'w') as fh:
        csv_writer = csv.writer(fh, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(['Token', 'Tag'])
        for token, tag in payload:
            csv_writer.writerow([token, tag])

if __name__ == '__main__':

    COMPILED_PATTERN = build_pattern()

    users = User.objects.exclude(username__in=['admin', 'carla'])

    cli = parse_command_line_arguments()

    phase = cli.phase or 'treino_1'
    doc_type = cli.doctype
    BASEDIR = cli.outdir

    for user in users:

        if phase == 'treino_1':
            project = Project.objects.filter(users__username=user.username,
                        name__startswith=doc_type, name__endswith=user.username).first()
        else:
            project = Project.objects.filter(users__username=user.username,
                        name__startswith=doc_type, name__endswith=phase).first()

        documents = Document.objects.filter(project=project)

        for document in documents:
            # id_ = document.text.split('\n')[-1].split(': ')[-1]
            id_ = parse_id(phase, document)
            annotations = SequenceAnnotation.objects.filter(document=document)
            offsets = [(a.start_offset, a.end_offset, a.label.text) for a in annotations]
            if annotations.count() > 0:
                data = (id_, process(document.text, offsets))
                save(user.username, doc_type, phase, data)
