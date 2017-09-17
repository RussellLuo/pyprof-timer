# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import functools
import threading

import monotonic


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
    """The map class that stores a timer mapping, which is attached
    to a specific context.
    """

    _ctx_timers_name = '_TimerMap_timers'
    _ctx_first_timer_name = '_TimerMap_first_timer'

    def get_timers(self, context):
        """Return the timers attached to the given context."""
        timers = getattr(context, self._ctx_timers_name, None)
        if timers is None:
            timers = {}
            setattr(context, self._ctx_timers_name, timers)
        return timers

    def get_first_timer(self, context):
        """Return the first timer attached to the given context."""
        return getattr(context, self._ctx_first_timer_name, None)

    def set_first_timer(self, context, timer):
        """Set the given timer as the first timer attached
        to the given context.
        """
        return setattr(context, self._ctx_first_timer_name, timer)

    def get_timer(self, context, name, timer_class=None):
        """Return a specific timer with the given name
        attached to the given context.
        """
        timers = self.get_timers(context)
        timer = timers.get(name)
        if timer is None and timer_class is not None:
            # non-None `timer_class` hints that we need to create a
            # dummy timer if it does not exist.
            timer = timers[name] = timer_class(name, dummy=True)
        return timer

    def attach(self, context, name, timer):
        """Attach the given `timer` to the given context."""
        # Set the first attached timer if it does not exist.
        if self.get_first_timer(context) is None:
            self.set_first_timer(context, timer)

        timers = self.get_timers(context)
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

        if self._dummy:
            # If the timer is dummy (which means it will not be used as
            # a decorator), then it will always be defined inside the request
            # context, and usually the user will not call .start()
            # (and .stop()) on the dummy timer, so it is safe and *necessary*
            # to do context-related operations here.
            self._timer_map.attach(self.get_context(), self._name, self)
            if self._parent_name is not None:
                self.parent.add_child(self)

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
        return cls._timer_map.get_timers(cls.get_context())

    @classproperty
    def first(cls):
        """Return the first timer attached to the context."""
        return cls._timer_map.get_first_timer(cls.get_context())

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
        return self._timer_map.get_timer(self.get_context(),
                                         self._parent_name, self.__class__)

    @property
    def children(self):
        return self._children

    def start(self):
        if not self._dummy:
            # If the timer is not dummy (which means it may be used as
            # a decorator), there are times when the timer is instantiated
            # outside the request context, so the following two
            # context-related operations are delayed from the init-phase
            # to the start-phase (here).
            self._timer_map.attach(self.get_context(), self._name, self)
            if self._parent_name is not None:
                self.parent.add_child(self)

        self._start = monotonic.monotonic()
        return self

    def stop(self):
        if not self._dummy and self._start is None:
            raise RuntimeError('timer %s: .start() has not been called' % self._name)

        self._stop = monotonic.monotonic()

        # If a callback function is given, call it after the timer is stopped.
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

    def __call__(self, func):
        """Make the timer object to be a decorator."""
        if self._dummy:
            raise RuntimeError('Dummy timer ought not to be used as a decorator')

        @functools.wraps(func)
        def decorator(*args, **kwargs):
            self.start()
            try:
                return func(*args, **kwargs)
            finally:
                self.stop()
        return decorator

    def __enter__(self):
        """Make the timer object to be a context manager."""
        self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        """Make the timer object to be a context manager."""
        self.stop()
