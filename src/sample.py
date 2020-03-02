from flask import Flask, render_template

from flask_ask import Ask, statement, question, session

app = Flask(__name__)

ask = Ask(app, "/message")


@app.route('/')
def homepage():
    return "hi there, how ya doin?"


@ask.launch
def welcome():
    print("HI!")
    return question("Welcome to my Print Message app, what do you want to do, my broses?")


@ask.intent("YesIntent")
def printMessage():
    print("HELLO!")
    return statement("Message Printed!")


if __name__ == "__main__":
    app.run(debug=True)
