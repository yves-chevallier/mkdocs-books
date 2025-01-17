from .helpers import to_kebab_case
from mkdocs.config import base, config_options as c
from mkdocs.config.base import Config


class CoverConfig(base.Config):
    name = c.Type(str, default="default")  # Cover template name
    color = c.Type(str, default="black")  # Primary color
    logo = c.Type(str)  # Logo path


class Debug(base.Config):
    save_html = c.Type(bool, default=False)
    """ Save intermediate HTML files for debugging. """


class BookConfig(base.Config):
    output_dir = c.Dir(default="books")
    """ Where to generate LaTeX books. """

    debug = c.SubConfig(Debug)
    """ Debugging options for developpers. """

    root = c.Type(str, default="")
    """ Section title to start the book from. """

    cover = c.SubConfig(CoverConfig)
    """ Book cover configuration. """

    base_level = c.Type(int, default=-2)
    """ Base level to start the book from (part, chapter, section...) """

    title = c.Type(str, default="Book")
    """ The title of your book. """

    subtitle = c.Optional(c.Type(str))
    """ The subtitle of your book. """

    author = c.Optional(c.Type(str))
    """ The author of the book. """

    year = c.Optional(c.Type(int))
    """ Release year of the book. """

    email = c.Optional(c.Type(str))
    """ Email displayed in the cover. """

    mermaid_config = c.Type(str, default="")
    folder = c.Dir(default=None)

    frontmatter = c.ListOfItems(c.Type(str), default=[])
    """ Sends some section titles into the frontmatter. """

    backmatter = c.ListOfItems(c.Type(str), default=[])
    """ Sends some section titles into the backmatter. """

    copy_files = c.Type(dict, default={})

    index_is_foreword = c.Type(bool, default=False)
    drop_title_index = c.Type(bool, default=False)

    def post_validation(self, config: Config, key_name: str) -> None:
        """Set folder to title in kebab case if not provided"""
        if self.folder is None and self.title is not None:
            self.folder = to_kebab_case(self.title)


class BooksConfig(base.Config):
    enabled = c.Type(bool, default=True)
    """ Enable Plugin: LaTeX Generation. """

    books = c.ListOfItems(c.SubConfig(BookConfig), default=[])
    """ List of books to generate. """

    clean_assets = c.Type(bool, default=True)
    """ Clean assets folder before generation (regenerate images). """

    # @classmethod
    # def propagate(cls, data: Any) -> Any:
    #     for book in data.books:
    #         to_propagate = ["build_dir", "mermaid_config", "save_html", "project_dir"]
    #         for key in to_propagate:
    #             if getattr(book, key) is None:
    #                 setattr(book, key, getattr(data, key))
    #     return data
