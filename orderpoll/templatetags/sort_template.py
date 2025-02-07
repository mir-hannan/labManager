from django import template

register = template.Library()

@register.filter(name='sort_by')
def sort_by(queryset, order):
    return queryset.order_by(order)

