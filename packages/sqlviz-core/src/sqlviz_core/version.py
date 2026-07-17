from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("sqlviz-core")
except PackageNotFoundError:
    __version__ = "dev"
