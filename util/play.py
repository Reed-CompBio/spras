import ast
value_ast = ast.parse("np.range.test(1, 2, 3)", mode='eval')
# print(ast.dump(value_ast.body, indent=2))
assert isinstance(value_ast.body, ast.Call)
print([ast.literal_eval(arg) for arg in value_ast.body.args])