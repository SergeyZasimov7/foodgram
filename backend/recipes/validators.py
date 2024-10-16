import re

from django.core.exceptions import ValidationError


def validate_username(username):
    regex = r'[\w.@+-]+'
    invalid_chars = re.sub(regex, '', username)
    if invalid_chars:
        invalid_chars_str = ''.join(set(invalid_chars))
        raise ValidationError(
            f'Недопустимые символы: {invalid_chars_str}.'
        )
    return username
