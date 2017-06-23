import six
import collections
from jinja2 import Template


class Replacer:
    def __init__(self, serializers):
        if isinstance(serializers, collections.MutableSequence):
            self.serializers = [Template(s) for s in serializers]
        else:
            self.serializers = [Template(serializers)]

    def __call__(self, text, current_version, new_version):
        if six.PY2:
            text = text.decode('utf8')

        new_text = text
        for serializer in self.serializers:
            search_pattern = serializer.render(
                **dict(current_version.simplify())
            )
            replace_pattern = serializer.render(**dict(new_version.simplify()))

            new_text = new_text.replace(search_pattern, replace_pattern)

        return new_text

    def run_all_serializers(self, current_version, new_version):
        summary = []
        for serializer in self.serializers:
            summary.append((
                serializer.render(**dict(current_version.simplify())),
                serializer.render(**dict(new_version.simplify()))
            ))

        return summary

    def run_main_serializer(self, current_version, new_version):
        return self.run_all_serializers(current_version, new_version)[0]
