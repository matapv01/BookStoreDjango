from django import template

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ''

@register.filter(name='divide')
def divide(value, arg):
    try:
        return int(value) / int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return ''