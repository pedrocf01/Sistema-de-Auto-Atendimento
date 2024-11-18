from django import template

register = template.Library()

@register.filter
def divide(value, divisor):
    try:
        return value // divisor
    except (ValueError, ZeroDivisionError):
        return None