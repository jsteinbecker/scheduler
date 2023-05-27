from django.template import Library
from django.template.defaultfilters import stringfilter
from django.template.loader import render_to_string
from pypugjs.ext.django import templatetags
from pypugjs.ext.django.compiler import Compiler

register = Library()

@register.simple_tag(name='icon')
def Icon(icon):
    return render_to_string("icons/{}.svg".format(icon))

@templatetags.register.simple_tag(name='icon')
def icon(icon):
    return "<iconify-icon class='iconify' icon='{}'></iconify-icon>".format(icon)
