from django.utils.html import format_html, mark_safe
from django.utils.text import slugify
from .models import Employee, Slot, Schedule, Version, FillsWith


class Icons:
    class Calculate:
        __str__ = lambda self: "iconify-icon(icon='fluent-emoji-high-contrast:abacus')"
        __html__ = lambda self: format_html(
            '<span class="iconify" data-icon="fluent-emoji-high-contrast:abacus"></span>')

    class Improve:
        __str__ = lambda self: "iconify-icon(icon='fluent-emoji-high-contrast:chart-increasing')"
        __html__ = lambda self: format_html(
            '<span class="iconify" data-icon="fluent-emoji-high-contrast:chart-increasing"></span>')

    class Hospital:
        __str__ = lambda self: "iconify-icon(icon='fluent-emoji-high-contrast:hospital')"
        __html__ = lambda self: format_html(
            '<span class="iconify" data-icon="fluent-emoji-high-contrast:hospital"></span>')

    class TimeAlert:
        __str__ = lambda self: "iconify-icon(icon='arcticons:alarmio')"
        __html__ = lambda self: format_html('<span class="iconify" data-icon="arcticons:alarmio"></span>')

    class Equity:
        __str__ = lambda self: "iconify-icon(icon='emojione-monotone:balance-scale')"
        __html__ = lambda self: format_html('<span class="iconify" data-icon="emojione-monotone:balance-scale"></span>')
