"""Small HTML query helpers for view tests (stdlib only, no extra dependency)."""

from dataclasses import dataclass, field
from html.parser import HTMLParser

VOID_ELEMENTS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"}
)


@dataclass
class Element:
    tag: str
    attrs: dict[str, str | None]
    children: list["Element"] = field(default_factory=list)
    texts: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        parts = [*self.texts, *(child.text for child in self.children)]
        return " ".join(" ".join(parts).split())

    def get(self, name: str) -> str | None:
        return self.attrs.get(name)

    def iter(self):
        yield self
        for child in self.children:
            yield from child.iter()

    def find_all(self, tag: str | None = None, **attrs: str) -> list["Element"]:
        return [
            element
            for element in self.iter()
            if (tag is None or element.tag == tag)
            and all(
                element.attrs.get(name.rstrip("_").replace("_", "-")) == value
                for name, value in attrs.items()
            )
        ]

    def find(self, tag: str | None = None, **attrs: str) -> "Element | None":
        found = self.find_all(tag, **attrs)
        return found[0] if found else None

    def by_id(self, element_id: str) -> "Element":
        element = self.find(id=element_id)
        assert element is not None, f"no element with id={element_id!r}"
        return element


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("#root", {})
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = Element(tag, dict(attrs))
        self.stack[-1].children.append(element)
        if tag not in VOID_ELEMENTS:
            self.stack.append(element)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.stack[-1].texts.append(data)


def parse_html(markup: str) -> Element:
    builder = _TreeBuilder()
    builder.feed(markup)
    return builder.root


def label_for(document: Element, control_id: str) -> Element | None:
    return document.find("label", for_=control_id)
