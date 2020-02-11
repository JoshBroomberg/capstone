"""
This submodule contains utility functions that are used during both DGP sampling and the sampling of data from DGPs. The functions in this module may be useful for users writing their own concrete DGPs.
"""
import numpy as np
import sympy as sp
import pandas as pd
from functools import partial
import importlib
from multiprocessing import Process

from ..constants import Constants

def select_objects_given_probability(objects_to_sample, selection_probability):
    """Samples objects from `objects_to_sample` based on `selection_probability`.

    Args:
        objects_to_sample (list or :class:`numpy.ndarray`): List of objects to sample. If dimensionality is greater than 1, selection is along the primary (row) axis.
        selection_probability (list or float): The probability with which to sample objects from `objects_to_sample`. The value or values supplied should be between 0 and 1. If a list of probabilities is supplied, it should be the same length as the primary axis of the list in `objects_to_sample` and will be the per-object/row selection probability. If float, then this is the selection probability for all objects. In this case, ``int(len(objects_to_sample)*selection_probability)`` objects will be sampled if this value is greater than 0. Otherwise the single probability will be the selection probability for each object.

    Returns:
        :class:`numpy.ndarray`: An array of the selected objects.

    Examples
        >>> select_objects_given_probability(["a", "b", "c"], [0.5, 0.1, 0.001])
        ["a"]

        >>> select_objects_given_probability(["a", "b", "c"], 0.1)
        ["a"]
    """

    objects_to_sample = np.array(objects_to_sample)
    n_objects = len(objects_to_sample)
    object_indeces = np.arange(n_objects)

    if hasattr(selection_probability, "__len__"):
        selection_status = np.random.uniform(size=n_objects) < selection_probability
        selected_indeces = object_indeces[selection_status]
    else:
        expected_num_to_select = int(n_objects*selection_probability)

        # If expected number is less than 1, fall back to per object sampling.
        if expected_num_to_select == 0:
            return select_objects_given_probability(
                objects_to_sample,
                np.full(n_objects, selection_probability))

        # else, proceed to select expected number.
        selected_indeces = np.random.choice(object_indeces,
            size=expected_num_to_select, replace=False)

    if len(objects_to_sample.shape) == 1:
        return objects_to_sample[selected_indeces]
    else:
        return objects_to_sample[selected_indeces, :]

from sympy.utilities.autowrap import ufuncify, CodeWrapper
import pathlib
import sys
C_PATH = "./_maccabee_compiled_code/"

class CompiledExpression():

    def __init__(self, expression, symbols):
        self.symbols = symbols
        self.expression = expression
        self.constant_expression = False

        self.compiled_module_name = None
        self.compiled_ordered_args = None
        self._compile()

        self.expression_func = None

    def __getstate__(self):
        return (
            self.expression,
            self.constant_expression,
            self.compiled_module_name,
            self.compiled_ordered_args
        )

    def __setstate__(self, state):
        (
            self.expression,
            self.constant_expression,
            self.compiled_module_name,
            self.compiled_ordered_args
        ) = state

        self.expression_func = None

    def _compile(self):
        free_symbols = getattr(self.expression, "free_symbols", None)
        if free_symbols is not None:
            try:
                # Module
                self.compiled_module_name = \
                    f"mod_{abs(hash(self.expression))}_{np.random.randint(1e8)}"
                mod_path = C_PATH+self.compiled_module_name

                pathlib.Path(C_PATH).mkdir(parents=True, exist_ok=True)
                CodeWrapper.module_name = self.compiled_module_name

                # print("Compiling")
                # Compile
                ufuncify(
                    self.symbols,
                    self.expression,
                    backend="cython",
                    tempdir=mod_path)
                # print("Done compiling")
            except Exception as e:
                raise Exception(f"Failure in compilation of compiled expression. {e}")
        else:
            # No free symbols, expression is constant.
            self.constant_expression = True

    def eval_expr(self, data):
        if self.constant_expression:
            return self.expression

        try:
            if self.expression_func is None:
                if self.compiled_module_name not in sys.modules:
                    mod_path = C_PATH + self.compiled_module_name

                    if mod_path not in sys.path:
                        sys.path.append(mod_path)

                    # print("Importing compiled module.")
                    mod = importlib.import_module(self.compiled_module_name)
                else:
                    # print("Loading existing compiled module.")
                    mod = sys.modules[self.compiled_module_name]

                # compiled_func_prefix = "wrapped_"
                compiled_func_prefix = "autofunc"
                func_name = next(filter(lambda x: x.startswith(compiled_func_prefix), dir(mod)))
                self.expression_func = getattr(mod, func_name)

            # print("Executing compiled code")
            data = map(lambda x: x.flatten(), np.hsplit(data.values, data.shape[1]))
            expr_result = self.expression_func(*data)
            # print("Done executing compiled code")
            res = pd.Series(expr_result)
            return res
        except Exception as e:
            print(f"failure in compiled expression eval. {e}")
            return evaluate_expression(self.expression, data)

