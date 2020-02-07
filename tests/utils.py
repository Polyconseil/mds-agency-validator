import datetime
import random
import string


def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def random_year():
    return random.randint(1800, 2100)


def get_timestamp():
    return int(datetime.datetime.now().timestamp())
