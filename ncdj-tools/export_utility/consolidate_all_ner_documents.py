
import os
import re
import csv
import json
import math
    
from collections import Counter

def scan(basedir, phase='', doc_type=''):
    """
    This function should scan the directories and create an data structure that
    should have an key to a .ner file and all ocurrences of that file within that
    basedir.
    """

    output = {}

    search_directory = os.path.join(phase, doc_type)

    for root, _, leaves in os.walk(basedir):
        if root.endswith(search_directory):
            for leaf in leaves:
                path = os.path.join(root, leaf)
                output.update({leaf: [path]}) if leaf not in output else output[leaf].append(path)

    return output

def open_document_and_get_initial_tokens(filename):
    """
    This function should return the initial tokens of the document. This will be used later to
    indicates which annotation was the most agreed between peers.
    """

    with open(filename, 'r') as fh:
        csvreader = csv.reader(fh, delimiter=';')

        start_tokens = {pos for pos, tuple_ in enumerate(csvreader) if re.match('B_', tuple_[1])}

    return start_tokens

def open_document_and_get_start_and_end_tokens(filename):
    """
    This function iterate over the indexes
    """

    output = []

    with open(filename, 'r') as fh:
        csvreader = csv.reader(fh, delimiter=';')
        tokens = list(csvreader)[1:]

    index = 0
    while index < len(tokens):

        following_index = index

        if not tokens[index][1].startswith('B_'):
            index += 1
        else:
            following_index += 1
            following_tag = tokens[following_index][1]

            while following_tag.startswith('I_'):
                following_index += 1
                if following_index < len(tokens):
                    following_tag = tokens[following_index][1]
                else:
                    break

            following_index -= 1

            output.append((index, following_index, tokens[index][1]))
            index = following_index
    
    return output

def majority_vote(sets):
    """
    This function should count the beginnings tokens and decide which tokens were annotated by 
    the majority of the annotators.
    """

    L = []
    for set_ in sets:
        L.extend(set_)

    C = Counter(L)

    number_of_annotators = len(sets)
    most_agreed_annotations = filter(lambda x: C[x] >= math.floor(number_of_annotators / 2) + 1, C)

    return most_agreed_annotations

def recreate_document_with_the_majority_annotations(filename, annotations):

    output = []

    with open(filename, 'r') as fh:
        csvreader = csv.reader(fh, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        tokens = list(csvreader)[1:]
        tokens = [token for token, _ in tokens]

    index = 0
    while index < len(tokens):
        if index not in majority_dict:
            tokens[index] = (tokens[index], 'O')
            index += 1
            continue
        else:
            boundary_index = int(majority_dict[index][1])
            start_tag = majority_dict[index][2]
            following_tag = start_tag.replace('B_', 'I_')
            tokens[index] = (tokens[index], start_tag)

            incremental_index = index + 1
            while incremental_index <= boundary_index:
                tokens[incremental_index] = (tokens[incremental_index], following_tag)
                incremental_index += 1
            index = incremental_index

    print(json.dumps(tokens, indent=4))

    basename = os.path.basename(filename)
    document_with_majority_annotations = os.path.join('outdir', basename)
    with open(document_with_majority_annotations, 'w') as fh:
        csv_writer = csv.writer(fh, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(['Token', 'Tag'])
        for token, tag in tokens:
            csv_writer.writerow([token, tag])


if __name__ == '__main__':
    output = scan('./mock', 'treino_1', 'Documentos')

    for key in output.keys():
        annotations_sets = []
        sample_document = output[key][0]  # any document will serve for this purpose
        for fname in output[key]:
            annotations = open_document_and_get_start_and_end_tokens(fname)
            annotations_sets.append(annotations)
        
        majority = majority_vote(annotations_sets)
        majority_dict = {v[0]:v for v in majority}
        print(majority_dict)
        # recreate_document_with_the_majority_annotations(sample_document, majority)

    # key = '20120802_Rcl_14003_76217662.ner.csv'

    # annotations_sets = []
    # sample_document = output[key][0]  # any document will serve for this purpose
    # for fname in output[key]:
    #     annotations = open_document_and_get_start_and_end_tokens(fname)
    #     annotations_sets.append(annotations)

    # majority = majority_vote(annotations_sets)
    # majority_dict = {v[0]:v for v in majority}
    # recreate_document_with_the_majority_annotations(sample_document, majority)
