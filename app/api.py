from flask import Flask
import http.client
from app.calc import Calculator
from app.util import convert_to_number

api_application = Flask(__name__)
HEADERS = {"Content-Type": "text/plain"}
CALCULATOR = Calculator()


@api_application.route("/")
def hello():
    return "Hello from The Calculator!\n"


@api_application.route("/calc/add/<op_1>/<op_2>", methods=["GET"])
def add(op_1, op_2):
    try:
        num_1 = convert_to_number(op_1)
        num_2 = convert_to_number(op_2)
        return ("{}".format(CALCULATOR.add(num_1, num_2)), http.client.OK, HEADERS)
    except TypeError as e:
        return (str(e), http.client.BAD_REQUEST, HEADERS)


@api_application.route("/calc/substract/<op_1>/<op_2>", methods=["GET"])
def substract(op_1, op_2):
    try:
        num_1 = convert_to_number(op_1)
        num_2 = convert_to_number(op_2)
        return ("{}".format(CALCULATOR.substract(num_1, num_2)), http.client.OK, HEADERS)
    except TypeError as e:
        return (str(e), http.client.BAD_REQUEST, HEADERS)


if __name__ == "__main__":  # pragma: no cover
    # Permite ejecutar la app directamente (útil para stages Rest/Performance en Jenkins)
    api_application.run(host="0.0.0.0", port=5000)
