import os, importlib

MODULES_PATH = os.path.join(os.path.dirname(__file__), "..", "modules")

def iter_modules():
    modules = {}
    for category in os.listdir(MODULES_PATH):
        cat_path = os.path.join(MODULES_PATH, category)
        if os.path.isdir(cat_path) and not category.startswith("__"):
            mods = []
            for f in os.listdir(cat_path):
                if f.endswith(".py") and f != "__init__.py":
                    mods.append(f[:-3])
            if mods:
                modules[category] = mods
    return modules