# Prueba-Tecnica-inversiones

# Análisis de portafolios de clientes: prueba técnica Aprendiz Gerencia Analítica de Inversiones 2027-1

Solución a la prueba técnica de Cibest / Valores Bancolombia. A partir de los archivos CSV entregados, el proyecto:

1. carga los datos en **PostgreSQL** (una tabla por archivo),
2. los **limpia con SQL** y deja vistas listas para análisis,
3. muestra en una **aplicación Django** el portafolio local (COP) e internacional (USD) de un cliente, con gráficos,
4. calcula un **modelo analítico** que evalúa si el portafolio de cada cliente es coherente con su perfil de riesgo, sustentado en **información de mercado** de los activos, y
5. integra el resultado del modelo en la misma aplicación.

> Los datos entregados por Cibest **no están en este repositorio**. Hay que copiarlos a la carpeta `data/` (ver "Puesta en marcha").

---

## 1. Qué responde cada punto de la prueba

| Requisito de la prueba | Dónde está |
|---|---|
| Base de datos PostgreSQL con una tabla por CSV | `sql/01_crear_tablas.sql`, `scripts/cargar_datos.py` |
| Limpieza de datos con SQL | `sql/02_limpieza.sql`, `sql/03_portafolio_ultimo.sql`; hallazgos en `docs/hallazgos.md` |
| Aplicación Django con gráficos del portafolio COP y USD de un cliente | `web/` (vista `portafolio`, plantilla `portafolio.html`) |
| Información de mercado de los activos locales e internacionales | `docs/fichas_activos.md`, `scripts/descargar_mercado.py` |
| Modelo analítico | `modelo/modelo_clientes.py`, `scripts/correr_modelo.py`, `sql/04_riesgo_activos.sql`, `sql/05_features_modelo.sql` |
| Repositorio con README, sin subir las bases entregadas | este archivo; `data/` y `.env` están en `.gitignore` |

---

## 2. Cómo fluye la información

```
CSV entregados (data/)
        │  scripts/cargar_datos.py
        ▼
PostgreSQL: 1 tabla por CSV
        │  sql/02, 03  (limpieza + último portafolio por cliente)
        ▼
Vistas limpias: v_portafolio_local_ultimo, v_portafolio_usd_ultimo, v_cliente_resumen
        │  sql/04, 05  (riesgo por activo + variables por cliente)
        ▼
v_cliente_features
        │  scripts/correr_modelo.py  (modelo/modelo_clientes.py)
        ▼
Tabla resultado_modelo_cliente
        │
        ▼
Django: página del cliente (gráficos + tarjeta "Análisis del modelo")
```

---

## 3. Estructura del repositorio

```
proyecto-analítica-inversiones/
├── sql/        Esquema, limpieza, vistas y tablas de riesgo (se ejecutan en orden numérico)
├── scripts/    Carga de datos, ejecución del modelo, descarga de datos de mercado
├── modelo/     Lógica del modelo (variables, segmentación, alineación, recomendaciones)
├── web/        Aplicación Django
├── notebooks/  Exploración inicial de los datos
├── docs/       hallazgos.md (calidad de datos) y fichas_activos.md (investigación de mercado)
├── data/       CSV entregados y salidas locales (NO se versiona)
├── .env        Credenciales de la base de datos (NO se versiona)
└── requirements.txt
```

---

## 4. Puesta en marcha

Requisitos: Python 3.12 o superior, PostgreSQL (probado con la versión 19) y Git.

1. **Clonar e instalar dependencias**
   ```powershell
   git clone https://github.com/sanvalar/Prueba-Tecnica-inversiones.git
   cd Prueba-Tecnica-inversiones
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Crear el archivo `.env`** en la raíz, con los datos de tu PostgreSQL:
   ```
   DB_USER=postgres
   DB_PASSWORD=tu_contraseña
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=analitica_inversiones
   ```

3. **Copiar los CSV entregados a la carpeta `data/`**, con los nombres que espera `scripts/cargar_datos.py`.

4. **Cargar los datos y crear las vistas** (crea la base si no existe, recrea las tablas, carga los CSV y ejecuta los archivos de `sql/`):
   ```powershell
   python scripts/cargar_datos.py --vistas
   ```
   Deben aparecer ejecutados `02_limpieza.sql`, `03_portafolio_ultimo.sql`, `04_riesgo_activos.sql` y `05_features_modelo.sql`.

5. **Ejecutar el modelo.** Crea la tabla `resultado_modelo_cliente`. **Sin este paso la aplicación funciona, pero la tarjeta "Análisis del modelo" muestra un aviso en lugar de resultados.**
   ```powershell
   python scripts/correr_modelo.py
   ```

6. **(Opcional) Descargar datos de mercado** (retorno, volatilidad y caída máxima a 1 año, con yfinance; requiere internet). Genera `data/mercado_resumen.csv`.
   ```powershell
   python scripts/descargar_mercado.py
   ```

7. **Levantar la aplicación**
   ```powershell
   cd web
   python manage.py migrate
   python manage.py loaddata consultas_sql
   python manage.py runserver
   ```
   Abrir `http://127.0.0.1:8000/` y elegir un cliente. Las consultas SQL que alimentan la aplicación se administran como registros "Consultas SQL" en `http://127.0.0.1:8000/admin/` (requiere un superusuario: `python manage.py createsuperuser`).

