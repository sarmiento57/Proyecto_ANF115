from django import template
register = template.Library()

@register.filter
def find_by_clave(items, clave):
    if not items: return None
    for it in items:
        if it.get('clave') == clave:
            return it
    return None
