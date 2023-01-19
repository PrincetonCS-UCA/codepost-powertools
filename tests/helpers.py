"""
Helpers for testing.
"""

# =============================================================================

import functools
import inspect
from pathlib import Path
from typing import Mapping

import pytest

# =============================================================================


class MockFunction:
    """An abstract class for mock functions.

    This will keep track of how many times the function was called.

    Child classes must implement ``mock()``.
    """

    def __init__(self, enable_set=False):
        """Initialize a mock function.

        If ``enable_set`` is True, the ``mock_function.set(**kwargs)``
        method will set args accepted by the mock function object.
        """
        self._times_called = 0
        self._enable_set = enable_set

    def __call__(self, *args, **kwargs):
        self._times_called += 1
        # pylint: disable=no-member
        # Child classes will implement this method
        return self.mock(*args, **kwargs)

    @property
    def times_called(self):
        return self._times_called

    def set(self, **kwargs):
        """Sets arguments that the mock accepts."""
        if self._enable_set is False:
            return
        if not isinstance(self._enable_set, tuple):
            # find the attributes that can be set and save it. assume
            # that it doesn't change (no new instance variables are
            # defined after this method is called for the first time)
            reserved = {"_times_called", "_enable_set"}
            attrs = []
            for attr in dir(self):
                if attr in reserved:
                    continue
                if len(attr) < 2:
                    continue
                if not (attr[0] == "_" and attr[1] != "_"):
                    continue
                attrs.append((attr, attr[1:]))
            self._enable_set = tuple(attrs)
        for attr_name, key in self._enable_set:
            if key in kwargs:
                setattr(self, attr_name, kwargs[key])

    def get(self, key):
        return getattr(self, f"_{key}")


# =============================================================================


def multi_scope_fixture(*, name, scopes, default_scope=None):
    """Creates multiple fixtures with different scopes.

    Defines the additional fixtures in the caller's global scope so that
    ``pytest`` recognizes them.

    Args:
        name (str): The base name of the fixture.
        scopes (Sequence[str]): The scopes to give to the fixture.
            Each scoped fixture will have the name "{scope}_{name}".
        default_scope (Optional[str]): The default scope.
            The fixture with this scope will simply have the given name.
    """
    # Inspired by:
    # https://github.com/pytest-dev/pytest/issues/2424#issuecomment-1041018452

    def wrapped(func):
        caller_globals = inspect.stack()[1][0].f_globals

        default_scope_func = None
        seen_scopes = set()
        for scope in scopes:
            if scope in seen_scopes:
                continue
            seen_scopes.add(scope)
            if default_scope is not None and scope == default_scope:
                default_scope_func = pytest.fixture(
                    func, name=name, scope=default_scope
                )
            else:
                fixture_name = f"{scope}_{name}"
                fixture = pytest.fixture(func, name=fixture_name, scope=scope)
                # add this fixture to the caller's global scope
                caller_globals[f"fixture_{fixture_name}"] = fixture
        return default_scope_func or func

    return wrapped


# =============================================================================


def get_src_path(request, func_name):
    # Inspired by: https://stackoverflow.com/a/61856751

    # check for "src_path" mark
    for mark in request.node.iter_markers():
        if mark.name == "src_path":
            src_file_path = mark.args[0]
            break
    else:
        # fallback to finding the path from the test path
        parts = []
        for part in reversed(Path(request.fspath).parts):
            if part == "tests":
                break
            parts.append(part)
        parts.append("codepost_powertools")
        # first part is gonna be `test_*.py`, so extract that part for
        # the actual module name
        parts[0] = parts[0][5:-3]
        src_file_path = ".".join(reversed(parts))
    return f"{src_file_path}.{func_name}"


def patch_mock_func(
    monkeypatch, request, func_name, definition_module, mock_func
):
    try:
        monkeypatch.setattr(get_src_path(request, func_name), mock_func)
    except AttributeError:
        # the function being mocked is not imported into the module
        # being tested
        pass
    # always mock the definition just to be safe (other functions may
    # call the mock target!)
    monkeypatch.setattr(definition_module, func_name, mock_func)


def patch_with_default_module(definition_module):
    """A convenience wrapper to define a default definition module for
    all calls to ``patch_mock_func()``.

    Example:
        from tests.helpers import patch_with_default_module

        patch_mock_func = patch_with_default_module(module)
    """

    @functools.wraps(patch_mock_func)
    def wrapped(monkeypatch, request, func_name, mock_func):
        patch_mock_func(
            monkeypatch, request, func_name, definition_module, mock_func
        )

    return wrapped


# =============================================================================


def get_request_param(request, **default):
    """Gets the provided parameters of the given request.
    Raises a RuntimeError if no args were provided.
    """
    if not hasattr(request, "param"):
        if "default" in default:
            return default["default"]
        raise RuntimeError(
            f'No params provided to "{request.fixturename}" fixture'
        )
    return request.param


# =============================================================================


def parametrize(*arguments, **kwargs):
    """A helper decorator that requires parametrized arguments to be
    specified in dicts so that the argument name-value assignments are
    clearer.

    This decorator can be called like:

    .. code-block:: python

       @parametrize(
           {'arg1': 'value0', 'arg2': 'value1'},
           {'arg1': 'value2', 'arg2': 'value3'},
       )

    The decorator accepts one mapping from argument names to values for
    each parametrized test run. All mappings must have the same set of
    argument names.

    If each mapping has an ``id`` key, those values will be used as the
    ``ids`` argument.

    The decorator also accepts additional keyword arguments that get
    passed to :deco:`pytest.mark.parametrize`.
    """
    ID_KEY = "id"

    arg_names = []
    arg_names_set = None
    arg_values = []
    save_ids = False
    ids = []
    for i, test_values in enumerate(arguments):
        if not isinstance(test_values, Mapping):
            raise TypeError(f"argument {i} is not a mapping")
        keys = set(test_values.keys())
        for arg in keys:
            if not isinstance(arg, str):
                raise TypeError(f"argument {i} has a non-str key")
        if arg_names_set is None:
            # getting the arg names from the first mapping
            arg_names = []
            arg_names_set = set()
            save_ids = False
            for arg in keys:
                if arg == ID_KEY:
                    save_ids = True
                else:
                    # don't save the id key in the args list
                    arg_names.append(arg)
                    arg_names_set.add(arg)
        elif (set(keys) - {ID_KEY}) != arg_names_set:
            raise ValueError(
                f"argument set {i} does not have the same argument names"
            )
        arg_values.append([test_values[arg] for arg in arg_names])
        if save_ids:
            ids.append(test_values[ID_KEY])
    if save_ids:
        if "ids" in kwargs:
            raise ValueError(
                f'arguments have "{ID_KEY}" key but `ids` keyword argument '
                "was also given"
            )
        kwargs["ids"] = ids

    if kwargs.pop("indirect_all", False):
        if "indirect" in kwargs:
            if set(kwargs["indirect"]) == arg_names_set:
                # indirect is already good; do nothing
                pass
            else:
                raise ValueError(
                    "parametrizing all indirect arguments, but `indirect` "
                    "keyword argument was also given"
                )
        else:
            kwargs["indirect"] = arg_names

    return pytest.mark.parametrize(arg_names, arg_values, **kwargs)


def parametrize_indirect(*arguments, **kwargs):
    """Parametrizes indirect arguments.

    Calls ``parametrize()`` with the keyword argument ``indirect`` equal
    to a sequence of all the given argument names.
    """
    return parametrize(*arguments, **kwargs, indirect_all=True)
