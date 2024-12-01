import os

def find_extensions(base_path, base_package):
    extensions = set()
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                relative_path = os.path.relpath(root, base_path)
                if relative_path == ".":
                    module_path = f"{base_package}.{file[:-3]}"
                else:
                    module_path = f"{base_package}.{relative_path.replace(os.sep, '.')}.{file[:-3]}"
                extensions.add(module_path)
    return extensions

EXTENSIONS = find_extensions(__path__[0], __package__)
