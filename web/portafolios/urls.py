from django.urls import path

from . import views

urlpatterns = [
    path("", views.portafolio, name="portafolio"),
    path("oportunidades/", views.oportunidades, name="oportunidades"),
    path("calidad/", views.calidad, name="calidad"),
]
