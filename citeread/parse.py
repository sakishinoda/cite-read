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


def find_named_descendants(soup, name):
    return [e for e in soup.descendants if hasattr(e, 'name')
            and e.name == name]


def parse_document(tex_soup, bib_dict):
    sections = partition_on_command(tex_soup, 'section')
    document_cites = {}
    for section_title, section_text in sections:
        cites = parse_text(section_text)
        cite_counts = {k: len(v) for k, v in cites.items()}
        print(colored('In section "{}", found:'.format(section_title.string), 'white', 'on_cyan'))
        for k, v in reversed(sorted(cite_counts.items(), key=lambda x: x[1])):
            print('')
            print(colored('-> Found {} time(s)'.format(v), 'magenta'))
            print(colored(bib_dict.get(k, 'Not found: {}'.format(k)), 'white', 'on_yellow'))
            for context in cites[k]:
                print('-->', colored(context, 'green'))
        print('-' * 80)
        document_cites[section_title] = cites
    return document_cites


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

    # Here map all the keys to numbers so we have a numerical bibliography
    # Then replace all the cite tags in the contexts with the numerical refs
    return cites


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

    parser = argparse.ArgumentParser()
    parser.add_argument('tex')
    parser.add_argument('bib')
    args = parser.parse_args()

    with open(args.tex, 'r') as f:
        tex = TexSoup(f.read())

    with open(args.bib, 'r') as f:
        bib = TexSoup(map(str, TexSoup(f.read()).thebibliography.contents))
        bib = parse_bib(bib)


    parse_document(tex, bib)



if __name__ == '__main__':
    main()