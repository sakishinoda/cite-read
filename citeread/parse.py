# How to handle bibliography? BBL, BIB, in-line?
import sys
import re
import itertools
from termcolor import colored
from functools import reduce
from TexSoup import TexSoup
from collections import OrderedDict, Counter, defaultdict
from nltk.tokenize import sent_tokenize

def purge_comments(text):
    comments = re.findall('%.*\\n', text)
    return reduce(lambda s, c: s.replace(c, ''), [text] + comments)

def partition_on_command(soup, cmd='section'):
    cmds = find_named_descendants(soup, cmd)
    text = str(soup)
    contents = []
    start_idxs = [text.find(str(cmd)) for cmd in cmds] + [len(text)]
    for i, cmd in enumerate(cmds):
        contents.append(
            (
                cmd,
                text[start_idxs[i]: start_idxs[i + 1]].lstrip(str(cmd))
            )
        )
    return contents

def parse_sentence(sent):
    parsed_sent = None
    for i in range(len(sent), 0, -1):
        try:
            parsed_sent = TexSoup(sent[:i])
        except EOFError:
            continue
        except TypeError:  # opened but not closed environments
            continue
        except AttributeError:  # opening an environment
            continue
        break

    return parsed_sent


def replace_cites(section, sent):
    while True:
        tag = sent.cite
        if not tag:
            return str(sent)
        args = ['<a href="#{0}/{1}">{1}</a>'.format(section.string, a.strip()) for a in tag.string.split(',')]
        tag.replace('({})'.format(', '.join(args)))


def find_named_descendants(soup, name):
    return [e for e in soup.descendants if hasattr(e, 'name')
            and e.name == name]

def parse_document(tex_soup, bib_dict):
    sections = partition_on_command(tex_soup, 'section')
    document_cites = []
    for section_title, section_text in sections:
        cites = parse_text(section_text)
        print(colored('In section "{}", found:'.format(section_title.string), 'white', 'on_cyan'))
        cites_with_bib_entry = []
        for k, v in cites:
            print('')
            print(colored('-> Found {} time(s)'.format(len(v)), 'magenta'))
            bib_entry = bib_dict.get(k, 'Not found: {}'.format(k))
            print(colored(bib_entry, 'white', 'on_yellow'))
            for context in v:
                print('-->', colored(context, 'green'))
            cites_with_bib_entry.append((k, bib_entry, [replace_cites(section_title, s) for s in v]))
        print('-' * 80)
        document_cites.append((section_title.string, cites_with_bib_entry))
    return document_cites

def count_and_rank_cites(cites):
    cite_counts = {k: len(v) for k, v in cites.items()}
    return {key: rank for rank, (key, count) in enumerate(reversed(sorted(cite_counts.items(), key=lambda x: x[1])))}

def sort_keys_by_value_count(d):
    counts = {k: len(v) for k, v in d.items()}
    return [k for k, _ in reversed(sorted(counts.items(), key=lambda x: x[1]))]

def convert_to_sorted_list(cites):
    cite_counts = {k: len(v) for k, v in cites.items()}
    return [(k, cites[k]) for k, _ in reversed(sorted(cite_counts.items(), key=lambda x: x[1]))]

def parse_text(text):
    purged_text = purge_comments(text.replace('citep', 'cite'))
    sentences = itertools.chain(
        *[s.split('\n') for s in sent_tokenize(purged_text)])
    cites = defaultdict(list)
    for sentence in sentences:
        if sentence.find('cite') < 0:
            continue
        parsed_sent = parse_sentence(sentence)
        cites_in_sent = find_named_descendants(parsed_sent, 'cite')
        cite_keys = collect_keys_for_context(cites_in_sent)
        for k in cite_keys:
            cites[k].append(parsed_sent)
    return convert_to_sorted_list(cites)


def collect_keys_for_context(cites_in_sent):
    keys = []
    for cite_command in cites_in_sent:
        cite_keys = cite_command.string.split(',')
        for cite_key in cite_keys:
            keys.append(cite_key.strip())
    return keys


def parse_bib(tex_soup):
    bibitems = partition_on_command(tex_soup, 'bibitem')
    return {b[0].args[-1]: b[1].strip() for b in bibitems}

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument('tex')
    parser.add_argument('bib')

    args = parser.parse_args()

    with open(args.tex, 'r') as f:
        tex = TexSoup(f.read())

    with open(args.bib, 'r') as f:
        bib = TexSoup(map(str, TexSoup(f.read()).thebibliography.contents))
        bib = parse_bib(bib)

    parsed = parse_document(tex, bib)
    with open('/tmp/parsed.json', 'w') as f:
        json.dump(parsed, f, indent=True)

    from jinja2 import Template
    with open('/home/sash/cite-read/citeread/template.html', 'r') as f:
        template = Template(f.read())

    with open('/tmp/parsed.html', 'w') as f:
        f.write(template.render(document=parsed))




if __name__ == '__main__':
    main()