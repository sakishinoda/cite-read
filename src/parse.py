# How to handle bibliography? BBL, BIB, in-line?
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

def partition_sections(soup, cmd='section'):
    cmds = [el for el in soup.descendants if hasattr(el, 'name') and el.name == cmd]
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

def citations_and_contexts(soup):
    cmds = [el for el in soup.descendants if hasattr(el, 'name') and
            el.name in ['cite', 'citep']]
    text = str(soup)
    contents = []
    start_idxs = [text.find(str(cmd)) for cmd in cmds]
    start_of_sentence = None  #
    end_of_sentence = None

def parse_document(tex_soup, bib_dict):
    sections = partition_sections(tex_soup, 'section')

    for section_title, section_text in sections:
        purged_section_text = purge_comments(section_text.replace('citep', 'cite'))
        section_sents = itertools.chain(*[s.split('\n') for s in sent_tokenize(purged_section_text)])
        cites = defaultdict(list)
        for sent in section_sents:
            if sent.find('cite') < 0:
                continue
            try:
                sent_soup = TexSoup(sent)
            except Exception as e:
                if isinstance(e, EOFError):
                    i = 1
                    while True:
                        try:
                            sent_soup = TexSoup(sent[:-i])
                        except Exception as e:
                            i += 1
                            continue
                        break
                elif isinstance(e, TypeError):
                    import IPython; IPython.embed()
                    continue

            cites_in_sent = [el for el in sent_soup.descendants if hasattr(el, 'name') and el.name == 'cite']
            for cite_command in cites_in_sent:
                for c in cite_command.string.split(','):
                    cites[c.strip()].append(str(sent_soup))

        cite_counts = {k: len(v) for k, v in cites.items()}
        print(colored('In section "{}", found:'.format(section_title.string), 'white', 'on_cyan'))

        for k, v in reversed(sorted(cite_counts.items(), key=lambda x: x[1])):
            print('')
            print(colored('-> Found {} time(s)'.format(v), 'magenta'))
            print(colored(bib_dict.get(k, 'Not found: {}'.format(k)), 'white', 'on_yellow'))
            for context in cites[k]:
                print('-->', colored(context, 'green'))
        print('-' * 80)

def parse_bib(tex_soup):
    bibitems = partition_sections(tex_soup, 'bibitem')
    return {b[0].args[-1]: b[1].strip() for b in bibitems}

if __name__ == '__main__':
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

