from django import template

register = template.Library()

# formato para numeros con comas y dos decimales
@register.filter
def money(value):
    try:
        return "${:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return "$0.00"
