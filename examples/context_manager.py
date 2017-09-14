import time

from flask import Flask
from pyprof_timer import Tree
from pyprof_timer.contrib.flask import FlaskTimer as Timer

app = Flask(__name__)


def f1():
    with Timer('time.sleep(1)', parent_name='f1'):
        time.sleep(1)

    time.sleep(0.1)


def f2():
    with Timer('time.sleep(1.5)', parent_name='f2'):
        time.sleep(1.5)

    time.sleep(0.1)


def show(t):
    print(Tree(t, span_unit='ms'))


@app.route("/")
def hello():
    with Timer('hello', on_stop=show):
        with Timer('f1', parent_name='hello'):
            f1()
        with Timer('f2', parent_name='hello'):
            f2()
        return "Hello World!"
