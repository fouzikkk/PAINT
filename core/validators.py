from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class DigitPasswordValidator:
    def validate(self, password, user=None):
        if not any(char.isdigit() for char in password):
            raise ValidationError(
                _('Hasło musi zawierać co najmniej jedną cyfrę.'),
                code='password_no_digit',
            )

    def get_help_text(self):
        return _('Hasło musi zawierać co najmniej jedną cyfrę.')
