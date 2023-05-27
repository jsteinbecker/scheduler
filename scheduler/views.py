from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from cal.models import Schedule, Workday
from org.models import Organization, Department, Shift
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader


# Create your views here.

def index_view(request):
    return render(request, 'index.pug')

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


