#!/usr/bin/env python
# coding=utf-8

from __future__ import division, print_function, unicode_literals

import pprint
from collections import OrderedDict

import pytest
from sacred import Ingredient, Experiment
from sacred.commands import (BLUE, ENDC, GREY, GREEN, RED, ConfigEntry,
                             PathEntry, _format_config, _format_entry,
                             help_for_command, _iterate_marked, _non_unicode_repr,
                             _format_named_configs, _format_named_config)
from sacred.config import ConfigScope
from sacred.config.config_summary import ConfigSummary


def test_non_unicode_repr():
    p = pprint.PrettyPrinter()
    p.format = _non_unicode_repr
    # make sure there is no u' in the representation
    assert p.pformat(u'HelloWorld') == "'HelloWorld'"


@pytest.fixture
def cfg():
    return {
        'a': 0,
        'b': {},  # 1
        'c': {    # 2
            'cA': 3,
            'cB': 4,
            'cC': {  # 5
                'cC1': 6
            }
        },
        'd': {  # 7
            'dA': 8
        }
    }


def test_iterate_marked(cfg):
    assert list(_iterate_marked(cfg, ConfigSummary())) == \
        [('a', ConfigEntry('a', 0, False, False, None, None)),
         ('b', ConfigEntry('b', {}, False, False, None, None)),
         ('c', PathEntry('c', False, False, None, None)),
         ('c.cA', ConfigEntry('cA', 3, False, False, None, None)),
         ('c.cB', ConfigEntry('cB', 4, False, False, None, None)),
         ('c.cC', PathEntry('cC', False, False, None, None)),
         ('c.cC.cC1', ConfigEntry('cC1', 6, False, False, None, None)),
         ('d', PathEntry('d', False, False, None, None)),
         ('d.dA', ConfigEntry('dA', 8, False, False, None, None))
         ]


def test_iterate_marked_added(cfg):
    added = {'a', 'c.cB', 'c.cC.cC1'}
    assert list(_iterate_marked(cfg, ConfigSummary(added=added))) == \
        [('a', ConfigEntry('a', 0, True, False, None, None)),
         ('b', ConfigEntry('b', {}, False, False, None, None)),
         ('c', PathEntry('c', False, True, None, None)),
         ('c.cA', ConfigEntry('cA', 3, False, False, None, None)),
         ('c.cB', ConfigEntry('cB', 4, True, False, None, None)),
         ('c.cC', PathEntry('cC', False, True, None, None)),
         ('c.cC.cC1', ConfigEntry('cC1', 6, True, False, None, None)),
         ('d', PathEntry('d', False, False, None, None)),
         ('d.dA', ConfigEntry('dA', 8, False, False, None, None))
         ]


def test_iterate_marked_updated(cfg):
    modified = {'b', 'c', 'c.cC.cC1'}
    assert list(_iterate_marked(cfg, ConfigSummary(modified=modified))) == \
        [('a', ConfigEntry('a', 0, False, False, None, None)),
         ('b', ConfigEntry('b', {}, False, True, None, None)),
         ('c', PathEntry('c', False, True, None, None)),
         ('c.cA', ConfigEntry('cA', 3, False, False, None, None)),
         ('c.cB', ConfigEntry('cB', 4, False, False, None, None)),
         ('c.cC', PathEntry('cC', False, True, None, None)),
         ('c.cC.cC1', ConfigEntry('cC1', 6, False, True, None, None)),
         ('d', PathEntry('d', False, False, None, None)),
         ('d.dA', ConfigEntry('dA', 8, False, False, None, None))
         ]


def test_iterate_marked_typechanged(cfg):
    typechanged = {'a': (bool, int),
                   'd.dA': (float, int)}
    result = list(_iterate_marked(cfg, ConfigSummary(typechanged=typechanged)))
    assert result == \
        [('a', ConfigEntry('a', 0, False, False, (bool, int), None)),
         ('b', ConfigEntry('b', {}, False, False, None, None)),
         ('c', PathEntry('c', False, False, None, None)),
         ('c.cA', ConfigEntry('cA', 3, False, False, None, None)),
         ('c.cB', ConfigEntry('cB', 4, False, False, None, None)),
         ('c.cC', PathEntry('cC', False, False, None, None)),
         ('c.cC.cC1', ConfigEntry('cC1', 6, False, False, None, None)),
         ('d', PathEntry('d', False, True, None, None)),
         ('d.dA', ConfigEntry('dA', 8, False, False, (float, int), None))
         ]


