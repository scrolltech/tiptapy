from pygments.formatter import Formatter
from pygments.token import Token, Text, STANDARD_TYPES
import functools

_escape_html_table = {
    ord('&'): '&amp;',
    ord('<'): '&lt;',
    ord('>'): '&gt;',
    ord('"'): '&quot;',
    ord("'"): '&#39;',
}

# TODO:
# Update css file accordingaly
# extra double quotes, fix that
# regex has /b, which makes previous char disappear, fix that

HLJS_TYPES = {
    # keyword
    Token.Keyword.Namespace: 'hljs-keyword',
    Token.Keyword.Declaration: 'hljs-keyword',
    Token.Keyword.Type: 'hljs-keyword',
    Token.Keyword.Constant: 'hljs-literal',
    Token.Keyword: 'hljs-keyword',
    # text
    Token.Text: '',
    Token.Punctuation: '',
    Token.Name: '',
    Token.Name.Class: 'hljs-title',
    Token.Name.Other: '',
    Token.Name.Namespace: '',
    Token.Name.Attribute: '',
    Token.Name.Function: 'hljs-title',
    Token.Name.Builtin: 'hljs-built_in',
    Token.Name.Builtin.Pseudo: '',
    Token.Name.Tag: 'hljs-attr',
    Token.Name.Variable: 'hljs-variable',
    # literal
    Token.Literal.String: 'hljs-string',
    Token.Literal.String.Single: 'hljs-string',
    Token.Literal.String.Doc: 'hljs-string',
    Token.Literal.String.Double: 'hljs-string',
    Token.Literal.String.Affix: 'hljs-string',
    Token.Literal.String.Interpol: '',
    Token.Literal.String.Backtick: '',
    Token.Literal.String.Regex: 'hljs-regexp',
    # comment
    Token.Comment.Single: 'hljs-comment',
    Token.Comment.Multiline: 'hljs-comment',
    Token.Comment.Preproc: 'hljs-meta',
    Token.Comment.Hashbang: 'hljs-meta',
    # operator
    Token.Operator: '',
    # number
    Token.Literal.Number: '',
    Token.Literal.Number.Float: 'hljs-number',
    Token.Literal.Number.Integer: 'hljs-number',
    Token.Literal.Number.Hex: 'hljs-number',
    Token.Literal.Number.Integer.Long: 'hljs-number',
}

HLJS_TYPES_LANGUAGE_OVERRIDE = {
    # python
    'html': {
        Token.Name.Tag: 'hljs-name',
        Token.Name.Attribute: 'hljs-attr',
    },
    'css': {
        Token.Keyword: 'hljs-attribute',
        Token.Keyword.Constant: '',
    },
}

class NullFormatter(Formatter):
    def __init__(self, **options):
        Formatter.__init__(self, **options)
        self.language = options.get('language') or ''
        self.span_element_openers = {}
        self.cssclass = 'highlight'

    @functools.lru_cache(maxsize=100)
    def _translate_parts(self, value):
        """HTML-escape a value and split it by newlines."""
        return value.translate(_escape_html_table).split('\n')

    def _format_lines(self, tokensource):
        """
        Just format the tokens, without any wrapping tags.
        Yield individual lines.
        """
        lsep = '\n'
        lspan = ''
        line = []
        for ttype, value in tokensource:
            try:
                cspan = self.span_element_openers[ttype]
            except KeyError:
                cspan = self.span_element_openers[ttype] = self._get_css_classes(ttype)
            print(ttype, cspan, value)
            parts = self._translate_parts(value)

            # for all but the last line
            for part in parts[:-1]:
                if line:
                    if lspan != cspan:
                        line.extend(((lspan and '</span>'), cspan, part,
                                     (cspan and '</span>'), lsep))
                    else:  # both are the same
                        line.extend((part, (lspan and '</span>'), lsep))
                    yield 1, ''.join(line)
                    line = []
                elif part:
                    yield 1, ''.join((cspan, part, (cspan and '</span>'), lsep))
                else:
                    yield 1, lsep
            # for the last line
            if line and parts[-1]:
                if lspan != cspan:
                    line.extend(((lspan and '</span>'), cspan, parts[-1]))
                    lspan = cspan
                else:
                    line.append(parts[-1])
            elif parts[-1]:
                line = [cspan, parts[-1]]
                lspan = cspan
            # else we neither have to open a new span nor set lspan

        if line:
            line.extend(((lspan and '</span>'), lsep))
            yield 1, ''.join(line)

    def _get_css_classes(self, ttype):
        """Generate the opening <span> tag for a given token type using CSS classes."""
        print(ttype)
        cls = HLJS_TYPES.get(ttype, '')
        cls = HLJS_TYPES_LANGUAGE_OVERRIDE.get(self.language, {}).get(ttype, cls)
        return cls and '<span class="%s">' % cls or ''

    def _wrap_div(self, inner):
        yield 0, ('<div' + (self.cssclass and ' class="%s"' % self.cssclass) + '>')
        yield from inner
        yield 0, '</div>\n'

    def _wrap_pre(self, inner):
        yield 0, ('<pre' + '><span></span>')
        yield from inner
        yield 0, '</pre>'

    def wrap(self, source, outfile):
        return self._wrap_div(self._wrap_pre(source))

    def format(self, tokensource, outfile):
        source = self._format_lines(tokensource)
        source = self.wrap(source, outfile)
        for t, piece in source:
            outfile.write(piece)
