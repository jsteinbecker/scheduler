from django.template import Library
from django.template.defaultfilters import stringfilter
from django.template.loader import render_to_string
from pypugjs.ext.django import templatetags
from pypugjs.ext.django.compiler import Compiler
from cal.components import Icons
from django.utils.html import format_html, mark_safe

register = Library()




@templatetags.register.simple_tag(name='icon')
def icon(icon):
    if icon == 'calculate':
        return format_html(
            '<iconify-icon class="iconify" data-icon="fluent-emoji-high-contrast:abacus"></iconify-icon>')

    if icon == "improve":
        return format_html(
            '<iconify-icon class="iconify" data-icon="fluent-emoji-high-contrast:chart-increasing"></iconify-icon>')

    if icon == "hospital":
        return format_html(
            '<iconify-icon class="iconify" data-icon="fluent-emoji-high-contrast:hospital"></iconify-icon>')

    if icon == "time-alert":
        return format_html(
            '<iconify-icon class="iconify" data-icon="arcticons:alarmio"></iconify-icon>')

    if icon == "equity":
        return format_html(
            '<iconify-icon class="iconify" data-icon="emojione-monotone:balance-scale"></iconify-icon>')

    if icon == "template":
        return mark_safe('<iconify-icon class="text-white" data-icon="basil:edit-alt-outline"></iconify-icon>')



@templatetags.register.simple_tag(name='spinner')
def spinner(n:int=0):
    svg_map = {
        0: 'svg-spinners:clock',
        1: 'svg-spinners:ring-resize',
        2: 'svg-spinners:blocks-shuffle-3'
            }

    return format_html(f"<iconify-icon class='iconify' data-icon='{svg_map[n]}'></iconify-icon>")