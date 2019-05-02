#!/usr/bin/env python
# coding: utf-8
import re
import os
import unidecode


months = {
    u'janeiro': '01', u'fevereiro': '02', u'mar\xe7o': '03', u'abril': '04',
    u'maio': '05', u'junho': '06', u'julho': '07', u'agosto': '08',
    u'setembro': '09', u'outubro': '10', u'novembro': '11', u'dezembro': '12'
}


def to_sweep(text, sig, num, monocratic=True):
    """ Main function, which removes unnecessary header, extra space, tabs and returns
    final text content, ready to be updated on ES
    """
    justice = justice_collector(text)

    if not justice:
        justice = justice_collector_till_2012(text)
    if not justice:
        justice = ""
    justice = justice.lower()
    
    jud_date = judgement_date_collector(text)
        
    report = {
        'ref_pag': 0,
        'ref_ass_dig': 0,
        'ref_sig_num': 0,
        'size_header': 0
    }
    
    old_size = len(text)

    if monocratic:
        text = remove_header_process_parts(text)
    else:
        text = remove_header_process_parts_acordaos(text)

    text = re.sub(' +', ' ', text).strip()  
    text = re.sub('\t',' ', text)
    
    report['size_header'] = old_size - len(text)

    text = re.sub(r"<Pagina (\d+)>", r"\n\n<Pagina \1>\n\n", text)
    text = re.sub(r"\n\n+", "\n\n", text)

    paragraphs = [t.strip() for t in text.split('\n\n') if t]

    sanitazied_content = []
    new_page = False
    for paragraph in paragraphs:

        # eliminates title at the very start of the page
        if new_page:
            new_page = False
            continue

        # eliminates page counter
        token_01 = "<Pagina"
        if token_01 in paragraph and len(paragraph) < 2 * len(token_01):
            report['ref_pag'] += 1
            if not monocratic:
                new_page = True
            continue

        # eliminates the digital signature at the end of every page
        token_02 = "Documento assinado digitalmente "
        if token_02 in paragraph and len(paragraph) <  400:
            report['ref_ass_dig'] += 1
            continue

        # eliminates the self reference title at the beginning of the page
        token_03 = "%s %s " % (sig.lower(), num)
        if len(set(token_03) - set(paragraph.lower())) == 0 and len(paragraph) < len(token_03) + 10:
            report['ref_sig_num'] += 1
            continue

        # eliminates very short rows, usually only with number or empty spaces
        if len(paragraph.replace(" ", "")) < 4:
            continue
        
        sanitazied_content.append(paragraph)

    i = 0
    new_text_content = ''
    while i < len(sanitazied_content):
        text_in_a_row = sanitazied_content[i].replace('\n', '')
        if text_in_a_row:
            if is_upper(text_in_a_row[0]):
                new_text_content += '\n\n'
            new_text_content += text_in_a_row + ' '
        i += 1 
    new_text_content = re.sub(' +', ' ', new_text_content).strip()  
    new_text_content = re.sub('\t',' ', new_text_content)
    
    return new_text_content, justice, jud_date, report


def justice_collector(text):
    """ Captures the process's Justice for years from 2013 to 2017
    """
    justice_at_start = re.search('.*\n\n?RELATORA? : MIN(\.|ISTRO) (.*)\n', text[:150])
    if justice_at_start:
        # checks if it finds justice at the beginning of the document
        justice_at_start = justice_at_start.groups()[1].strip()
        justice_at_the_end = re.search('\nMinistr[oa] (.*)\n', text[-100:])
        if justice_at_the_end:
            # checks if it finds justice at the end of the document
            justice_at_the_end = justice_at_the_end.groups()[0].strip()
            if justice_at_start.lower() == justice_at_the_end.lower():
                return justice_at_start.title()
    else:
        if re.search('.*\n\n?REGISTRADO : MIN(\.|ISTRO) PRESIDENTE\n', text[:150]):
            justice_at_the_end = re.search('\nMinistr[oa] (.*)\n', text[-100:])
            if justice_at_the_end:
                # checks if it finds justice at the end of the document
                justice_at_the_end = justice_at_the_end.groups()[0].strip()
                return justice_at_the_end.title() + ' | Presidente'


def justice_collector_till_2012(text):
    """ Captures the process's Justice for years until 2012 (for these cases, the pattern is different)
    """
    justice_at_the_end = re.search('\nMinistr[oa] (.*)\n', text[-150:])
    if justice_at_the_end:
        justice_at_the_end = justice_at_the_end.groups()[0].strip()
        if justice_at_the_end:
            return justice_at_the_end.title()


def judgement_date_collector(text):
    """ Captures judgement date of the decision 
    """
    pattern = re.search('\nBras\xedlia,? (\d{1,2}).{,4} de (\D{4,9}) de (\d{4})\.? ?\n', text[-150:])
    if pattern:   
        day = pattern.groups()[0]
        if len(day) < 2:
            day = '0' + day
        month = months.get(pattern.groups()[1].lower())
        year = pattern.groups()[2]
        if day and month and year:
            return year + '-' + month + '-' + day


def remove_header_process_parts(text):
    """ Finds beginning of relevant text content, then loops backwards to remove paragraphs which refer to parts of process 
    """
    idx_start = re.search(
        '\n\n.{,5}(decis...?.?.?(\n|: )|despacho.?.?.?(\n|: )|vistos etc|trata-se de|tendo em conta)',
        text, flags=re.IGNORECASE
    )
    if idx_start:
        idx_start = idx_start.start()
        header = text[:idx_start]
        paragraphs = header.split('\n\n')
        for i in range(len(paragraphs)-1, -1, -1):
            number_of_colons = paragraphs[i].count(':')
            number_of_line_breaks = paragraphs[i].count('\n')
            if (number_of_colons > 1) and (number_of_line_breaks > 0) and (number_of_colons >= number_of_line_breaks/2.) and is_upper(paragraphs[i]):
                break
        paragraphs = [par for par in paragraphs[i+1:]]
        return '\n\n'.join(paragraphs) + '\n\n' + text[idx_start + 2:]
    return text


def remove_header_process_parts_acordaos(text):
    """ Finds beginning of relevant text content, then loops backwards to remove paragraphs which refer to parts of process 
    """
    idx_start = re.search('\n\ne ?m ?e ?n ?t ?a ?:? ', text, flags=re.IGNORECASE)
    if idx_start:
        threshold_colons = 0
        if idx_start > 500:
            # if the beggning of the text content itself (the text after the process' parts) is not in beginning of text, 
            # then we need to be a little more restrict
            threshold_colons += 1
        idx_start = idx_start.start()
        header = text[:idx_start]
        paragraphs = header.split('\n\n')
        for i in range(len(paragraphs)-1, -1, -1):
            number_of_colons = paragraphs[i].count(':')
            number_of_line_breaks = paragraphs[i].count('\n')
            if (number_of_colons > threshold_colons) and (number_of_line_breaks > 0) and (number_of_colons >= number_of_line_breaks/2.) and paragraphs[i].isupper():
                break
        paragraphs = [par for par in paragraphs[i+1:]]
        return '\n\n'.join(paragraphs) + '\n\n' + text[idx_start+2:]
    return text


def is_upper(ch):
    txt = unidecode.unidecode(ch)
    if re.match(r"[A-Z]|[1-9]|‘|“|'|\"", txt):
        return True
    return False
