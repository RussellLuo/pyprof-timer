# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from flask import g

from pyprof_timer.timer import Timer


class FlaskTimer(Timer):
    """The timer implementation in Flask."""

    def _get_context(self):
        """Returns the request context."""
        return g
