"""Module for facilitating the testing of Blender scripts or addons
All credit goes to https://github.com/MaximeWeyl/blender_testing
"""

import contextlib
import importlib.util
import inspect
import logging
import os
import pickle
import shutil
import subprocess
import tempfile
from unittest import TestCase

INSIDE_BLENDER = bool(importlib.util.find_spec('bpy') is not None)

BLENDER_FAILURE_CODE = 1
BEGIN_LINE = "==========BlenderTestingBegin=========="
END_LINE = "==========BlenderTestingEnd=========="
ERROR_BEGIN_LINE = "==========BlenderTestingErrorBegin=========="
ERROR_END_LINE = "==========BlenderTestingErrorEnd=========="


def composed(*decs):
    """Compose several operators together

    Code written by Jochen Ritzel here :
    https://stackoverflow.com/questions/5409450/...
    can-i-combine-two-decorators-into-a-single-one-in-python

    """

    def deco(func):
        """Custom-function returned by the composed decorator
        """

        for dec in reversed(decs):
            func = dec(func)
        return func

    return deco


class BlenderNotFound(Exception):
    """Exception Raised when the path to blender is not found
    """


@contextlib.contextmanager
def _tempdir():
    """Context manager for providing a temp directory

    The temp dir is deleted at the end of the context manager ('with' keyword)
    """
    try:
        directory = tempfile.mkdtemp()
        yield directory
    finally:
        shutil.rmtree(directory)


def run_inside_blender(blender_path=None, import_paths=None):
    """Decorator Factory for running functions into Blender

    If run outside of Blender, it opens Blender and run the function into
    Blender.

    :param blender_path: If None, it searches for the environment variable
    "BLENDER_PATH". If not defined, it assumes blender is already in
    system's path by just calling "blender'
    :param import_paths: List of paths to add to system's path for blender to
    be able to find python libs of your project (or any other path you
    may want to use)
    """

    import_paths = [] if import_paths is None else list(import_paths)

    if INSIDE_BLENDER:
        def wrapper(func):
            """Custom-made decorator for running functions into Blender
            """
            return func

    else:
        import decorator

        if blender_path is None:
            blender_path = get_blender_path()

        @decorator.decorator
        def wrapper(func, *args, **kwargs):
            """Custom-made decorator for running functions into Blender
            """

            logging.info('We are not inside Blender')

            f_name, m_name = _get_func_name_and_module(func)

            modules, args_strings = FunctionCallExpression.aggregate_args(
                args, kwargs
            )

            modules.update({m_name, 'pickle'})

            logging.info('Function to run : {}'.format(f_name))
            logging.info('Module of the function : {}'.format(m_name))

            call_string = r'{}.{}({})'.format(
                m_name, f_name,
                ", ".join(args_strings)
            )

            TRY_PRINT = r'    print("{}")'

            with _tempdir() as temp_dir:
                shutil.copy2(__file__, temp_dir)
                import_paths.append(temp_dir)

                script = "\n".join([
                    r'import traceback,sys',
                    r'print("{}")'.format(BEGIN_LINE),
                    r'try:',
                    r'    import sys',
                    r'    sys.path.extend({})'.format(import_paths),
                    r'    import {}'.format(', '.join(modules)),
                    r'    print("Import OK")',
                    r'    {}'.format(call_string),
                    TRY_PRINT.format(END_LINE),
                    r'except Exception as e:',
                    TRY_PRINT.format(END_LINE),
                    TRY_PRINT.format(ERROR_BEGIN_LINE),
                    r'    print(e)',
                    r'    traceback.print_exc(file=sys.stdout)',
                    TRY_PRINT.format(ERROR_END_LINE),
                    r'    exit({})'.format(BLENDER_FAILURE_CODE),
                ])

                file_path = os.path.join(temp_dir, "script_blender.py")
                with open(file_path, "w") as file:
                    file.write(script)

                call_args = [
                    blender_path, "-b",
                    "--python-exit-code", str(BLENDER_FAILURE_CODE),
                    "--python", file_path
                ]

                logging.info('In {} : {}'.format(
                    temp_dir, os.listdir(temp_dir)))
                logging.info('---Script :---\n{}'.format(script))
                logging.info('Calling : {}'.format(call_args))

                try:
                    process_return = subprocess.run(
                        call_args, stdout=subprocess.PIPE,
                        stderr=None
                    )
                except FileNotFoundError:
                    raise BlenderNotFound(
                        'Blender not found at: "{}"'.format(blender_path)
                    )

            stdout = process_return.stdout.decode()
            logging.info(process_return.returncode)
            logging.info(stdout)

            if process_return.returncode == BLENDER_FAILURE_CODE:
                import pytest
                blender_error = 'Error in Blender !!!\n' + str(stdout)
                pytest.fail(blender_error, pytrace=False)

    return wrapper


