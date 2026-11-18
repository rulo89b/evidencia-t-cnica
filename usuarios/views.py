
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect("usuarios:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("usuarios:login")

    else:
        form = RegisterForm()

    return render(
        request,
        "usuarios/register.html",
        {"form": form},
    )


@login_required
def home(request):
    return render(request, "usuarios/home.html")
