# pyprof-timer

A timer for profiling a Python function or snippet.


## Installation

Release version:

```bash
$ pip install pyprof-timer
```

Development version:

```bash
$ pip install -e git+https://github.com/RussellLuo/pyprof-timer.git#egg=pyprof-timer
```


## Quick start

### Manual profiling

Sometimes, we only want to measure the execution time of partial snippets or a few functions, then we can inject all timing points into our code manually by leveraging `Timer`:

```python

# manual_example.py

import time

from pyprof_timer import Timer, Tree


def main():
    t = Timer('sleep1', parent_name='main').start()
    time.sleep(1)
    t.stop()

    t = Timer('sleep2', parent_name='main').start()
    time.sleep(1.5)
    t.stop()

    print(Tree(Timer.root))


if __name__ == '__main__':
    main()
```

Run the example code:

```bash
$ python manual_example.py
```

and it will show you the profiling result:

```
2.503s  main
├── 1.001s  sleep1
└── 1.501s  sleep2

```

### Automatic profiling

More commonly, chances are that we want to measure the execution time of an entry function and all its subfunctions. In this case, it's too tedious to do it manually, and we can leverage `Profiler` to inject all the timing points for us automatically:

```python

# automatic_example.py

import time # line number 1

from pyprof_timer import Profiler, Tree


def f1():
    time.sleep(1)


def f2():
    time.sleep(1.5)


def show(p):
    print(Tree(p.root))


@Profiler(on_disable=show)
def main():
    f1()
    f2()


if __name__ == '__main__':
    main()
```

Run the example code:

```bash
$ python automatic_example.py
```

and it will show you the profiling result:

```
2.506s  main  [automatic_example.py:18]
├── 1.001s  f1  [automatic_example.py:6]
│   └── 1.001s  <time.sleep>
└── 1.505s  f2  [automatic_example.py:10]
    └── 1.505s  <time.sleep>

```


## Supported frameworks

While you can do profiling on normal Python code, as a web developer, chances are that you will usually do profiling on web service code.

Currently supported web frameworks:

- [Flask](http://flask.pocoo.org/)


## Examples

For profiling web service code (involving web requests), check out [examples](examples).


## License

[MIT](http://opensource.org/licenses/MIT)
