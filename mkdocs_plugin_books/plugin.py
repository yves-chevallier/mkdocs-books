import shutil
import yaml

from datetime import datetime
from pathlib import Path, PosixPath
from typing import List

from mkdocs.structure import StructureItem
from mkdocs.structure.nav import Section
from mkdocs.utils import log
from mkdocs.plugins import BasePlugin
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.nav import Navigation
from mkdocs.structure.files import Files
from .config import BooksConfig, BookConfig
from .renderer import LaTeXRenderer

from IPython import embed


def path_representer(dumper, data, current=Path(".")):
    # Path relative to the project directory
    data = data.resolve().relative_to(current.resolve())
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


yaml.add_representer(PosixPath, path_representer)


class Books(BasePlugin[BooksConfig]):
    def __init__(self):
        self.dirty = False
        self.saved_nav = []
        self.latex_dir = Path("build")
        self.is_serve = False
        self.renderer = None
        self.current_config = None
        self.project_dir = None
        self.build_dir = None
        self.saved_nav = None

    def on_startup(self, command: str, dirty: bool):
        # Save the command to check if latex has to be generated
        # Those are not available later in the process.
        self.is_serve = command == "serve"
        self.dirty = dirty

    def on_nav(self, nav: Navigation, config: MkDocsConfig, files: Files):
        self.project_dir = Path(config.config_file_path).parent

        if not Path(self.config.output_dir).is_absolute():
            self.config.output_dir = self.project_dir / self.config.output_dir

        # Disable plugin if serve command is used
        self.config.enabled &= not self.is_serve

        # Need to postpone the nav processing until pages are processed
        # nav isn't ready yet and not available later in process
        self.saved_nav = nav

    def on_env(self, env, config, files):
        if not self.config.enabled:
            return

        # Add default book if none is provided
        if not self.config.books:
            self.config.books.append(BookConfig())
            book = self.config.books[0]
            book.root = self.saved_nav.pages[0].title
            book.title = config.site_name
            book.author = config.site_author
            book.year = datetime.now().year
            book.subtitle = config.site_description

        # Apply default values
        for book in self.config.books:
            if book.title is None:
                book.title = config.site_name
            if book.author is None:
                book.author = config.site_author
            if book.year is None:
                book.year = datetime.now().year
            if book.subtitle is None:
                book.subtitle = config.site_description
            if book.directory is None:
                book.directory = book.title

            book.directory = self.project_dir / book.directory

        books = []

        # For each book, identify root section by title
        # There is no other stuff in nav (anchor, uuid...), title
        # is the only way to identify a section (can be improved?)
        for book_config in self.config.books:
            for item in self.saved_nav.pages:
                if section := self._find_item_by_title(item, book_config.root):
                    break
            else:
                raise ValueError(
                    f"Root section {book_config.root} not found in documentation."
                )

            book = Book(section, book_config, self)
            books.append(book)

        # Build each book
        for book in books:
            book.build()

    def _find_item(self, item: StructureItem, cb: callable):
        if cb(item):
            return item
        for child in item.children or []:
            if result := self._find_item(child, cb):
                return result
        return None

    def _find_item_by_title(self, item: StructureItem, title: str):
        return self._find_item(item, lambda item: item.title == title)

    def _build_nav(self, section: Section, node):
        for child in section.children:
            if child.is_page:
                node.append(child.file.src_path)
            else:
                new_node = []
                node.append([child.title, new_node])
                _build_nav(child, new_node)

    def _nav_map(self, section: StructureItem, cb: callable, level: int = 0):
        cb(section, level)
        for child in section.children or []:
            _nav_map(child, cb, level + 1)


