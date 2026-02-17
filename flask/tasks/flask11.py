from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    # get the name from URL query parameter
    name = request.args.get('name')

    # if name is provided
    if name:
        return f"<h1>HELLO {name.upper()}</h1>"
    else:
        return "<h1>Please provide a name in the URL</h1>"

if __name__ == '__main__':
    app.run(debug=True)
