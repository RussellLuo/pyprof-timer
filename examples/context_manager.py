import time

from flask import Flask
from pyprof_timer.contrib.flask import FlaskTimer as Timer
from pyprof_timer.tree import Tree

app = Flask(__name__)


def f1():
    with Timer('time.sleep(1)', parent_name='f1'):
        time.sleep(1)

    time.sleep(0.1)


def f2():
    with Timer('time.sleep(1.5)', parent_name='f2'):
        time.sleep(1.5)

    time.sleep(0.1)


@app.route("/")
def hello():
    t = Timer('hello', dummy=True)

    with Timer('f1', parent_name='hello'):
        f1()

    with Timer('f2', parent_name='hello'):
        f2()

    print(Tree(t, span_unit='ms'))

    return "Hello World!"
