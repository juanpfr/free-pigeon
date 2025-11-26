from django import template
import re

register = template.Library()


def _only_digits(value):
    if not value:
        return ''
    return re.sub(r'\D', '', str(value))


@register.filter
def cpf_format(value):
    """
    Formata CPF como xxx.xxx.xxx-xx
    """
    digits = _only_digits(value)
    if len(digits) != 11:
        return value or ''
    return f"{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"


@register.filter
def phone_br(value):
    """
    Formata telefone como (xx) xxxxx-xxxx ou (xx) xxxx-xxxx
    """
    digits = _only_digits(value)

    # Celular 11 dígitos: (11) 98765-4321
    if len(digits) == 11:
        return f"({digits[0:2]}) {digits[2:7]}-{digits[7:11]}"

    # Fixo 10 dígitos: (11) 1234-5678
    if len(digits) == 10:
        return f"({digits[0:2]}) {digits[2:6]}-{digits[6:10]}"

    return value or ''
