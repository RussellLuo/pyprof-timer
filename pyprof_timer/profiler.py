# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import collections
import functools
import re
import sys
import time

from .timer import Timer


class _NameCounter(object):
    """The counter class that counts a given function name in a given frame,
    and returns an unique name for each function, in case that it has the
    same name as other functions in the same frame.
    """

    _ctx_counts_name = '_NameCounter_counts'

    def __init__(self, context):
        self._counts = getattr(context, self._ctx_counts_name, None)
        if self._counts is None:
            self._counts = collections.defaultdict(int)
            setattr(context, self._ctx_counts_name, self._counts)

    def incr(self, frame, name):
        self._counts[(frame, name)] += 1

    def raw_name(self, frame, name):
        return '%s%s' % (frame, name)

    def unique_name(self, frame, name):
        """Return an unique name for function `name` in frame `frame`."""
        count = self._counts[(frame, name)]
        unique_name = self.raw_name(frame, name)
        if count > 1:
            unique_name += str(count - 1)
        return unique_name


class Profiler(object):
    """The profiler class that automatically injects a timer for each
    function to measure its execution time.
    """

    def __init__(self, timer_class=Timer, on_disable=None):
        self._timer_class = timer_class
        self._on_disable_callback = on_disable

        self._counter = None

        # Mainly due to the side effect of disabling the profiler.
        self._excluded_func_names = (
            '<sys.setprofile>',
            # the following line number need to be updated if the
            # actual line number of the method `disable()` is changed.
            self._format_func_name(
                re.sub('(\.pyc)$', '.py', __file__), 80, 'disable')
        )

    @staticmethod
    def _format_func_name(filename, firstlineno, name):
        return '{2}  [{0}:{1}]'.format(filename, firstlineno, name)

    def _get_func_name(self, frame):
        fcode = frame.f_code
        fn = (fcode.co_filename, fcode.co_firstlineno, fcode.co_name)
        return self._format_func_name(*fn)

    def enable(self):
        # It's necessary to delay calling `timer_class.get_context()` here
        # if this profiler is used as a decorator.
        self._counter = _NameCounter(self._timer_class.get_context())

        sys.setprofile(self._profile)
        return self

    def disable(self):
        sys.setprofile(None)

        # If a callback function is given, call it after the timer is disabled.
        if self._on_disable_callback is not None:
            self._on_disable_callback(self)

        return self

    @property
    def first(self):
        """The first timer attached to the context."""
        return self._timer_class.first

    def _profile(self, frame, event, arg):
        """The core handler used as the system’s profile function."""
        if event in ('c_call', 'c_return'):  # C function
            func_name = '<%s.%s>' % (arg.__module__, arg.__name__)
            parent_frame = frame
        else:  # Python function
            func_name = self._get_func_name(frame)
            parent_frame = frame.f_back

        if event in ('call', 'c_call'):
            # Ignore the `call` event of some excluded functions.
            if func_name not in self._excluded_func_names:
                self._counter.incr(frame, func_name)

                unique_func_name = self._counter.unique_name(frame, func_name)
                parent_name = self._get_func_name(parent_frame)
                unique_parent_name = self._counter.unique_name(
                    parent_frame, parent_name)

                # Create and start a timer for the entering function
                self._timer_class(
                    unique_func_name,
                    parent_name=unique_parent_name,
                    display_name=func_name
                ).start()
        elif event in ('return', 'c_return'):
            unique_func_name = self._counter.unique_name(frame, func_name)
            timer = self._timer_class.timers.get(unique_func_name)
            if timer is not None:
                # Stop the timer for the exiting function
                timer.stop()

    def __call__(self, func):
        """Make the profiler object to be a decorator."""
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            self.enable()
            try:
                return func(*args, **kwargs)
            finally:
                self.disable()
        return decorator
