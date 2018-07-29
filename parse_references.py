"""
Convert a entries in `references.bib` to a markdown file
"""
import unicodedata
import itertools

import bibtexparser
from bibtexparser.latexenc import unicode_to_latex, unicode_to_crappy_latex1, unicode_to_crappy_latex2
from jinja2 import Environment, DictLoader


template = """Below is a far-from-comprehensive list of references that we collected while organizing this session. Please feel free to suggest any additions!

{% for e in entries %}
* {{e.author | latex_to_unicode | tex_filter}} {{e.year | latex_to_unicode | tex_filter}}, *{{e.title | latex_to_unicode | tex_filter}}*, {{e.journal | latex_to_unicode | tex_filter}}, **{{e.volume | latex_to_unicode | tex_filter}}:{{e.pages | latex_to_unicode | tex_filter}}**, [(Link)](https://doi.org/{{e.doi | latex_to_unicode | tex_filter}})
{% endfor %}
"""


def tex_filter(string):
    """
    Any replacement, filtering in the journal abbreviations
    """
    return string.replace('&', '\&')


def latex_to_unicode(string):
    """
    Convert a LaTeX string to unicode equivalent.

    NOTE: Taken from latest bibtexparser codebase
    (https://github.com/sciunto-org/python-bibtexparser),
    but using the version in pip as the newest version seems
    to have some bugs. This could be a problem with new releases
    on PyPI
    """
    if '\\' in string or '{' in string:
        for k, v in itertools.chain(unicode_to_crappy_latex1, unicode_to_latex):
            if v in string:
                string = string.replace(v, k)

    # If there is still very crappy items
    if '\\' in string:
        for k, v in unicode_to_crappy_latex2:
            if v in string:
                parts = string.split(str(v))
                for key, string in enumerate(parts):
                    if key+1 < len(parts) and len(parts[key+1]) > 0:
                        # Change order to display accents
                        parts[key] = parts[key] + parts[key+1][0]
                        parts[key+1] = parts[key+1][1:]
                string = k.join(parts)

    # Place accents at correct position
    # LaTeX requires accents *before* the character. Unicode requires accents
    # to be *after* the character. Hence, by a raw conversion, accents are not
    # on the correct letter, see
    # https://github.com/sciunto-org/python-bibtexparser/issues/121.
    # We just swap accents positions to fix this.
    cleaned_string = []
    i = 0
    while i < len(string):
        if not unicodedata.combining(string[i]):
            # Not a combining diacritical mark, append it
            cleaned_string.append(string[i])
            i += 1
        elif i < len(string) - 1:
            # Diacritical mark, append it but swap with next character
            cleaned_string.append(string[i + 1])
            cleaned_string.append(string[i])
            i += 2
        else:
            # If trailing character is a combining one, just discard it
            i += 1

    # Normalize unicode characters
    # Also, when converting to unicode, we should return a normalized Unicode
    # string, that is always having only compound accentuated character (letter
    # + accent) or single accentuated character (letter with accent). We choose
    # to normalize to the latter.
    cleaned_string = unicodedata.normalize("NFC", "".join(cleaned_string))

    # Remove any left braces
    cleaned_string = cleaned_string.replace("{", "").replace("}", "")

    return cleaned_string


if __name__=='__main__':
    # Parse bib file
    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    with open('references.bib', 'r') as f:
        bib = parser.parse_file(f)
    entries = sorted(bib.entries, key=lambda x:x['year'])
    # Setup jinja environment
    env = Environment(loader=DictLoader({'references.md': template}))
    env.filters.update({'latex_to_unicode': latex_to_unicode, 'tex_filter': tex_filter})
    # Render template
    references_md = env.get_template('references.md').render(entries=entries)
    with open('pages/references.md','w') as f:
        f.write(references_md)