import cerberus
import re


class MdsValidator(cerberus.Validator):
    """Our custom cerberus validator

    We added an uuid type that is a string formated uuid
    """

    def _validate_type_uuid(self, value):
        if not isinstance(value, str):
            return False
        re_uuid = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', re.I)
        return bool(re_uuid.match(value))