class Book:
    def __init__(self, section: StructureItem, config: BookConfig, plugin: Books):
        self.plugin = plugin
        self.section = section
        self.config = config

        self.files = self._fetch_files(self.section)

        self._propagate_meta(self.section, config.base_level)

        self.frontmatter = []
        self.mainmatter = []
        self._sort_by_part(self.section)

        embed()

    def _fetch_files(self, item: StructureItem):
        files = []
        for child in item.children or []:
            if child.is_page:
                files.append(child.file)
            else:
                files.extend(self._fetch_files(child))
        return files

    def _propagate_meta(self, item: StructureItem, level=0, numbered=True):
        item.level = level
        item.numbered = numbered
        item.drop_title = False

        if getattr(item.parent, "frontmatter", False):
            item.frontmatter = True
        if item.is_page:
            item.tex_path = item.file.src_path.replace(".md", ".tex")
            if self.config.index_is_foreword and item.file.name == "index":
                if self.config.drop_title_index:
                    item.drop_title = True
                    # level -= 1
                item.numbered = False

        for child in item.children or []:
            if child.title in self.config.frontmatter:
                child.frontmatter = True
            self._propagate_meta(child, level + 1, numbered=numbered)

    def _sort_by_part(self, item: StructureItem):
        if getattr(item, "frontmatter", False):
            self.frontmatter.append(item)
        else:
            self.mainmatter.append(item)
        for section in item.children or []:
            self._sort_by_part(section)

    def render_cover(self, renderer: LaTeXRenderer):
        return renderer.formatter[f"covers_{self.config.cover.name}"](self.config.cover)

    def _get_latex(self, elements: List[StructureItem], renderer: LaTeXRenderer):
        latex = []
        for element in elements:
            if element.is_page:
                latex.append(
                    renderer.formatter.include(element.tex_path, title=element.title)
                )
            elif element.level > self.config.base_level:
                latex.append(
                    renderer.formatter.heading(
                        element.title, level=element.level, numbered=True
                    )
                )

        return "\n".join(latex)

    def build(self):
        self.config.directory.mkdir(exist_ok=True)
        renderer = LaTeXRenderer(self.config.directory, self.config)

        # Build all files
        for file in self.files:
            self._build_file(file, renderer)

        # Remove unused objets (list build/assets directors and remove those that are not in assets_map keys)
        assets_map = renderer.get_assets_map()
        if self.config.debug.clean_assets:
            for file in (self.config.folder / "assets/").iterdir():
                if file not in assets_map and file.is_file():
                    log.info(f"Removing unused asset {file}")
                    file.unlink()

        (build_dir / "assets_map.yml").write_text(
            yaml.dump(assets_map, default_flow_style=False, allow_unicode=True)
        )

        # Build index page
        self._get_latex(self.frontmatter, renderer)
        index = renderer.formatter.template(
            title=self.config.title,
            author=self.config.author,
            subtitle=self.config.subtitle,
            email=self.config.email,
            year=self.config.year,
            frontmatter=self._get_latex(self.frontmatter, renderer),
            mainmatter=self._get_latex(self.mainmatter, renderer),
        )
        (self.config.folder / "index.tex").write_text(index)

        (self.config.folder / "acronyms.tex").write_text(renderer.get_list_acronyms())
        (self.config.folder / "glossary.tex").write_text(renderer.get_list_glossary())
        (self.config.folder / "solutions.tex").write_text(renderer.get_list_solutions())
        (self.config.folder / "cover.tex").write_text(self.render_cover(renderer))

        # Copy class file
        shutil.copy2(
            Path(__file__).parent / "latex/templates/mkbook.cls",
            build_dir / "mkbook.cls",
        )

        self._copy_assets()

    def _build_file(self, file: Path, renderer: LaTeXRenderer):
        log.info("Processing LaTeX '%s' ...", file.src_path)
        path = self.config.directory / file.page.tex_path
        path.parent.mkdir(parents=True, exist_ok=True)

        html = file.page.content

        if self.config.save_html:
            path.with_suffix(".html").write_text(html)

        latex = renderer.render(
            html,
            self.config.directory,
            Path(file.abs_src_path),
            base_level=file.page.level,
            numbered=file.page.numbered,
            drop_title=file.page.drop_title,
        )

        path.write_text(latex)

    def _copy_assets(self):
        """Optional assets can be copied to the LaTeX build directory
        such as .latexmkrc, .bib files, etc."""
        for src_pattern, dest_dir in self.config.copy_files.items():
            src_pattern = self.plugin.project_dir / src_pattern
            dest_dir = self.config.folder / dest_dir
            if "*" not in src_pattern.name and not src_pattern.exists():
                log.warning("Pattern %s does not exist", src_pattern)
                continue
            for src in src_pattern.parent.glob(src_pattern.name):
                dest = dest_dir
                log.info("Copying %s to %s", src, dest)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
