"""Regression contract for the research-IA site's root-absolute links and routes.

This checks source before publication; the basePath-aware exported-HTML crawl in
scripts/audit_web_export.py remains the final check for computed links.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
NAV_FILE = Path("web/components/site/nav.ts")
SOURCE_DIRS = (Path("web/app"), Path("web/components"))
REQUIRED_ROUTES = ("/research/", "/studies/", "/log/", "/about/")
PAGES_BASE_PATH = "/z0evals"

# Only statically written href values are in scope. Dynamic expression hrefs
# (for example href={entry.href}) are covered by the post-build export crawl.
JSX_HREF_START = re.compile(r"""(?<![\w-])href\s*=\s*\{?\s*(["'`])""")
NAV_HREF_START = re.compile(r"""\bhref\s*:\s*(["'`])""")
NAV_BLOCK = re.compile(r"\bNAV\s*=\s*\[(.*?)\]\s*as\s+const\b", re.DOTALL)
SECTION_ROOTS_BLOCK = re.compile(r"\bSECTION_ROOTS\s*=\s*\[(.*?)\]", re.DOTALL)


@dataclass(frozen=True)
class LinkRef:
    source: str
    href: str


def quoted_at(text: str, opening: int) -> tuple[str, int]:
    """Read a JS/JSX string or template literal, allowing escaped delimiters."""
    quote = text[opening]
    if quote not in ("'", '"', "`"):
        raise ValueError(f"not a quoted literal at offset {opening}")
    pos = opening + 1
    while pos < len(text):
        if text[pos] == "\\":
            pos += 2
        elif text[pos] == quote:
            return text[opening + 1:pos], pos + 1
        else:
            pos += 1
    raise ValueError(f"unterminated href literal at offset {opening}")


def jsx_hrefs(source: str) -> list[tuple[int, str]]:
    """Find quoted href= values, with or without JSX expression braces."""
    found: list[tuple[int, str]] = []
    for match in JSX_HREF_START.finditer(source):
        value, _ = quoted_at(source, match.end() - 1)
        found.append((source.count("\n", 0, match.start()) + 1, value))
    return found


def nav_literals(source: str) -> list[str]:
    """Read both the NAV href properties and SECTION_ROOTS string literals."""
    nav = NAV_BLOCK.search(source)
    section = SECTION_ROOTS_BLOCK.search(source)
    if not nav or not section:
        raise AssertionError("nav.ts must declare NAV and SECTION_ROOTS")
    hrefs = [
        quoted_at(nav.group(1), match.end() - 1)[0]
        for match in NAV_HREF_START.finditer(nav.group(1))
    ]
    roots: list[str] = []
    text = section.group(1)
    pos = 0
    while pos < len(text):
        if text[pos] in ("'", '"', "`"):
            value, pos = quoted_at(text, pos)
            roots.append(value)
        else:
            pos += 1
    if not hrefs or not roots:
        raise AssertionError("NAV and SECTION_ROOTS must contain link literals")
    return hrefs + roots


def internal_path(href: str) -> str | None:
    """Keep a template's static prefix, then discard query/fragment portions."""
    prefix = href.split("${", 1)[0]
    if not prefix.startswith("/") or prefix.startswith("//"):
        return None  # external, relative, fragment-only, or nonliteral prefix
    return prefix.split("?", 1)[0].split("#", 1)[0] or "/"


def route_file(path: str, root: Path = ROOT) -> Path | None:
    """Locate a concrete app route or a generated one-segment markdown route."""
    app = root / "web/app"
    if path == "/":
        homepage = app / "page.tsx"
        return homepage if homepage.is_file() else None
    segments = path.strip("/").split("/")
    if any(segment in ("", ".", "..") for segment in segments):
        return None
    concrete = app.joinpath(*segments) / "page.tsx"
    if concrete.is_file():
        return concrete
    if len(segments) != 1:
        return None

    # web/app/[slug]/page.tsx calls markdownOnlySlugs() from web/lib/posts.ts.
    # scripts/build_posts.py generates web/data/posts/<slug>.json from posts/*.md.
    # The generated JSON is not committed, so the matching Markdown source plus
    # the dynamic route file proves this slug is in generateStaticParams().
    generated = app / "[slug]/page.tsx"
    markdown = root / "posts" / f"{segments[0]}.md"
    return generated if generated.is_file() and markdown.is_file() else None


def collect_links(root: Path = ROOT) -> list[LinkRef]:
    nav = root / NAV_FILE
    links = [LinkRef(NAV_FILE.as_posix(), href)
             for href in nav_literals(nav.read_text(encoding="utf-8"))]
    for directory in SOURCE_DIRS:
        folder = root / directory
        if not folder.is_dir():
            raise AssertionError(f"missing JSX source directory: {directory}")
        for file in sorted(folder.rglob("*.tsx")):
            rel = file.relative_to(root).as_posix()
            source = file.read_text(encoding="utf-8")
            links.extend(LinkRef(f"{rel}:{line}", href)
                         for line, href in jsx_hrefs(source))
    return links


def link_errors(links: list[LinkRef], root: Path = ROOT) -> list[str]:
    unresolved: list[str] = []
    for link in links:
        path = internal_path(link.href)
        if path is None:
            continue
        if path == PAGES_BASE_PATH or path.startswith(PAGES_BASE_PATH + "/"):
            unresolved.append(
                f"{link.source}: {link.href!r} hard-codes the {PAGES_BASE_PATH} basePath"
            )
        elif route_file(path, root) is None:
            unresolved.append(
                f"{link.source}: {link.href!r} -> {path!r} has no Next app route"
            )
    return sorted(set(unresolved))


class ResearchRouteContractTests(unittest.TestCase):
    def test_all_nav_and_jsx_literal_links_resolve(self):
        links = collect_links()
        self.assertGreater(len(links), len(REQUIRED_ROUTES),
                           "route/link scanner did not collect JSX links")
        errors = link_errors(links)
        self.assertEqual(errors, [], "Unresolved internal links:\n" + "\n".join(errors))

    def test_required_sections_have_real_pages(self):
        self.assertEqual(route_file("/"), ROOT / "web/app/page.tsx")
        for path in REQUIRED_ROUTES:
            with self.subTest(path=path):
                self.assertEqual(route_file(path),
                                 ROOT / "web/app" / path.strip("/") / "page.tsx")

    def test_live_nav_includes_every_section_and_home(self):
        found = nav_literals((ROOT / NAV_FILE).read_text(encoding="utf-8"))
        for path in ("/", *REQUIRED_ROUTES):
            with self.subTest(path=path):
                self.assertIn(path, found)

    def test_nav_parser_reads_href_and_section_roots(self):
        source = (
            'export const NAV = [{ href: "/research/", label: "r" }, '
            '{ href: `/studies/#toc`, label: "s" }] as const;\n'
            'const SECTION_ROOTS = ["/", "/about/"];\n'
        )
        self.assertEqual(nav_literals(source),
                         ["/research/", "/studies/#toc", "/", "/about/"])

    def test_missing_nav_route_is_reported(self):
        source = ('export const NAV = [{ href: "/missing/", label: "missing" }] '
                  'as const;\nconst SECTION_ROOTS = ["/"];\n')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app = root / "web/app"
            app.mkdir(parents=True)
            (app / "page.tsx").write_text("export default function Home() {}\n",
                                          encoding="utf-8")
            errors = link_errors([LinkRef("fixture/nav.ts", v)
                                  for v in nav_literals(source)], root)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("/missing/", errors[0])
        self.assertIn("no Next app route", errors[0])

    def test_query_hash_and_template_prefixes(self):
        source = """
<SiteLink href="/research/?area=speed#history" />
<SiteLink href={'/studies/#toc'} />
<SiteLink href={`/log/#${entry.id}`} />
<SiteLink href={`/research/?area=${area.id}`} />
<SiteLink href={`/${entry.slug/`} />
<SiteLink href={dynamicHref} />
<a href="#local" />
<a href="https://example.invalid/external" />
"""
        values = [value for _, value in jsx_hrefs(source)]
        self.assertEqual([internal_path(v) for v in values],
                         ["/research/", "/studies/", "/log/", "/research/",
                          "/", None, None])
        self.assertEqual(len(values), 7)

    def test_hard_coded_pages_base_path_is_reported(self):
        fixture = ('<SiteLink href="/z0evals/research/" />\n'
                   '<a href={"/z0evals?area=memory"} />\n')
        links = [LinkRef(f"fixture.tsx:{line}", href)
                 for line, href in jsx_hrefs(fixture)]
        errors = link_errors(links)
        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(all("hard-codes" in error for error in errors), errors)

    def test_dynamic_slug_requires_markdown_generation_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated = root / "web/app/[slug]/page.tsx"
            generated.parent.mkdir(parents=True)
            generated.write_text("export default function Post() {}\n",
                                 encoding="utf-8")
            posts = root / "posts"
            posts.mkdir()
            (posts / "published.md").write_text("# published\n", encoding="utf-8")
            self.assertEqual(route_file("/published/", root), generated)
            self.assertIsNone(route_file("/unpublished/", root))
            self.assertIsNone(route_file("/published/nested/", root))


if __name__ == "__main__":
    unittest.main()
