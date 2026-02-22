from .constants import MAX_STR_LENGTH


def truncate(value, length=MAX_STR_LENGTH):
    return value[:length] + '...' if len(value) > length else value
