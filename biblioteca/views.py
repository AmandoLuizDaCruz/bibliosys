from django.shortcuts import get_object_or_404, redirect, render

from .forms import ObraForm
from .models import Obra


def home(request):
    return render(request, "biblioteca/home.html")


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
