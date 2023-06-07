from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.utils.html import format_html

from cal.models import Schedule, Workday
from org.models import Organization, Department, Shift
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from pypugjs.ext.django.templatetags import get_template, register
from django.template.loader import render_to_string, get_template


# Create your views here.
class CardComponent:
    def __init__(self, title, dx, link, qty, img_src, img_alt, inst, inst_full):
        self.title = title
        self.description = dx
        self.link = link
        self.qty = qty
        self.img_src = img_src
        self.img_alt = img_alt
        self.inst = inst

        self.inst_full = inst_full

    @register.inclusion_tag('mixins/UI-Card.pug')
    def render(self):
        return  {
            'title': self.title,
            'description': self.description,
            'link': self.link,
            'qty': self.qty,
            'img_src': self.img_src,
            'img_alt': self.img_alt,
            'inst': self.inst,
            'inst_full': self.inst_full
        }


def index_view(request):
    OrgCard = CardComponent(title="Organization",
                            dx="Organization",
                            inst_full="Organization",
                            inst="Org",
                            link="/org/",
                            qty=Organization.objects.count(),
                            img_src="/static/img/org.svg",
                            img_alt="Organization")

    ProfileCard = CardComponent(title="Profile",
                                inst_full="Profile",
                                inst="Profile",
                                dx="Profile",
                                link="/profile/",
                                qty=0,
                                img_src="/static/img/profile.svg",
                                img_alt="Profile")
    return render(request, 'index.pug',
                  {'OrgCard': OrgCard,
                   'ProfileCard': ProfileCard})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        if username and password:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('/')
            else:
                return render(request, 'login.pug', {'error': 'Invalid username or password'})
        else:
            return render(request, 'login.pug', {'error': 'Username and password are required'})



