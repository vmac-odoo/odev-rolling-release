# Part of Odoo. See LICENSE file for full copyright and licensing details.

NOT_OPERATOR = "!"
OR_OPERATOR = "|"
AND_OPERATOR = "&"

TRUE_LEAF = (1, "=", 1)
FALSE_LEAF = (0, "=", 1)

TRUE_DOMAIN = [TRUE_LEAF]
FALSE_DOMAIN = [FALSE_LEAF]


def normalize_domain(domain):
    """Returns a normalized version of ``domain_expr``, where all implicit '&' operators
    have been made explicit. One property of normalized domain expressions is that they
    can be easily combined together as if they were single domain components.
    """
    assert isinstance(
        domain, (list, tuple)
    ), "Domains to normalize must have a 'domain' form: a list or tuple of domain components"
    if not domain:
        return [TRUE_LEAF]
    result = []  # type: ignore
    expected = 1  # expected number of expressions
    op_arity = {NOT_OPERATOR: 1, AND_OPERATOR: 2, OR_OPERATOR: 2}
    for token in domain:
        if expected == 0:  # more than expected, like in [A, B]
            result[0:0] = [AND_OPERATOR]  # put an extra '&' in front
            expected = 1
        if isinstance(token, (list, tuple)):  # domain term
            expected -= 1
            if len(token) == 3 and token[1] in ("any", "not any"):
                token = (token[0], token[1], normalize_domain(token[2]))
            else:
                token = tuple(token)
        else:
            expected += op_arity.get(token, 0) - 1
        result.append(token)
    if expected:
        raise ValueError(f"Domain {domain} is syntactically not correct.")
    return result


def combine(operator, unit, zero, domains):
    """Returns a new domain expression where all domain components from ``domains``
    have been added together using the binary operator ``operator``.

    It is guaranteed to return a normalized domain.

    :param operator:
    :param unit: the identity element of the domains "set" with regard to the operation
                 performed by ``operator``, i.e the domain component ``i`` which, when
                 combined with any domain ``x`` via ``operator``, yields ``x``.
                 E.g. [(1,'=',1)] is the typical unit for AND_OPERATOR: adding it
                 to any domain component gives the same domain.
    :param zero: the absorbing element of the domains "set" with regard to the operation
                 performed by ``operator``, i.e the domain component ``z`` which, when
                 combined with any domain ``x`` via ``operator``, yields ``z``.
                 E.g. [(1,'=',1)] is the typical zero for OR_OPERATOR: as soon as
                 you see it in a domain component the resulting domain is the zero.
    :param domains: a list of normalized domains.
    """
    result = []
    count = 0
    if domains == [unit]:
        return unit
    for domain in domains:
        if domain == unit:
            continue
        if domain == zero:
            return zero
        if domain:
            result += normalize_domain(domain)
            count += 1
    result = [operator] * (count - 1) + result
    return result or unit


def AND(domains):
    """AND([D1,D2,...]) returns a domain representing D1 and D2 and ..."""
    return combine(AND_OPERATOR, [TRUE_LEAF], [FALSE_LEAF], domains)
