import time

from flask import Flask
from pyprof_timer.contrib.flask import FlaskTimer as Timer
from pyprof_timer.tree import Tree

app = Flask(__name__)


@Timer('f1', parent_name='hello')
def f1():
    with Timer('time.sleep(1)', parent_name='f1'):
        time.sleep(1)

    time.sleep(0.1)


@Timer('f2', parent_name='hello')
def f2():
    with Timer('time.sleep(1.5)', parent_name='f2'):
        time.sleep(1.5)

    time.sleep(0.1)


@app.route("/")
def hello():
    t = Timer('hello', dummy=True)

    f1()
    f2()

    print(Tree(t, span_unit='ms'))

    return "Hello World!"
