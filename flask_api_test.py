from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Math API! Use /add, /subtract, /multiply, or /divide."
@app.route('/add', methods=['GET'])
def add():
    num1 = float(request.args.get('num1', 0))
    num2 = float(request.args.get('num2', 0))
    result = num1 + num2
    return jsonify({"operation": "addition", "result": result})

@app.route('/subtract', methods=['GET'])
def subtract():
    num1 = float(request.args.get('num1', 0))
    num2 = float(request.args.get('num2', 0))
    result = num1 - num2
    return jsonify({"operation": "subtraction", "result": result})

@app.route('/multiply', methods=['GET'])
def multiply():
    num1 = float(request.args.get('num1', 0))
    num2 = float(request.args.get('num2', 0))
    result = num1 * num2
    return jsonify({"operation": "multiplication", "result": result})

@app.route('/divide', methods=['GET'])
def divide():
    num1 = float(request.args.get('num1', 0))
    num2 = float(request.args.get('num2', 1))  # Default to 1 to avoid division by zero
    if num2 == 0:
        return jsonify({"error": "Division by zero is not allowed"}), 400
    result = num1 / num2
    return jsonify({"operation": "division", "result": result})

if __name__ == '__main__':
    app.run()
    #app.run(host='0.0.0.0', port=5000, debug=True)
