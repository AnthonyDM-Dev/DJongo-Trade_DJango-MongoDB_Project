from django import template

register = template.Library()

@register.simple_tag()
def multiply(a, b):
    return a*b

@register.simple_tag()
def divide(a, b):
    return a/b

@register.simple_tag()
def subtract(a, b):
    return a-b

@register.simple_tag()
def addition(a, b):
    return a+b