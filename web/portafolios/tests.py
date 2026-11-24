from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase, TransactionTestCase

from .models import ConsultaSQL
from .servicios import ConsultaNoDisponible, ejecutar
from .views import _posicion, etiqueta_cliente


class ConsultaSQLTests(TestCase):
    def test_acepta_select(self):
        ConsultaSQL(nombre="ok", titulo="ok", sql="SELECT 1").clean()

    def test_rechaza_escritura(self):
        for sql in ("DELETE FROM x", "SELECT 1; DROP TABLE x", "UPDATE x SET a = 1"):
            with self.assertRaises(ValidationError, msg=sql):
                ConsultaSQL(nombre="mala", titulo="mala", sql=sql).clean()


class EjecutarTests(TransactionTestCase):
    # TransactionTestCase: ejecutar() abre su propia transacción de solo lectura,
    # que en PostgreSQL debe ser la primera instrucción de la transacción.
    def test_consulta_inexistente(self):
        with self.assertRaises(ConsultaNoDisponible):
            ejecutar("no_existe")

    def test_ejecuta_consulta_con_parametros(self):
        ConsultaSQL.objects.create(
            nombre="suma", titulo="suma", sql="SELECT %(a)s::int + 1 AS r"
        )
        self.assertEqual(ejecutar("suma", {"a": 4}), [{"r": 5}])

    def test_transaccion_de_solo_lectura(self):
        if connection.vendor != "postgresql":
            self.skipTest("Solo aplica en PostgreSQL")
        ConsultaSQL.objects.create(
            nombre="escribe", titulo="escribe",
            sql="CREATE TEMP TABLE t AS SELECT 1",  # saltándose clean()
        )
        with self.assertRaises(Exception):
            ejecutar("escribe")


class AyudantesTests(TestCase):
    def test_etiqueta_de_id_completo(self):
        self.assertEqual(etiqueta_cliente("10039616197", False), "10039616197")

    def test_etiqueta_de_id_truncado(self):
        self.assertEqual(etiqueta_cliente("TRUNC-100901", True), "ID truncado 100901…")

    def test_etiqueta_de_id_truncado_separado_por_perfil(self):
        self.assertIn("perfil 1466", etiqueta_cliente("TRUNC-100114#1466", True))

    def test_posicion_en_la_escala(self):
        self.assertEqual(_posicion(1), 0)
        self.assertEqual(_posicion(5), 100)
        self.assertEqual(_posicion(3), 50)
        self.assertIsNone(_posicion(None))


class PaginasTests(TestCase):
    """Sin consultas cargadas, las páginas no se caen: explican qué falta."""

    def test_portafolio_sin_consultas(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "cargar_consultas")

    def test_oportunidades_sin_consultas(self):
        r = self.client.get("/oportunidades/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "cargar_consultas")

    def test_calidad_sin_consultas(self):
        r = self.client.get("/calidad/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "cargar_consultas")
