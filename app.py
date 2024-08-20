from flask import Flask, jsonify

app = Flask(__name__)

on = False

@app.route('/check', methods=['GET'])
def check():
    global on
    on = some_function()
    return jsonify({"status": on})

def some_function():
    return True

if __name__ == '__main__':
    app.run(debug=True)