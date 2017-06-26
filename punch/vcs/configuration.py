import collections

from jinja2 import Template

from punch.defaults import DEFAULT_COMMIT_MESSAGE


class VCSConfiguration(object):
    def __init__(self, name, options, global_variables, special_variables,
                 commit_message=None, finish_release=True):
        self.name = name

        if commit_message is None:
            commit_message = DEFAULT_COMMIT_MESSAGE

        commit_message_template = Template(commit_message)

        template_variables = {}
        template_variables.update(global_variables)
        template_variables.update(special_variables)

        self.commit_message = commit_message_template.render(
            **template_variables)
        self.finish_release = finish_release

        self.options = {}
        for key, value in options.items():
            if isinstance(value, collections.Sequence):
                value_template = Template(value)
                self.options[key] = value_template.render(**template_variables)
            else:
                self.options[key] = value

        self.options.update(special_variables)

    @classmethod
    def from_dict(cls, vcs_configuration,
                  global_variables, special_variables):
        return VCSConfiguration(
            vcs_configuration['name'],
            vcs_configuration.get('options', {}),
            global_variables,
            special_variables,
            vcs_configuration.get('commit_message', None),
            vcs_configuration.get('finish_release', True)
        )
