from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """Add a CSS class to a form field widget"""
    return field.as_widget(attrs={
        "class": f"{field.field.widget.attrs.get('class', '')} {css_class}".strip()
    })

@register.filter(name='field_type')
def field_type(field):
    """Return the field type"""
    return field.field.widget.__class__.__name__