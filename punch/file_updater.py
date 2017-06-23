import os
import six

from punch.replacer import Replacer


class FileUpdater(object):
    def __init__(self, file_configuration):
        self.file_configuration = file_configuration
        self.replacer = Replacer(file_configuration.config['serializer'])

    def __call__(self, current_version, new_version):
        if not os.path.exists(self.file_configuration.path):
            if six.PY2:
                raise IOError(
                    "The file {} does not exist".format(
                        self.file_configuration.path
                    )
                )
            else:
                raise FileNotFoundError(
                    "The file {} does not exist".format(
                        self.file_configuration.path
                    )
                )

        with open(self.file_configuration.path, 'r') as f:
            old_file_content = f.read()

        new_file_content = self.replacer(old_file_content,
                                         current_version, new_version)

        if six.PY2:
            new_file_content = new_file_content.encode('utf8')

        with open(self.file_configuration.path, 'w') as f:
            f.write(new_file_content)

    def get_summary(self, current_version, new_version):
        return self.replacer.run_all_serializers(current_version, new_version)
