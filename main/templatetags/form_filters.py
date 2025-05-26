from django import template

register = template.Library()

@register.filter(name='addclass')
def addclass(value, arg):
    """Add a CSS class to a form field"""
    css_classes = value.field.widget.attrs.get('class', '')
    # Avoid duplicate classes
    existing_classes = css_classes.split()
    if arg not in existing_classes:
        css_classes = f"{css_classes} {arg}".strip()
    return value.as_widget(attrs={'class': css_classes})