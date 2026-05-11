import ast
from typing import Callable


def python_evalish_coerce[T](
    value: str,
    func: Callable[..., T],
    desired_function_name: str
) -> T:
    """
    A convenient function for parsing strings of the form
    `function_name(arg1, arg2, named=arg3, ...)` using Python's `ast`,
    and evaluating them against some anonymous function. We choose to immediately evaluate
    against `func`, as Python's internal parameter validation logic encapsulates precisely
    what we need for this function.

    Since these errors occur in the context of a union type, we don't worry too much
    about trying to collect all function names for erroring purposes.

    @param value: The value to parse against.
    @param func: The function to pass arguments to.
    @param desired_function_name: The function name to look for.

    @returns The result of calling `func` with the arguments in `value`
    """
    # To do this, we get the AST of our string as an expression
    # (filename='<string>' is to make the error message more closely resemble that of eval.)
    value_ast = ast.parse(value, mode='eval', filename='<string>')

    # Then we do some light parsing - we're only looking to do some literal evaluation
    # (allowing light python notation) and some basic function parsing. Full python programs
    # should just generate a config.yaml.

    # This should always be an Expression whose body is Call (a function).
    if not isinstance(value_ast.body, ast.Call):
        raise ValueError(f'This argument "{value}" was interpreted as a non-function-calling string: it should be a function call (e.g. range(100, 201, 50)), or an int or a float.')

    # We get the function name back as a string
    function_name = ast.unparse(value_ast.body.func)

    if desired_function_name != function_name:
        raise ValueError(f"Tried looking for a function of the name {desired_function_name}, but got {function_name} instead.")

    # and we use the (non-availability) safe `ast.literal_eval` to support literals passed into functions.
    arguments = [ast.literal_eval(arg) for arg in value_ast.body.args]
    # TODO: unclear when keyword.arg can be None? We filter for none-None values to satisfy the type checker.
    kv_arguments = {keyword.arg: ast.literal_eval(keyword.value) for keyword in value_ast.body.keywords if keyword.arg is not None}

    return func(*arguments, **kv_arguments)
