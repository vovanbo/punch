import sys


class Action:
    @classmethod
    def factory(cls, **kwargs):
        action_type = kwargs.pop('type')
        class_name = action_type.title().replace("_", "") + 'Action'
        action_class = getattr(sys.modules[__name__], class_name)
        return action_class(**kwargs)

    def process_version(self, version):
        raise NotImplementedError()


class RefreshAction(Action):
    def __init__(self, refresh_fields, fallback_field):
        self.refresh_fields = refresh_fields
        self.fallback_field = fallback_field

    def process_version(self, version):
        raise NotImplementedError()


class ConditionalResetAction(Action):
    def __init__(self, field, update_fields=None):
        self.field = field
        self.update_fields = update_fields

    def process_version(self, version):
        new_version = version.copy()

        reset_part = new_version[self.field]

        for f in self.update_fields:
            update_part = new_version[f]
            update_part.inc()

        if new_version == version:
            reset_part.inc()
        else:
            reset_part.reset()

        return new_version
