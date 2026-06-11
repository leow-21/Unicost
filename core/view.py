from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate

def home(request):
    return render(request, 'home.html')