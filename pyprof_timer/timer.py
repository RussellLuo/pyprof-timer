# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import functools

import monotonic


class _Context(object):
    """The context class specially used to create a default context."""
    pass


class Timer(object):
    """The base class for profiling a Python function or snippet.

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

    __default_ctx = _Context()
    _ctx_timers = '_Timer_timers'

    def __init__(self, name, parent_name=None, dummy=False):
        self._name = name
        self._parent_name = parent_name
        self._dummy = dummy

        self._start = None
        self._stop = None
        self._children = []

        if self._dummy:
            # If the timer is dummy (which means it will not be used as
            # a decorator), then it will always be defined inside the request
            # context, and usually the user will not call .start()
            # (and .stop()) on the dummy timer, so it is safe and *necessary*
            # to do context-related operations here.
            self._attach_to_context(self._name, self)
            if self._parent_name is not None:
                self.parent.add_child(self)

    def _get_context(self):
        """Returns the default context.

        NOTE: You should customize this method to use the framework-specific
              context implementation if you are profiling the web service code.
        """
        return self.__default_ctx

    def _attach_to_context(self, name, timer):
        """Attach the given `timer` to the context."""
        timers = self._timers
        if name in timers:
            raise RuntimeError('timer name "%s" is duplicated' % name)
        timers[name] = timer

    @property
    def _timers(self):
        """Returns the timers attached to the context."""
        ctx = self._get_context()

        timers = getattr(ctx, self._ctx_timers, None)
        if timers is None:
            timers = {}
            setattr(ctx, self._ctx_timers, timers)

        return timers

    def add_child(self, timer):
        """Add the given `timer` as a child of the current timer."""
        self._children.append(timer)

    @property
    def name(self):
        return self._name

    @property
    def parent(self):
        timers = self._timers
        if self._parent_name not in timers:
            timers[self._parent_name] = self.__class__(self._parent_name, dummy=True)
        return timers[self._parent_name]

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
            self._attach_to_context(self._name, self)
            if self._parent_name is not None:
                self.parent.add_child(self)

        self._start = monotonic.monotonic()
        return self

    def stop(self):
        if not self._dummy and self._start is None:
            raise RuntimeError('timer %s: .start() has not been called' % self._name)

        self._stop = monotonic.monotonic()
        return self

    def span(self, unit='s'):
        """Returns the elapsed time as a fraction.

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
