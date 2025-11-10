# libs/strawberry_graphql/decorator.py
# registry + decorators (intentionally module-level, no classes here)

QUERY_ROOTS: list[type] = []
MUTATION_ROOTS: list[type] = []

def register_query_root(cls: type):
    QUERY_ROOTS.append(cls)
    return cls

def register_mutation_root(cls: type):
    MUTATION_ROOTS.append(cls)
    return cls
