import pytest
from citeread.parse import parse_sentence

@pytest.mark.parametrize('test_sent', [
    '\\begin{equation}',
    'If the elements of $v, x$ are uniformly bounded by $M$ \footnote{i.e.',
    ''
])
def test_parse_sentence_ok(test_sent):
    parse_sentence(test_sent)