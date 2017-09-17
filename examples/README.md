# Examples

Some examples that illustrates how to do profiling on web service code.


## Example APIs

### Manual profiling

- [basic](basic.py)
- [context manager](context_manager.py)
- [decorator](decorator.py)

### Automatic profiling

- [automatic](automatic.py)


## Run the example API

```bash
$ FLASK_APP=normal.py flask run
# Or
$ FLASK_APP=context_manager.py flask run
# Or
$ FLASK_APP=decorator.py flask run
# Or
$ FLASK_APP=automatic.py flask run
```

## Consume the example API

```bash
$ curl localhost:5000
```

## Check out the profiling result

### Manual profiling

```
2710.234ms  hello
├── 1105.160ms  f1
│   └── 1001.651ms  time.sleep(1)
└── 1605.074ms  f2
    └── 1504.913ms  time.sleep(1.5)

```

### Automatic profiling

```
2508.580ms  hello  [/Users/russellluo/projects/pyprof-timer/examples/automatic.py:22]
├── 1005.211ms  f1  [/Users/russellluo/projects/pyprof-timer/examples/automatic.py:10]
│   └── 1005.145ms  <time.sleep>
└── 1503.251ms  f2  [/Users/russellluo/projects/pyprof-timer/examples/automatic.py:14]
    └── 1503.165ms  <time.sleep>

```
