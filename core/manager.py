# core/manager.py
import importlib
import os
import pkgutil

class SourceManager:
    def __init__(self):
        self.sources = []
        self._load_sources()

    def _load_sources(self):
        # load modules from sources package
        pkg_name = "sources"
        package = importlib.import_module(pkg_name)
        package_path = package.__path__[0]
        for finder, name, ispkg in pkgutil.iter_modules([package_path]):
            if name.startswith("_"):
                continue
            mod = importlib.import_module(f"{pkg_name}.{name}")
            # expect a 'Source' class in module
            if hasattr(mod, "Source"):
                try:
                    self.sources.append(mod.Source())
                except Exception:
                    pass
                  
