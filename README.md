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

As an example, we can do a simple profiling on normal Python code:

```python

# example.py

import time

from pyprof_timer import Timer, Tree


def main():
    t = Timer('sleep1', parent_name='main').start()
    time.sleep(1)
    t.stop()

    t = Timer('sleep2', parent_name='main').start()
    time.sleep(1.5)
    t.stop()

    print(Tree(t.parent, span_unit='ms'))


if __name__ == '__main__':
    main()
```

Run the example code:

```bash
$ python example.py
```

and it will show you the profiling result:

```
main (2507.00 ms)
├── sleep1 (1002.23 ms)
└── sleep2 (1504.77 ms)

```


## Supported frameworks

While you can do profiling on normal Python code, as a web developer, chances are that you will usually do profiling on web service code.

Currently supported web frameworks:

- [Flask](http://flask.pocoo.org/)


## Examples

For profiling web service code (involving web requests), see [examples](examples) as follows:

- [normal](examples/normal.py)
- [context manager](examples/context_manager.py)
- [decorator](examples/decorator.py)


## License

[MIT](http://opensource.org/licenses/MIT)
