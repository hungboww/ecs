from rest_framework.exceptions import ValidationError

from core.user_files.models import UserFile
from core.user_files.exceptions import InvalidUserFileNameError


def user_file_name_validator(value):
    try:
        UserFile.deconstruct_name(value)
    except InvalidUserFileNameError:
        raise ValidationError("The user file name is invalid.", code="invalid")