@pytest.mark.parametrize("entry,expected", [
    (ConfigEntry('a', 0, False, False, None, None),       "a = 0"),
    (ConfigEntry('foo', 'bar', False, False, None, None), "foo = 'bar'"),
    (ConfigEntry('b', [0, 1], False, False, None, None),  "b = [0, 1]"),
    (ConfigEntry('c', True, False, False, None, None),    "c = True"),
    (ConfigEntry('d', 0.5, False, False, None, None),     "d = 0.5"),
    (ConfigEntry('e', {}, False, False, None, None),      "e = {}"),
    # Path entries
    (PathEntry('f', False, False, None, None), "f:"),
    # Docstring entry
    (ConfigEntry('__doc__', 'multiline\ndocstring', False, False, None, None),
     GREY + '"""multiline\ndocstring"""' + ENDC),
])
def test_format_entry(entry, expected):
    assert _format_entry(0, entry) == expected


@pytest.mark.parametrize("entry,color", [
    (ConfigEntry('a', 1, True, False, None, None),         GREEN),
    (ConfigEntry('b', 2, False, True, None, None),         BLUE),
    (ConfigEntry('c', 3, False, False, (bool, int), None), RED),
    (ConfigEntry('d', 4, True, True, None, None),          GREEN),
    (ConfigEntry('e', 5, True, False, (bool, int), None),  RED),
    (ConfigEntry('f', 6, False, True, (bool, int), None),  RED),
    (ConfigEntry('g', 7, True, True, (bool, int), None),   RED),
    # Path entries
    (PathEntry('a', True, False, None, None),         GREEN),
    (PathEntry('b', False, True, None, None),         BLUE),
    (PathEntry('c', False, False, (bool, int), None), RED),
    (PathEntry('d', True, True, None, None),          GREEN),
    (PathEntry('e', True, False, (bool, int), None),  RED),
    (PathEntry('f', False, True, (bool, int), None),  RED),
    (PathEntry('g', True, True, (bool, int), None),   RED),
])
def test_format_entry_colors(entry, color):
    s = _format_entry(0, entry)
    assert s.startswith(color)
    assert s.endswith(ENDC)


def test_format_config(cfg):
    cfg_text = _format_config(cfg, ConfigSummary())
    lines = cfg_text.split('\n')
    assert lines[0].startswith('Configuration')
    assert ' a = 0' in lines[1]
    assert ' b = {}' in lines[2]
    assert ' c:' in lines[3]
    assert ' cA = 3' in lines[4]
    assert ' cB = 4' in lines[5]
    assert ' cC:' in lines[6]
    assert ' cC1 = 6' in lines[7]
    assert ' d:' in lines[8]
    assert ' dA = 8' in lines[9]


def test_help_for_command():
    def my_command():
        """This is my docstring"""
        pass

    help_text = help_for_command(my_command)
    assert "my_command" in help_text
    assert "This is my docstring" in help_text


def _config_scope_with_single_line_doc():
    """doc"""
    pass


def _config_scope_with_multiline_doc():
    """Multiline
    docstring!
    """
    pass


@pytest.mark.parametrize('indent, path, named_config, expected', [
    (0, 'a', None, 'a'),
    (1, 'b', None, ' b'),
    (4, 'a.b.c', None, '    a.b.c'),
    (0, 'c', ConfigScope(_config_scope_with_single_line_doc), 'c' + GREY
     + '   # doc' + ENDC),
    (0, 'd', ConfigScope(_config_scope_with_multiline_doc),
     'd' + GREY + '\n  """Multiline\n    docstring!\n    """' + ENDC)
])
def test_format_named_config(indent, path, named_config, expected):
    assert _format_named_config(indent, path, named_config) == expected


def test_format_named_configs():
    ingred = Ingredient('ingred')
    ex = Experiment(name='experiment', ingredients=[ingred])

    @ingred.named_config
    def named_config1():
        pass

    @ex.named_config
    def named_config2():
        """named config with doc"""
        pass

    dict_config = dict(v=42)
    ingred.add_named_config('dict_config', dict_config)

    named_configs_text = _format_named_configs(OrderedDict(
        ex.gather_named_configs()), hide_path=ex.path)
    assert named_configs_text.startswith('Named Configurations (' +
                                            GREY + 'doc' + ENDC + '):')
    assert 'named_config2' in named_configs_text
    assert '# named config with doc' in named_configs_text
    assert 'ingred.named_config1' in named_configs_text
    assert 'ingred.dict_config' in named_configs_text
