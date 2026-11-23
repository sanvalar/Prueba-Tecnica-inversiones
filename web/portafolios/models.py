import re

from django.core.exceptions import ValidationError
from django.db import models

# Palabras que no deben aparecer en una consulta de solo lectura
PROHIBIDAS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy)\b",
    re.IGNORECASE,
)


class ConsultaSQL(models.Model):
    """Una consulta SQL guardada en la base y administrable desde el panel de admin."""

    nombre = models.SlugField(
        max_length=60, unique=True,
        help_text="Identificador que usa el código, por ejemplo: local_detalle",
    )
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    sql = models.TextField(
        help_text="Solo SELECT. Parámetros con nombre, por ejemplo: %(cliente)s",
    )
    activa = models.BooleanField(default=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "consulta SQL"
        verbose_name_plural = "consultas SQL"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.titulo}"

    def clean(self):
        texto = self.sql.strip().rstrip(";").strip()
        if not re.match(r"(select|with)\b", texto, re.IGNORECASE):
            raise ValidationError({"sql": "La consulta debe empezar con SELECT o WITH."})
        if ";" in texto:
            raise ValidationError({"sql": "Escribe una sola sentencia (sin ';' en medio)."})
        if PROHIBIDAS.search(texto):
            raise ValidationError({"sql": "Solo se permiten consultas de lectura."})