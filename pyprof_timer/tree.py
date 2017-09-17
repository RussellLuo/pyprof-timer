# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from operator import itemgetter

import six
from tree_format import format_tree


@six.python_2_unicode_compatible
class Tree(object):
    """The class that represents the given timer and its children
    timers as a tree.
    """

    def __init__(self, timer, span_unit='s', span_fmt='%.3f'):
        self._timer = timer
        self._span_unit = span_unit
        self._span_fmt = span_fmt

    @property
    def nodes(self):
        span = self._span_fmt % self._timer.span(self._span_unit)
        node = '%s%s  %s' % (span, self._span_unit, self._timer.display_name)
        children = [Tree(child, self._span_unit, self._span_fmt).nodes
                    for child in self._timer.children]
        return node, children

    def __str__(self):
        return format_tree(
            self.nodes, format_node=itemgetter(0), get_children=itemgetter(1)
        )
