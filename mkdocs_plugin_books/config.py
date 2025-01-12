from typing import Any, Dict, Optional
from .transformers import to_kebab_case
from mkdocs.config import base, config_options as c

class CoverConfig(base.Config):
    name = c.Type(str, default='default') # Cover template name
    color = c.Type(str, default='black') # Primary color
    logo = c.Type(str) # Logo path

class BookConfig(base.Config):
    build_dir = c.Type(str, default="")
    save_html = c.Type(bool, default=False)
    mermaid_config = c.Type(str, default=None)
    project_dir = c.Type(str, default=None)  # Set internally

    root = c.Type(str)  # Section title used as root
    title = c.Type(str)  # Book title
    subtitle = c.Type(str)
    author = c.Type(str)
    year = c.Type(int)
    email = c.Type(str)

    folder = c.Dir()
    frontmatter = c.ListOfItems(c.Type(str), default=[])
    backmatter = c.ListOfItems(c.Type(str), default=[])
    base_level = c.Type(int, default=-2)
    copy_files =  Optional[Dict[str, str]] = {}

    index_is_foreword = c.Type(bool, default=False)
    drop_title_index = c.Type(bool, default=False)
    cover = c.SubConfig(CoverConfig)

    def set_folder_and_build_dir(self):
        """Set folder to title in kebab case if not provided"""
        if self.folder is None and self.title is not None:
            self.folder = to_kebab_case(self.title)

        return self


class LaTeXConfig(base.Config):
    enabled = c.Type(bool, default=True)
    books = c.ListOfItems(c.SubConfig(BookConfig))
    clean_assets = c.Type(bool, default=True)

    @classmethod
    def propagate(cls, data: Any) -> Any:
        for book in data.books:
            to_propagate = ["build_dir", "mermaid_config", "save_html", "project_dir"]
            for key in to_propagate:
                if getattr(book, key) is None:
                    setattr(book, key, getattr(data, key))
        return data

    #model_config = ConfigDict(extra="forbid")

    def add_extra(self, **extra_data):
        """Allow to add extra data to the configuration object."""
        for key, value in extra_data.items():
            object.__setattr__(self, key, value)
            object.__setattr__(self, key, value)
            object.__setattr__(self, key, value)
            object.__setattr__(self, key, value)
