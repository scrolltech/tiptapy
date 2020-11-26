import json

from html import escape as e
from typing import Dict
from inspect import isclass
from urllib.parse import urlparse
from .image import url2mime

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.filters import TokenMergeFilter

from .nullFormat import NullFormatter

__version__ = '0.8.1'

renderers: Dict = {}


class BaseNode:
    """
    Base Node class with reference implemention for common cases.
    This should be used as base class for all leaf level nodes
    which do not contain other nodes.
    """
    type = "prose-mirror_content-type"
    wrap_tag: str = ""
    css_class: str = ""

    def is_renderable(self, node):
        """
        Checks whether the node is worth rendering.
        Example: Image block without src attribute might not.
        """
        return True

    def render(self, in_data) -> str:
        out = ''
        if self.is_renderable(in_data):
            out = self.inner_render(in_data)
            css_class_s = f' class="{self.css_class}"' if self.css_class else ''
            if self.wrap_tag:
                out = f"<{self.wrap_tag}{css_class_s}>{out}</{self.wrap_tag}>"
        return out

    def inner_render(self, node) -> str:
        return e(node["content"]["text"])


class BaseContainer(BaseNode):
    """
    Base class for container type nodes which may further contain other nodes.
    """

    def inner_render(self, nodes: Dict) -> str:
        out = ""
        for node in nodes.get("content", []):
            node_type = node.get("type")
            renderer = renderers.get(node_type)
            assert renderer, f'Unsupported node_type: "{node_type}"'
            if renderer:
                out += renderer.render(node)
        return out


class config:
    """
    Config class to store constans which are used by the othe nodes.
    """
    DOMAIN = "python.org"


class Text(BaseNode):
    type = "text"
    mark_tags = {"bold": "strong", "italic": "em", "link": "a", "sup": "sup"}

    def inner_render(self, node):
        text = e(node["text"])
        marks = node.get("marks")
        if marks:
            for mark in marks:
                tag = self.mark_tags.get(mark.get("type"))
                attrs = mark.get("attrs")
                if attrs:
                    if tag == "a":
                        url = attrs.get("href") or ""
                        if not is_trusted_link(url):
                            attrs["target"] = "_blank"
                            attrs["rel"] = "noopener nofollow"
                    attrs_s = " ".join(
                        f'{k}="{e(v)}"' for k, v in attrs.items()
                    )
                    text = f"<{tag} {attrs_s}>{text}</{tag}>"
                else:
                    text = f"<{tag}>{text}</{tag}>"
        return text


class Heading(BaseContainer):
    type = "heading"

    def inner_render(self, node) -> str:
        attrs = node['attrs']
        level = attrs.get('level') or 1
        tag = e(f"h{level}")
        inner_html = super().inner_render(node)
        return f"<{tag}>{inner_html}</{tag}>"


class Image(BaseNode):
    type = "image"
    wrap_tag: str = "figure"

    def is_renderable(self, node):
        attrs = node.get("attrs", {})
        src = attrs.get("src", "")
        return src and bool(
            src.get('image', '').strip() or src.get('fallback', '').strip()
        )

    def inner_render(self, node) -> str:
        attrs = node["attrs"]
        alt = attrs.get('alt', '').strip()
        caption = attrs.get('caption', '').strip()
        image_url = attrs['src']['image']
        fallback_url = attrs['src']['fallback']
        image_type = url2mime(image_url)
        fallback_type = url2mime(fallback_url)
        image_src = f'<img src="{fallback_url}"/>'
        if alt:
            image_src = f'<img src="{fallback_url}" alt="{e(alt)}"/>'
        html = f'<picture><source srcset="{image_url}" type="{image_type}"/><source srcset="{fallback_url}" type="{fallback_type}"/>{image_src}</picture>'  # noqa: E501
        if caption:
            html = html + f'<figcaption>{e(caption)}</figcaption>'
        return html


class Embed(BaseContainer):
    type = "embed"

    def inner_render(self, node) -> str:
        attrs = node['attrs']
        html = attrs.get('html', '')
        if attrs.get('type') == 'video':
            caption = (attrs.get('caption') or '').strip()
            if caption:
                html += f"<figcaption>{caption}</figcaption>"
        provider_name = attrs.get('provider') or 'link'
        return f'<div class="embed-wrapper {provider_name.lower()}-wrapper"><figure>{html}</figure></div>'  # noqa: E501

class CodeBlock(BaseNode):
    type = "code_block"
    language_map = {
        'xml': 'html'
    }

    def inner_render(self, node):
        attrs = node.get("attrs", {})
        language = attrs.get("language", "")
        language = self.language_map.get(language, language)
        content = node.get("content", {})[0]
        text = content.get("text", "")
        print(language)
        if language:
            lexer = get_lexer_by_name(language, stripall=True)
            print(lexer)
            lexer.add_filter(TokenMergeFilter())
            formatter = NullFormatter(language=language)
            formatter = HtmlFormatter()
            html = highlight(text, lexer, formatter)
        return f'{html}'

class Title(BaseContainer):
    type = "title"
    wrap_tag: str = "h1"


class Paragraph(BaseContainer):
    type = "paragraph"
    wrap_tag: str = "p"

    def is_renderable(self, node):
        return bool(node.get('content'))


class BlockQuote(BaseContainer):
    type = "blockquote"
    wrap_tag: str = "blockquote"


class HardBreak(BaseContainer):
    type = "hard_break"

    def inner_render(self, node):
        return "<br>"


class HorizontalRule(BaseNode):
    type = "horizontal_rule"

    def inner_render(self, node):
        return "<hr>"


class ListItem(BaseContainer):
    type = "list_item"
    wrap_tag: str = "li"


class BulletList(BaseContainer):
    type = "bullet_list"
    wrap_tag: str = "ul"


class Doc(BaseContainer):
    type = "doc"


class OrderedList(BaseContainer):
    type = "ordered_list"
    wrap_tag: str = "ol"


def register_renderer(cls):
    renderers[cls.type] = cls()


for o in tuple(locals().values()):
    if isclass(o) and issubclass(o, BaseNode):
        register_renderer(o)


def convert_any(in_data):
    typ = in_data.get("type")
    renderer = renderers.get(typ)
    return renderer.render(in_data)


def is_trusted_link(url):
    """
    Check if the domain is the same as in the config.
    """
    link = urlparse(url)
    # Getting the domain of the link
    link = link.netloc
    return link.endswith(config.DOMAIN)


def to_html(s):
    in_data = s if isinstance(s, dict) else json.loads(s)
    return convert_any(in_data)


if __name__ == "__main__":
    import timeit

    s = open("tests/data.json").read()
    print(to_html(s))
    print(
        timeit.timeit(
            "to_html(s)",
            setup="from __main__ import to_html, s", number=100000
        )
    )