def evaluate_expression(expression, data):
    """Evaluates the Sympy expression in `expression` using the :class:`pandas.DataFrame` in `data` to fill in the value of all the variables in the expression. The expression is evaluated once for each row of the DataFrame.

    Args:
        expression (Sympy Expression): A Sympy expression with variables that are a subset of the variables in columns data.
        data (:class:`~pandas.DataFrame`): A DataFrame containing observations of the variables in the expression. The names of the columns must match the names of the symbols in the expression.

    Returns:
        :class:`~numpy.ndarray`: An array of expression values corresponding to the rows of the `data`.
    """
    if isinstance(expression, CompiledExpression):
        return expression.eval_expr(data)
    else:
        free_symbols = getattr(expression, "free_symbols", None)
        if free_symbols is not None:
            expr_func = sp.lambdify(
                    list(data.columns),
                    expression,
                    modules=[
                        {
                            "amax": lambda x: np.maximum(*x),
                            "amin": lambda x: np.minimum(*x)
                        },
                        "numpy"
                    ],
                    dummify=False)

            return pd.Series(expr_func(*np.hsplit(data.values, data.shape[1])).flatten())
        else:
            # No free symbols, return expression itself.
            return expression

def initialize_expression_constants(
    constants_sampling_distro, expressions,
    constant_symbols=Constants.DGPSampling.SUBFUNCTION_CONSTANT_SYMBOLS):
    """Initialize the constants in the expressions in `expressions` by sampling from `constants_sampling_distro`.

    Args:
        constants_sampling_distro (function): A function which produces `n` samples from some distribution over real values when called using a size keyword argument as in ``constants_sampling_distro(size=n)``.
        expressions (list): A list of Sympy expressions in which the constant symbols from `constant_symbols` appears. These are initialized to the values sampled from `constants_sampling_distro`.
        constant_symbols (list): A list of Sympy symbols which are constants to be initialized. Defaults to ``{sympy.abc.a, sympy.abc.c}``.

    Returns:
        list: A list of the sympy expressions from `expressions` with the constant symbols from `constant_symbols` randomly intialized.

    Examples
        >>> from sympy.abc import a, x
        >>> import numpy as np
        >>> initialize_expression_constants(np.random.normal, [a*x], [a])
        0.1*x
        >>> initialize_expression_constants(np.random.normal, [a*x], [a])
        -0.3*x
    """

    initialized_expressions = []

    for expression in expressions:
        # Find the free symbols which are in the constant symbols arg.
        constants_to_initialize = \
            constant_symbols.intersection(expression.free_symbols)

        initialized_expressions.append(
            # Init expression
            expression.subs(
                # enumerable of (symbol, val) tuples
                zip(constants_to_initialize,
                    constants_sampling_distro(size=len(constants_to_initialize))
                    )
                )
            )

    return initialized_expressions
