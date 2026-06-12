from django.shortcuts import get_object_or_404, redirect, render

from .forms import LeitorForm, ObraForm
from .models import Leitor, Obra


def home(request):
    return render(request, "biblioteca/home.html")


# CRUD DE OBRAS

def listar_obras(request):
    obras = Obra.objects.all().order_by("titulo")

    return render(
        request,
        "biblioteca/obras/lista.html",
        {"obras": obras},
    )


def cadastrar_obra(request):
    if request.method == "POST":
        formulario = ObraForm(request.POST)

        if formulario.is_valid():
            formulario.save()
            return redirect("listar_obras")
    else:
        formulario = ObraForm()

    return render(
        request,
        "biblioteca/obras/formulario.html",
        {
            "formulario": formulario,
            "titulo": "Cadastrar obra",
        },
    )


def editar_obra(request, obra_id):
    obra = get_object_or_404(Obra, id=obra_id)

    if request.method == "POST":
        formulario = ObraForm(request.POST, instance=obra)

        if formulario.is_valid():
            formulario.save()
            return redirect("listar_obras")
    else:
        formulario = ObraForm(instance=obra)

    return render(
        request,
        "biblioteca/obras/formulario.html",
        {
            "formulario": formulario,
            "titulo": "Editar obra",
        },
    )


def excluir_obra(request, obra_id):
    obra = get_object_or_404(Obra, id=obra_id)

    if request.method == "POST":
        obra.delete()
        return redirect("listar_obras")

    return render(
        request,
        "biblioteca/obras/excluir.html",
        {"obra": obra},
    )


# CRUD DE LEITORES

def listar_leitores(request):
    leitores = Leitor.objects.all().order_by("nome_completo")

    return render(
        request,
        "biblioteca/leitores/lista.html",
        {"leitores": leitores},
    )


def cadastrar_leitor(request):
    if request.method == "POST":
        formulario = LeitorForm(request.POST)

        if formulario.is_valid():
            formulario.save()
            return redirect("listar_leitores")
    else:
        formulario = LeitorForm()

    return render(
        request,
        "biblioteca/leitores/formulario.html",
        {
            "formulario": formulario,
            "titulo": "Cadastrar leitor",
        },
    )


def editar_leitor(request, leitor_id):
    leitor = get_object_or_404(Leitor, id=leitor_id)

    if request.method == "POST":
        formulario = LeitorForm(request.POST, instance=leitor)

        if formulario.is_valid():
            formulario.save()
            return redirect("listar_leitores")
    else:
        formulario = LeitorForm(instance=leitor)

    return render(
        request,
        "biblioteca/leitores/formulario.html",
        {
            "formulario": formulario,
            "titulo": "Editar leitor",
        },
    )


def excluir_leitor(request, leitor_id):
    leitor = get_object_or_404(Leitor, id=leitor_id)

    if request.method == "POST":
        leitor.delete()
        return redirect("listar_leitores")

    return render(
        request,
        "biblioteca/leitores/excluir.html",
        {"leitor": leitor},
    )