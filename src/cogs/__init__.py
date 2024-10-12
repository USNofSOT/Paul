from pkgutil import walk_packages

EXTENTIONS = set(
    extension.name for extension in walk_packages(__path__, f'{__package__}.')
)