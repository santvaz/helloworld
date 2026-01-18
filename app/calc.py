import app


class InvalidPermissions(Exception):
    pass


class Calculator:
    def add(self, x, y):
        self.check_types(x, y)
        return x + y

    def substract(self, x, y):
        self.check_types(x, y)
        return x - y

    def multiply(self, x, y):
        self.check_types(x, y)
        return x * y

    def divide(self, x, y):
        self.check_types(x, y)
        if y == 0:
            raise TypeError("Division by zero is not possible")
        return x / y

    def power(self, x, y):
        self.check_types(x, y)
        return x ** y

    def check_types(self, x, y):
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError("Parameters must be numbers")


def convert_to_number(operand):
    """
    Convierte la entrada en número entero o float.
    Lanza TypeError para inputs no convertibles o no string.
    """
    if not isinstance(operand, str):
        raise TypeError("Operator cannot be converted to number")
    if operand == "":
        raise TypeError("Operator cannot be converted to number")

    try:
        if "." in operand:
            return float(operand)
        return int(operand)
    except ValueError:
        raise TypeError("Operator cannot be converted to number")


def InvalidConvertToNumber(operand):  # pragma: no cover
    try:
        if "." in operand:
            return float(operand)
        return int(operand)
    except ValueError:
        raise TypeError("Operator cannot be converted to number")


def validate_permissions(operation, user):  # pragma: no cover
    print(f"checking permissions of {user} for operation {operation}")
    return user == "user1"


if __name__ == "__main__":  # pragma: no cover
    calc = Calculator()
    result = calc.add(2, 2)
    print(result)
