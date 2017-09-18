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

    @staticmethod
    def raw_name(frame, name):
        return '%s%s' % (frame, name)

    def incr(self, frame, name):
        self._counts[(frame, name)] += 1

    def unique_name(self, frame, name):
        """Return an unique name for function `name` in frame `frame`."""
        count = self._counts[(frame, name)]
        unique_name = self.raw_name(frame, name)
        if count > 1:
            unique_name += str(count - 1)
        return unique_name


class _FrameDepth(object):

    _ctx_first_frame_name = '_FrameDepth_first_frame'

    def __init__(self, context):
        self._context = context

    def get_first_frame(self):
        """Return the first frame attached to the context."""
        return getattr(self._context, self._ctx_first_frame_name, None)

    def set_first_frame(self, frame):
        """Set the given frame as the first frame attached to the context."""
        setattr(self._context, self._ctx_first_frame_name, frame)

    def get_frame_depth(self, frame):
        """Return the depth from the given frame to the first frame."""
        # Two scenarios:
        #
        # 1. If the profiler is used as a decorator, the frame of the
        #    decorated function is the first frame, then the frame depths
        #    of other functions can be calculated correctly, since all the
        #    other functions are sub-functions of the first function.
        #
        # 2. If the profiler is used to wrap several functions at the same
        #    level, the frame of the first function is the first frame, but
        #    the frame depths of other functions at the same level can not
        #    be calculated correctly, since we can not compare the frame of
        #    any other same-leveled function with the first frame.
        #
        # To handle the above two cases consistently:
        #     1. We define the *root frame* as the parent frame of the
        #        first frame.
        #     2. Then the actual depth is the root depth minus one.
        root = self.get_first_frame().f_back

        depth = 0
        while frame != root:
            frame = frame.f_back
            depth += 1

        return depth - 1


class Profiler(object):
    """The profiler class that automatically injects a timer for each
    function to measure its execution time.
    """

    def __init__(self, timer_class=Timer, depth=None, on_disable=None):
        self._timer_class = timer_class
        self._depth = depth
        self._on_disable_callback = on_disable

        self._counter = None
        self._frame_depth = None

        # The excluded function is mainly due to the side effect of
        # enabling or disabling the profiler.
        current_filename = re.sub('(\.pyc)$', '.py', __file__)
        self._excluded_func_names = (
            '<sys.setprofile>',
            # the following line number need to be updated if the
            # actual line number of the method `enable()` is changed.
            self._format_func_name(current_filename, 140, 'enable'),
            # the following line number need to be updated if the
            # actual line number of the method `disable()` is changed.
            self._format_func_name(current_filename, 150, 'disable'),
        )

    @staticmethod
    def _format_func_name(filename, firstlineno, name):
        return '{2}  [{0}:{1}]'.format(filename, firstlineno, name)

    @staticmethod
    def _is_c(event):
        """Judge if the given event happened on a C function."""
        return event in ('c_call', 'c_return')

    def _get_func_name(self, frame):
        fcode = frame.f_code
        fn = (fcode.co_filename, fcode.co_firstlineno, fcode.co_name)
        return self._format_func_name(*fn)

    def _exceed_depth(self, frame, is_c):
        """Judge if the given frame exceeds the specified depth."""
        if self._frame_depth.get_first_frame() is None:
            self._frame_depth.set_first_frame(frame)
            return False

        if self._depth is None:
            return False

        depth = self._depth - 1 if is_c else self._depth
        return self._frame_depth.get_frame_depth(frame) > depth

    def enable(self):
        # It's necessary to delay calling `timer_class.get_context()` here
        # if this profiler is used as a decorator.
        context = self._timer_class.get_context()
        self._counter = _NameCounter(context)
        self._frame_depth = _FrameDepth(context)

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
        is_c = self._is_c(event)

        if is_c:  # C function
            func_name = '<%s.%s>' % (arg.__module__, arg.__name__)
            parent_frame = frame
        else:  # Python function
            func_name = self._get_func_name(frame)
            parent_frame = frame.f_back

        # Ignore the excluded functions.
        if func_name in self._excluded_func_names:
            return

        # Ignore the function whose frame exceeds the specified depth.
        if self._exceed_depth(frame, is_c):
            return

        if event in ('call', 'c_call'):
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
