import time

from flask import Flask
from pyprof_timer import Tree
from pyprof_timer.contrib.flask import FlaskTimer as Timer

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


def show(t):
    print(Tree(t, span_unit='ms'))


@app.route("/")
@Timer('hello', on_stop=show)
def hello():
    f1()
    f2()
    return "Hello World!"
