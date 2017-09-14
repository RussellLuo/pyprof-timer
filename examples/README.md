# Examples

Some examples that illustrates how to do profiling on web service code.


## Run the API

```bash
$ FLASK_APP=normal.py flask run
# Or
$ FLASK_APP=context_manager.py flask run
# Or
$ FLASK_APP=decorator.py flask run
```

## Consume the API

```bash
$ curl localhost:5000
```

## See the profiling result

```
hello (2710.51 ms)
├── f1 (1106.89 ms)
│   └── time.sleep(1) (1002.38 ms)
└── f2 (1603.62 ms)
    └── time.sleep(1.5) (1503.24 ms)

```
