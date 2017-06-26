import sys


def import_file(module_name, filepath):
    if sys.version_info < (3, 0):
        import imp

        module = imp.load_source(module_name, filepath)

    elif sys.version_info < (3, 5):
        from importlib.machinery import SourceFileLoader

        try:
            module = SourceFileLoader(module_name, filepath).load_module()
        except FileNotFoundError:
            raise ValueError(
                "The module file {} cannot be found.".format(filepath))
        except ImportError:
            raise ValueError(
                "The module file {} cannot imported due to an error.".format(
                    filepath))

    else:
        import importlib.util

        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

    return module
