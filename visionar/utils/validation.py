import re
def lengthValidation(value, minimum, maximum):
	if len(value) < minimum or len(value) > maximum:
		return False
	else:
		return True

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def mailValidation(email):
	if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email):
		return False
	else:
		return True