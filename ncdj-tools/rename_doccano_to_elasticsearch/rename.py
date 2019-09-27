
import os
import argparse

SIMPLE_LOOKUP = {
    'LTDA': '20120802_Rcl_14003_76217662',
    'EMENTA': '20151001_RHC_128515_307832857',
    'Ementa': '20120828_ARE_689457_2906011',
    'DECISÃO': '20150302_RE_861115_305513530',
}

def parse_command_line_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--indir', help='base directory for exports', required=True)
    parser.add_argument('--phase', help='1st level directory', required=True)
    parser.add_argument('--doctype', help='2nd level directory', required=True)
    cli = parser.parse_args()

    return cli

def walktrough(dirname):
    for root, _, leaf in os.walk(dirname):
        if root.endswith('%s/%s' % (phase, doctype)):
            if leaf:
                for fname in leaf:
                    pathname = os.path.join(root, fname)

                    with open(pathname, 'r') as fh:

                        if phase == 'treino_1':
                            content = fh.readlines()[1][:-1]
                            new_fname = binding_by_strategy_1(content)
                        elif phase == 'treino_2':
                            content = fh.readlines()[-1][:-1]
                            new_fname = binding_by_strategy_2(content)

                    new_pathname = os.path.join(root, new_fname)

                    os.rename(pathname, new_pathname)

def binding_by_strategy_1(content):
    for first_token in ['LTDA', 'EMENTA', 'Ementa', 'DECISÃO']:
        if content.startswith(first_token):
            new_fname = '%s.ner.csv' % SIMPLE_LOOKUP[first_token]
            break

    return new_fname

def binding_by_strategy_2(content):
    id_component = content.split(';')[0]
    new_fname = '%s.ner.csv' % id_component
    
    return new_fname
    

if __name__ == '__main__':
    cli = parse_command_line_arguments()

    dirname = cli.indir
    phase = cli.phase
    doctype = cli.doctype

    walktrough(dirname)
