# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import collections
import functools
import re
import sys

import six

from .timer import Timer


class OrderedDefaultDictInt(collections.OrderedDict):
    def __missing__(self, key):
        self[key] = value = 0
        return value


class _FrameNameCounter(object):
    """The counter class that counts a given function name in a given frame,
    and returns an unique name for each function, in case that it has the
    same name as other functions in the same frame.
    """

    _ctx_counts_name = '_NameCounter_counts'

    def __init__(self, context):
        self._counts = getattr(context, self._ctx_counts_name, None)
        if self._counts is None:
            self._counts = OrderedDefaultDictInt()
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

    @property
    def first_frame(self):
        """Return the first frame attached to the context."""
        default = (None, None)
        return next(iter(six.iterkeys(self._counts)), default)[0]


class Profiler(object):
    """The profiler class that automatically injects a timer for each
    function to measure its execution time.
    """

    CALL_EVENTS = ('call', 'c_call')
    RETURN_EVENTS = ('return', 'exception', 'c_return', 'c_exception')

    def __init__(self, timer_class=Timer, depth=None, on_disable=None):
        self._timer_class = timer_class
        self._depth = depth
        self._on_disable_callback = on_disable

        self._ctx_local_vars = dict(
            # Mapping: context -> call_stack_depth [PER CONTEXT]
            #                     (The depth of the call stack).
            call_stack_depths={},
            # Mapping: context -> frame_depth [PER CONTEXT]
            #                     (Mapping: frame -> depth [PER FRAME],
            #                                        relative to the first frame).
            frame_depths={},

            # Mapping: context -> counter [PER CONTEXT]
            #                     (The helper to make unique function name).
            counters={},
        )

        # The excluded function is mainly due to the side effect of
        # enabling or disabling the profiler.
        current_filename = re.sub('(\.pyc)$', '.py', __file__)
        self._excluded_func_names = (
            '<sys.setprofile>',
            # the following line number need to be updated if the
            # actual line number of the method `enable()` is changed.
            self._format_func_name(current_filename, 106, 'enable'),
            # the following line number need to be updated if the
            # actual line number of the method `disable()` is changed.
            self._format_func_name(current_filename, 119, 'disable'),
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
        ctx = self._timer_class.get_context()

        # Attach the context local variables.
        self._ctx_local_vars['call_stack_depths'][ctx] = -1
        self._ctx_local_vars['frame_depths'][ctx] = {}
        self._ctx_local_vars['counters'][ctx] = _FrameNameCounter(ctx)

        sys.setprofile(self._profile)
        return self

    def disable(self):
        sys.setprofile(None)

        # It's necessary to delay calling `timer_class.get_context()` here
        # if this profiler is used as a decorator.
        ctx = self._timer_class.get_context()

        # Detach the context local variables.
        self._ctx_local_vars['call_stack_depths'].pop(ctx)
        self._ctx_local_vars['frame_depths'].pop(ctx)
        self._ctx_local_vars['counters'].pop(ctx)

        # If a callback function is given, call it after this profiler is disabled.
        if self._on_disable_callback is not None:
            self._on_disable_callback(self)

        return self

    @property
    def root(self):
        """Return the root timer of the implicit entire timer tree."""
        return self._timer_class.root

    def _profile(self, frame, event, arg):
        """The core handler used as the system’s profile function."""
        ctx = self._timer_class.get_context()

        # Judge if the given event happened on a C function.
        # i.e. ('c_call', 'c_return', 'c_exception')
        is_c = event.startswith('c_')

        if is_c:  # C function
            func_name = '<%s.%s>' % (arg.__module__, arg.__name__)
            parent_frame = frame
        else:  # Python function
            func_name = self._get_func_name(frame)
            parent_frame = frame.f_back

        # Ignore the excluded functions.
        if func_name in self._excluded_func_names:
            return

        current_depth = 0
        frame_name = ('c_' if is_c else '') + unicode(frame)
        if event in Profiler.CALL_EVENTS:
            # Increment the depth of the call stack.
            self._ctx_local_vars['call_stack_depths'][ctx] += 1

            d = self._ctx_local_vars['call_stack_depths'][ctx]
            current_depth = self._ctx_local_vars['frame_depths'][ctx][frame_name] = d
        elif event in Profiler.RETURN_EVENTS:
            # Decrement the depth of the call stack.
            self._ctx_local_vars['call_stack_depths'][ctx] -= 1

            current_depth = self._ctx_local_vars['frame_depths'][ctx].pop(frame_name)

        # Ignore the frame if its depth exceeds the specified depth.
        if self._depth is not None and current_depth > self._depth:
            return

        ctx_local_counter = self._ctx_local_vars['counters'][ctx]
        if event in Profiler.CALL_EVENTS:
            ctx_local_counter.incr(frame, func_name)

            unique_func_name = ctx_local_counter.unique_name(frame, func_name)

            if frame is ctx_local_counter.first_frame:
                unique_parent_name = None
            else:
                parent_name = self._get_func_name(parent_frame)
                unique_parent_name = ctx_local_counter.unique_name(
                    parent_frame, parent_name)

            # Create and start a timer for the entering function
            self._timer_class(
                unique_func_name,
                parent_name=unique_parent_name,
                display_name=func_name
            ).start()
        elif event in Profiler.RETURN_EVENTS:
            unique_func_name = ctx_local_counter.unique_name(frame, func_name)
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
