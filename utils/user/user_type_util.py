from users import models


class UserType:
    def get_user_type(user_type):
        return UserType.is_valid_user_type(user_type)

    def is_valid_user_type(user_type, user_model=None):
        if user_type not in models.CustomUser.all_user_types:
            raise Exception(f"User type ({user_type}) does not exist")

        if user_model == models.UniversityUser and (user_type not in models.CustomUser.university_user_types):
            raise Exception(f"Wrong User type ({user_type}) for this Model User ({user_model})")

        if user_model == models.CustomUser and (user_type != models.CustomUser.super_user_type):
            raise Exception(f"Wrong User type ({user_type}) for this Model User ({user_model})")

        return user_type

    def get_user_type_by_model(user_model):
        if user_model == models.CustomUser:
            return models.CustomUser.super_user_type

        if user_model == models.UniversityUser:
            return models.CustomUser.university_user_type

        raise Exception(f"Not exist User type by this Model User ({user_model})")
