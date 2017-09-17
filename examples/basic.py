import time

from flask import Flask
from pyprof_timer import Tree
from pyprof_timer.contrib.flask import FlaskTimer as Timer

app = Flask(__name__)


def f1():
    t = Timer('time.sleep(1)', parent_name='f1').start()
    time.sleep(1)
    t.stop()

    time.sleep(0.1)


def f2():
    t = Timer('time.sleep(1.5)', parent_name='f2').start()
    time.sleep(1.5)
    t.stop()

    time.sleep(0.1)


@app.route("/")
def hello():
    t = Timer('f1', parent_name='hello').start()
    f1()
    t.stop()

    t = Timer('f2', parent_name='hello').start()
    f2()
    t.stop()

    print(Tree(Timer.first.parent, span_unit='ms'))

    return "Hello World!"
