from dataclasses import dataclass, field

from bs4 import BeautifulSoup


@dataclass
class HTMLBlock:
    kind: str  # heading | paragraph | table | list_item
    level: int | None
    text: str


@dataclass
class HTMLExtractionResult:
    blocks: list[HTMLBlock] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n\n".join(b.text for b in self.blocks if b.text)


_NOISE_TAGS = {"script", "style", "nav", "footer", "header", "noscript"}


def extract_html_structure(html: str) -> HTMLExtractionResult:
    """Parses HTML into structural blocks (headings/paragraphs/tables/list
    items) instead of collapsing everything into one raw text blob, so
    downstream chunking and metadata extraction can use real structure."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(_NOISE_TAGS):
        tag.decompose()

    result = HTMLExtractionResult()
    body = soup.body or soup
    for el in body.find_all(["h1", "h2", "h3", "h4", "p", "table", "li"]):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if el.name in {"h1", "h2", "h3", "h4"}:
            result.blocks.append(HTMLBlock(kind="heading", level=int(el.name[1]), text=text))
        elif el.name == "table":
            rows = [" | ".join(c.get_text(strip=True) for c in tr.find_all(["td", "th"])) for tr in el.find_all("tr")]
            result.blocks.append(HTMLBlock(kind="table", level=None, text="\n".join(r for r in rows if r)))
        elif el.name == "li":
            result.blocks.append(HTMLBlock(kind="list_item", level=None, text=text))
        else:
            result.blocks.append(HTMLBlock(kind="paragraph", level=None, text=text))
    return result