def get_blender_path():
    if 'BLENDER_PATH' not in os.environ:
        return 'blender'

    blender_path = os.environ.get('BLENDER_PATH')

    # Remove quotes
    for char in ("'", '"'):
        if blender_path.startswith(char) and blender_path.endswith(char):
            blender_path = blender_path[1:-1]

    return blender_path


def _get_func_name_and_module(func):
    f_name = func.__name__
    module = inspect.getmodule(func)
    m_name = module.__name__

    if m_name == '__main__':
        m_name = os.path.splitext(
            os.path.basename((inspect.getfile(func))))[0]

    logging.info(m_name)

    return f_name, m_name


class FunctionCallExpression:
    """Class that represents a python expression that can be called later
    inside Blender

    """

    def __init__(self):
        self.modules = set()
        self.call_string = None

    def __repr__(self):
        return (
            'Fixture(modules={},call_string={})'.format(
                self.modules, self.call_string)
        )

    @staticmethod
    def aggregate_args(args, kwargs):
        """Aggregate various args and kwargs for using through subprocess

        Args:
            args: List of args that can be either:
                FunctionCallExpression instances
                Any pickle-able instance
            kwargs: Dict of keywords. Values must be pickle-able.

        Returns:
            A modules,args_string tuple:
                modules: Set of modules that should be imported for using these expressions.
                args_string: A list of strings that use either calls of
                FunctionCallExpression or serialized strings of pickle-able
                objects.
        """

        args_strings = []
        modules = set()

        for arg in args:
            if isinstance(arg, FunctionCallExpression):
                modules.update(arg.modules)
                args_strings.append(arg.call_string)
            else:
                serialized_string = pickle.dumps(
                    arg)
                args_strings.append(
                    'pickle.loads({})'.format(
                        serialized_string)
                )
        args_strings.append("**pickle.loads({})".format(
            pickle.dumps(kwargs)
        ))

        return modules, args_strings

    def build(self, func, args):
        """Builds the object.

        :param func: The function that should be used in this expression
        :param args: List of FunctionCallExpression that should be used as function arguments
        """

        f_name, m_name = _get_func_name_and_module(func)

        # We update the list of modules that blender should import
        # to be able to use this fixture
        modules = set()
        modules.add(m_name)
        for arg in args:
            modules.update(arg.modules)

        # We build the string that blender should call to run this
        # fixture
        call_string = "{}.{}({})".format(
            m_name,
            f_name,
            ", ".join(a.call_string for a in args)
        )

        self.call_string = call_string
        self.modules = modules


class BadFixtureArgument(Exception):
    """Exception raised when a fixture gets a wrong argument."""


def blender_fixture():
    """Decorator Factory for using pytest fixtures inside Blender.

    It gives a decorator that behave as the following:
    When run inside of Blender, it is a simple function.
    When run outside of Blender, it is a pytest fixture, which calls all other fixtures
    (they MUST be blender_fixture as well).
    The underlying function is not called outside of blender.
    The scope is always equivalent to pytest "function",
    because the fixture is called each time
    (we run each test in a new Blender instance that has no idea about the other tests nor pytest).
    """

    if INSIDE_BLENDER:
        def inside_blender_wrapper(func):
            """Decorator for when we are inside of Blender

            It returns a decorated function which sort of mimics the pytest
            fixtures
            """

            return_values = dict()

            def decorated_function(*args):
                """Decorated function returned by the blender_fixture decorator
                when inside Blender

                It uses the function closure to remember if the function should
                be called or if it has already been (and this can return the return value directly)
                """

                key = args
                if key not in return_values:
                    return_values[key] = func(*args)

                return return_values[key]

            return decorated_function

        return inside_blender_wrapper

    import pytest
    import decorator

    @decorator.decorator
    def outside_blender_wrapper(func, *args):
        """Decorator for when we are outside of Blender.

        It wraps the function for calling it in Blender through command line.
        """

        for arg in args:
            if not isinstance(arg, FunctionCallExpression):
                raise BadFixtureArgument('Fixture got non fixture argument !')

        exp = FunctionCallExpression()
        exp.build(func, args)
        return exp

    return composed(pytest.fixture, outside_blender_wrapper)


def _build_assert_functions():
    test_case = TestCase()
    for assert_func_name in dir(test_case):
        if (not assert_func_name.startswith('assert') or
                assert_func_name.endswith('_')):
            continue

        globals()[assert_func_name] = (
            test_case.__getattribute__(assert_func_name)
        )


_build_assert_functions()
