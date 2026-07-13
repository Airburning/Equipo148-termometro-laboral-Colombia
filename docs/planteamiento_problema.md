# Planteamiento del problema

## Contexto

El desempleo en Colombia tiene fuertes diferencias regionales: la Tasa de
Desocupación (TD) de la región Caribe o de Orinoquía/Amazonía/Insular no se
mueve igual que la de la región Central, ni en el mismo momento del ciclo
económico. Las cifras oficiales del DANE (Gran Encuesta Integrada de
Hogares, GEIH) reportan esta tasa de forma retrospectiva, semestre a
semestre — no hay una proyección oficial de hacia dónde va cada región en
el semestre siguiente.

## Pregunta que responde el proyecto

> Dado el historial reciente de indicadores laborales de una región
> (TD, TO, TGP, TS) y el contexto macro de informalidad (laboral,
> empresarial, de micronegocios) y de desigualdad interna de esa región,
> **¿cuál será la Tasa de Desocupación del semestre siguiente?**

Es un problema de **forecasting a un paso**, resuelto por separado para
cada una de las 5 grandes regiones del DANE (Caribe, Central, Oriental,
Orinoquía/Amazonía/Insular, Pacífica).

## Por qué es un problema no trivial

- La TD tiene una **tendencia estructural fuerte y no estacionaria**: cayó
  de ~20% en 2010 a ~8% en 2025 a nivel nacional. Un modelo que solo vea el
  nivel histórico corre el riesgo de no saber extrapolar fuera del rango
  que ya observó en entrenamiento (ver `docs/marco_metodologico.md`,
  sección "el truco: predecir el cambio, no el nivel").
- Las fuentes oficiales de informalidad (GEIH-ANEXOS, IMIE) son
  **nacionales**, no regionales, y no todas cubren el rango completo
  2010-2025 — hay que decidir cómo extenderlas sin inventar señal donde no
  la hay (ver `docs/fuentes_datos.md`).
- El panel resultante es pequeño para estándares de ML (160 filas: 5
  regiones × 32 semestres), lo que limita cuántas variables se le pueden
  dar al modelo sin sobreajustar (ver `docs/conclusiones.md`).

## A quién le sirve

Un insumo de este tipo es útil para:

- Priorización de política pública activa de empleo por región.
- Contexto para decisiones de inversión/apertura de operaciones que sean
  sensibles al ciclo laboral regional.
- Como ejercicio metodológico de integración de múltiples fuentes
  oficiales dispersas (6 archivos, 3 formatos, 3 granularidades distintas)
  en un solo panel analítico reproducible.

## Alcance y lo que el proyecto NO hace

- No predice desempleo a nivel de departamento o ciudad (se mantiene a
  nivel de las 5 grandes regiones DANE; ver `docs/conclusiones.md` para la
  discusión de por qué se descartó ese nivel de granularidad).
- No es un modelo causal: no identifica *por qué* sube o baja la TD, solo
  proyecta su valor más probable dado el patrón histórico.
- No incorpora choques no observados en el historial (una crisis nueva,
  un cambio de política abrupto) — es una proyección estadística, no un
  escenario de política.