---

## 5. Datos y limpieza

Cada CSV entregado se carga como una tabla: `cat_perfil_riesgo`, `catalogo_activos`, `catalogo_banca`, `historico_aba_macroactivos` (portafolio local, COP) e `historico_aba_usd_internacional` (portafolio internacional, USD). Las vistas de `sql/02` y `sql/03` corrigen los problemas encontrados y dejan, por cliente, la **última foto** de su portafolio.

Principales problemas de calidad detectados (detalle en `docs/hallazgos.md`):

- **Identificadores truncados por Excel** (notación científica): impiden cruzar algunos clientes con el portafolio USD. La aplicación los marca como "ID truncado".
- Filas desplazadas y duplicados.
- **Códigos de activo sin catálogo**: el 10007 (10 clientes, ≈ 4,2 % del valor local), el 1022 y la categoría "SIN CLASIFICAR". No se inventa su naturaleza: se documentan como dato faltante y se les asigna el riesgo de su clase.
- Identificadores sospechosos (por ejemplo, de 10 dígitos y una sola fecha), tratados como posibles errores de digitación.
- En USD, el campo `tipo_activo` clasifica como "Acciones y ETFs" a ETFs de bonos, a un ETF apalancado y, como "Renta fija", a notas estructuradas. El modelo los reclasifica por nombre (`sql/04_riesgo_activos.sql`).

---

## 6. Aplicación Django

Para el cliente elegido muestra:

- Totales en COP y USD, banca y perfil de riesgo declarado.
- Portafolio local: dona por macroactivo, barras de las mayores posiciones y tabla de detalle.
- Portafolio internacional: dona por tipo de activo, barras y tabla con vencimiento y cupón. Si el cliente no tiene portafolio USD, lo indica.
- **Tarjeta "Análisis del modelo"**: segmento, perfil declarado frente al perfil sugerido, estado de alineación (verde, amarillo o rojo), puntaje de riesgo en COP y USD y recomendación.

Las consultas son sentencias SQL parametrizadas guardadas en el admin de Django; las gráficas se dibujan con Plotly.

---

## 7. Modelo analítico

### Objetivo
Evaluar si el portafolio de cada cliente es **coherente con su perfil de riesgo declarado** y **sugerir un perfil** a quienes lo tienen "SIN DEFINIR", entregando recomendaciones explicables para el asesor.

El modelo es **descriptivo, no predictivo**: no estima rentabilidades futuras. Con unos 30 clientes, un modelo predictivo no sería confiable.

### Capas
1. **Variables por cliente** (`v_cliente_features`): valor total, participación por clase de activo, concentración, presencia de portafolio USD y puntaje de riesgo ponderado.
2. **Segmentación**: K-Means sobre variables estandarizadas. Se prueba k de 2 a 5, se elige por el coeficiente de silueta y se descartan los k que dejan un grupo de menos de 2 clientes. Cada segmento recibe un nombre automático (clase dominante y nivel de patrimonio).
3. **Alineación perfil frente a riesgo**: el puntaje del portafolio (promedio de los riesgos de cada activo, ponderado por valor) se traduce a un perfil implícito, y se compara con el declarado.
4. **Recomendaciones por reglas explicables**: alerta de concentración, perfil más riesgoso o más conservador que el declarado, falta de portafolio internacional con patrimonio relevante y perfil sin definir.

### Escala de riesgo por activo (1 = muy bajo, 5 = muy alto)
Cada puntaje está sustentado en una ficha con fuente y fecha en `docs/fichas_activos.md`. Bandas de perfil: **CONSERVADOR** < 2,75; **MODERADO** de 2,75 a 3,75; **AGRESIVO** ≥ 3,75.

