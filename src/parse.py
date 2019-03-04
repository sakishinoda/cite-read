# How to handle bibliography? BBL, BIB, in-line?
from TexSoup import TexSoup
from collections import OrderedDict, Counter, defaultdict

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
        section_text_ = section_text.replace('citep', 'cite')
        cites_ = partition_sections(TexSoup(section_text_), 'cite')
        cites = defaultdict(list)
        for cite_command, cite_context in cites_:
            split_commands = [c.strip() for c in cite_command.string.split(',')]
            for cmd in split_commands:
                cites[cmd].append(cite_context[:100])

        cite_counts = {k: len(v) for k, v in cites.items()}
        print('In section "{}", found:'.format(section_title.string))

        for k, v in reversed(sorted(cite_counts.items(), key=lambda x: x[1])):
            print('-> Found {} time(s)'.format(v))
            print(bib_dict.get(k, 'Not found: {}'.format(k)))
            for context in cites[k]:
                print('-->', context)
        print('-' * 80)

def parse_bib(tex_soup):
    bibitems = partition_sections(tex_soup, 'bibitem')
    return {b[0].args[-1]: b[1] for b in bibitems}

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

