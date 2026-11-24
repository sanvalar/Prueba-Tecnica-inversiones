# Hallazgos del modelo analítico

Resultados de `scripts/correr_modelo.py` con los datos entregados (31 clientes). El detalle por cliente está en la tabla `resultado_modelo_cliente`.

## ¿Cuántos segmentos hay y qué los diferencia?

Hay 3 segmentos (K-Means, silueta ≈ 0,56; se descarta k = 4 porque dejaría un grupo de un solo cliente):

| Segmento | Clientes | Composición | Puntaje de riesgo |
|---|---|---|---|
| FICs, patrimonio medio | 14 | Casi 100 % en FICs y CDT | 1,0 a 2,5 |
| Renta variable, patrimonio bajo | 14 | 100 % en acciones | 4,4 a 5,0 |
| Diversificado, patrimonio alto | 3 | Portafolios grandes, con renta fija, FICs o acciones | 1,5 a 4,3 |

## Clientes con el perfil sin definir

15 de 31 clientes (48 %) tienen el perfil SIN DEFINIR. El perfil que sugiere su portafolio (`perfil_implicito`):

- 11 clientes: AGRESIVO (todos con 100 % en acciones).
- 4 clientes: CONSERVADOR (todos con 100 % en FICs).

Ninguno resulta moderado: sus portafolios son de un solo tipo de activo y caen en los extremos.

## Clientes con perfil definido

| Estado | Clientes | Detalle |
|---|---|---|
| Alineado | 5 | 4 conservadores y 1 agresivo |
| Más conservador que su perfil | 8 | 7 moderados y 1 agresivo |
| Más riesgoso que su perfil | 3 | Todos moderados |

Solo 5 de los 16 clientes con perfil (31 %) tienen un portafolio coherente con él. Los 8 "más conservadores" son una oportunidad comercial (espacio para más riesgo); los 3 "más riesgosos" requieren revisar su exposición: son moderados con 100 % en acciones.

## Alertas de concentración

25 de 31 clientes superan el umbral (≥ 80 % en una posición y 2 o menos posiciones): 14 con ID completo, a quienes se les muestra la alerta, y 11 con ID truncado, a quienes se les pide validar el ID antes de evaluar concentración. El umbral es poco selectivo en esta base porque casi todos los clientes tienen una sola posición.

## Patrimonio local alto sin portafolio internacional

6 clientes tienen más de $50 millones COP en local y ningún portafolio USD. Cinco de ellos tienen el identificador truncado por Excel, así que podrían tener USD sin que se pueda cruzar. En total, 19 de los 31 clientes no tienen portafolio USD.

## Un caso concreto

Cliente 10039616197:

- Perfil declarado: SIN DEFINIR.
- Local (15/05/2024): $18.357.700 COP, 100 % renta variable en 3 posiciones. Puntaje 4,7 (agresivo).
- Internacional (30/05/2024): USD 5.610,22. Puntaje USD 1,5 (bajo).
- El modelo sugiere completar su perfil: su parte local se comporta como agresiva.
- Matiz: el portafolio internacional es mucho más conservador que el local; mirar solo el local sobreestima su riesgo total.
