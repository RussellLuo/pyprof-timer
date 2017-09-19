import time

from flask import Flask
from pyprof_timer import Profiler, Tree
from pyprof_timer.contrib.flask import FlaskTimer as Timer

app = Flask(__name__)


def f1():
    time.sleep(1)


def f2():
    time.sleep(1.5)


def show(p):
    print(Tree(p.root, span_unit='ms'))


@app.route("/")
@Profiler(timer_class=Timer, on_disable=show)
def hello():
    f1()
    f2()
    return "Hello World!"