| Activos locales | Riesgo | Sustento |
|---|---|---|
| FIC de liquidez (Renta Liquidez, Fiducuenta) | 1,0 | Calificación AAAf / S1, volatilidad < 0,5 % |
| FIC Fidurenta | 1,5 | S2 / AAAf, volatilidad 0,8 % |
| FIC Plan Semilla | 2,0 | S3 / AAAf, volatilidad 1,3 % |
| FIC Sura Crédito Privado | 3,0 | Fondo cerrado, sin calificación, activos alternativos |
| CDT Bancolombia / CDT Tuya | 1,0 / 1,5 | AAA(col) Fitch; seguro de depósitos (Fogafín) hasta $50 millones por depositante en cada entidad |
| Acciones locales | 4,5 | Volatilidad anual de 31 % a 44 % (Yahoo Finance) |

| Activos internacionales | Riesgo base | Ajustes por emisor o fondo |
|---|---|---|
| Liquidez | 1,0 | |
| Bonos del Tesoro de EE. UU. | 1,0 | Calificación AA+ estable (S&P, Fitch) |
| ETFs de bonos | 1,5 | ETF Tesoro 7-10 años: 2,5 (duración larga) |
| Bonos corporativos | 2,0 | EPM 2,5; GNB 3,0; Coltel 3,5; Braskem Idesa 5,0 (Fitch CC) |
| Fondos de bonos / mixtos / de acciones | 2,0 / 3,0 / 4,0 | Ajustes por fondo (por ejemplo, BGF Continental European Flexible: 4,0) |
| Notas estructuradas | 3,5 | Doble riesgo: índice y banco emisor |
| Acciones y ETFs de acciones | 4,0 | Volatilidad anual de 15 % a 43 % |
| ETF apalancado 3X | 5,0 | Objetivo diario de 3×; riesgo de pérdida total |

Las correcciones por activo viven en `sql/04_riesgo_activos.sql` (tablas `riesgo_activo_local` y `riesgo_usd_manual`) y cada una lleva su fuente.

### Resultados
<!-- COMPLETAR con la salida de scripts/correr_modelo.py: número de clientes, k elegido, silueta, nombre de los segmentos, cuántos clientes están alineados / más conservadores / más riesgosos / sin definir. -->
El detalle por cliente está en la tabla `resultado_modelo_cliente` y en la tarjeta de la aplicación.

### Limitaciones
- **Muestra pequeña** (≈ 30 clientes): los segmentos describen, no generalizan.
- **El puntaje de riesgo es un supuesto documentado**, no una medida estadística; cada valor se sustenta en una fuente, pero la traducción de una calificación o volatilidad a la escala 1 a 5 es criterio del analista.
- **El puntaje USD no entra en la alineación** (mezclar COP y USD requiere una tasa de cambio, que los datos no traen). Se muestra aparte.
- Códigos de activo sin catálogo (10007, 1022, SIN CLASIFICAR) usan el riesgo de su clase.
- Identificadores truncados impiden cruzar algunos clientes con el portafolio USD; 18 de los 30 clientes no tienen portafolio internacional.
- Las participaciones se calculan sobre el valor agregado, dominado por pocos clientes.
- **La volatilidad de los fondos locales no es comparable entre administradoras** (distinta metodología); la del FIC de Sura está subestimada por su valoración a TIR.
- Calificaciones crediticias: son las más recientes encontradas y pueden diferir de las vigentes en la fecha de los datos. Algunos datos (SRI de los fondos internacionales, perspectiva de Fitch de Tuya) quedan marcados como no verificados en las fichas.
- Un año de historia de precios describe el pasado reciente y no predice el futuro.

---

## 8. Documentación de apoyo

- `docs/hallazgos.md`: problemas de calidad de datos y cómo se trataron.
- `docs/fichas_activos.md`: investigación de mercado, una ficha por activo local y por familia internacional, con fuente y fecha de consulta.

## 9. Uso de herramientas de IA
Se usó un asistente de IA (Claude) como apoyo para estructurar el trabajo, revisar el código y buscar fuentes de mercado. Las decisiones del modelo, los puntajes de riesgo y las conclusiones fueron revisados por la autora. <!-- Ajusta esta sección para que describa con exactitud lo que hiciste. -->

## 10. Posibles mejoras
- Incorporar tasa de cambio para incluir el portafolio USD en la alineación.
- Cuarentena en la limpieza para los identificadores que no tengan 11 dígitos o tengan una sola fecha.
- Reemplazar el puntaje fijo de las acciones por uno derivado de la volatilidad de cada activo, y calcular la volatilidad esperada del portafolio.
- Un umbral de concentración más selectivo (el actual marca a casi todos los clientes).