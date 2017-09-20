# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import collections
import functools
import threading

import monotonic
import six


class classproperty(property):
    """A decorator that converts a method into a read-only class property.

    Note:
        You ought not to set the value of classproperty-decorated attributes!
        The result of the behavior is undefined.
    """

    def __init__(self, fget, *args, **kwargs):
        super(classproperty, self).__init__(classmethod(fget),
                                            *args, **kwargs)

    def __get__(self, obj, cls):
        return self.fget.__get__(obj, cls)()


class _ThreadLocalContext(threading.local):
    """The thread-local context class that is thread safe."""
    pass


class _TimerMap(object):
    """The map class that manages a timer mapping, which is attached
    to a specific context.
    """

    _ctx_timers_name = '_TimerMap_timers'

    def get_map(self, context):
        """Return the timer mapping attached to the given context."""
        timers = getattr(context, self._ctx_timers_name, None)
        if timers is None:
            timers = collections.OrderedDict()
            setattr(context, self._ctx_timers_name, timers)
        return timers

    def get_first(self, context):
        """Return the first timer in the timer mapping."""
        timers = self.get_map(context)
        return next(iter(six.itervalues(timers)), None)

    def get(self, context, name):
        """Return a specific timer with the given name
        from the timer mapping.
        """
        timers = self.get_map(context)
        return timers.get(name)

    def add(self, context, name, timer):
        """Add the given timer into the timer mapping."""
        timers = self.get_map(context)
        if name in timers:
            raise RuntimeError('timer name "%s" is duplicated' % name)
        timers[name] = timer


class Timer(object):
    """The timer class for profiling a Python function or snippet.

    There are two types of timers:

        Normal timer -- a timer that actually calculates the consuming time,
                        you ought to call .start() and .stop() methods on it,
                        and the span of the timer is the stopping time minus
                        the starting time.

        Dummy timer  -- a timer that represents a virtual composition of all
                        its children timers, you need not to call .start()
                        or .stop() methods on it, and the span of the timer
                        is the sum of spans of all its children timers.
    """

    _default_ctx = _ThreadLocalContext()

    _timer_map = _TimerMap()

    def __init__(self, name, parent_name=None, on_stop=None,
                 dummy=False, display_name=None):
        self._name = name
        self._parent_name = parent_name
        self._on_stop_callback = on_stop
        self._dummy = dummy
        self._display_name = display_name or name

        self._start = None
        self._stop = None
        self._children = []

        if self._parent_name is not None:
            self.parent.add_child(self)

        self._timer_map.add(self.get_context(), self._name, self)

    @classmethod
    def get_context(cls):
        """Return the default context.

        NOTE: You can customize this method to use the framework-specific
              context implementation if you are profiling the web service code.
        """
        return cls._default_ctx

    @classproperty
    def timers(cls):
        """Return the timers attached to the context."""
        return cls._timer_map.get_map(cls.get_context())

    @classproperty
    def root(cls):
        """Return the root timer of the implicit entire timer tree, which is
        just the first timer attached to the context.
        """
        return cls._timer_map.get_first(cls.get_context())

    def add_child(self, timer):
        """Add the given `timer` as a child of the current timer."""
        self._children.append(timer)

    @property
    def name(self):
        return self._name

    @property
    def display_name(self):
        return self._display_name

    @property
    def parent(self):
        if self._parent_name is None:
            return None
        else:
            parent = self._timer_map.get(self.get_context(), self._parent_name)
            if parent is None:
                # We need to create a dummy parent timer if it does not exist.
                parent = self.__class__(self._parent_name, dummy=True)
            return parent

    @property
    def children(self):
        return self._children

    def start(self):
        self._start = monotonic.monotonic()
        return self

    def stop(self):
        if not self._dummy and self._start is None:
            raise RuntimeError('timer %s: .start() has not been called' % self._name)

        self._stop = monotonic.monotonic()

        # If a callback function is given, call it after this timer is stopped.
        if self._on_stop_callback is not None:
            self._on_stop_callback(self)

        return self

    def span(self, unit='s'):
        """Return the elapsed time as a fraction.

        unit:
            's'  -- in seconds (the default value)
            'ms' -- in milliseconds
            'us' -- in microseconds
        """
        multipliers = dict(s=1, ms=1000, us=1000000)
        assert unit in multipliers, '`unit` must be one of %s' % multipliers.keys()

        if self._dummy:
            # For dummy timer, return the sum of all children timers
            return sum(child.span(unit) for child in self._children)

        if self._stop is None:
            raise RuntimeError('timer %s: .stop() has not been called' % self._name)

        return (self._stop - self._start) * multipliers[unit]

    @classmethod
    def time(cls, name, parent_name=None, on_stop=None, display_name=None):
        """A decorator that will create a timer with the given arguments
        at runtime to profile the given function dynamically.
        """
        def wrapper(func):
            @functools.wraps(func)
            def decorator(*args, **kwargs):
                timer = cls(name, parent_name, on_stop, False, display_name)
                timer.start()
                try:
                    return func(*args, **kwargs)
                finally:
                    timer.stop()
            return decorator
        return wrapper

    def __enter__(self):
        """Make the timer object to be a context manager."""
        self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        """Make the timer object to be a context manager."""
        self.stop()
