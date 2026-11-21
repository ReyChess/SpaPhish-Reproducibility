# SpaPhish — Verificación reforzada de CMAR (19 noviembre 2026)

## Resultado comprobado sobre el archivo canónico de GitHub

Se inspeccionaron directamente los 1.395 registros y sus 45 indicadores del
`data/spaphish_binary_folds.csv` de `ReyChess/SpaPhish-Reproducibility`.
Para el primer fold externo hay 1.254 ejemplos de entrenamiento
(597 legítimos, clase 77; 657 phishing, clase 78).

Con **soporte conjunto mínimo 0.50**, el umbral de frecuencia es
`ceil(0.5 × 1254) = 627` transacciones. Sólo seis indicadores pueden
aparecer en antecedentes frecuentes. Tras **enumerar todos sus 63
subconjuntos no vacíos** y contar la conjunción antecedente+consecuente,
**una sola CAR** pasa el umbral: `DISTRACTION_YES -> phishing (78)`,
con 638/1254 de soporte conjunto, y 638/941 = **0.6780 de confianza**.

Por tanto, con `support=0.50` y `confidence=0.80`, **ninguna CAR no vacía
puede cumplir simultáneamente ambos parámetros** en este mismo fold
y esta representación basada sólo en indicadores presentes.

Es incompatible con el registro histórico de 1.135 reglas **si** ese
registro correspondía realmente a esos mismos datos y esos umbrales
conjuntos. Esta prueba no identifica por sí sola si el problema está
en la versión histórica del wrapper, el comando Java, el preprocesado,
la implementación interna o en la correspondencia del registro.

## Verificación del código externo

- `arulesCBA/R/LUCS_KDD_CBA.R` construye `-S{floor(100*support)}`
  y `-C{floor(100*confidence)}`; no omite el parámetro.
- `Work/LUCS_KDD/runCMAR.java` pasa los argumentos al constructor
  `AprioriTFP_CMAR(args)`.
- Se inspeccionó también código de CMAR en KEEL, **que NO demuestra
  el comportamiento del mismo JAR histórico**: allí se utiliza
  un mínimo calculado como `numRows*support/100`.

No se ha ejecutado aquí el JAR original porque en este entorno
no están disponibles Rscript ni una copia local del JAR y el acceso
a la descarga binaria está restringido. Por ello, la causa concreta
**no está determinada**.

## Archivos e instrucciones

1. Obtener el CSV original sin modificar desde
   `https://github.com/ReyChess/SpaPhish-Reproducibility/blob/main/data/spaphish_binary_folds.csv`.
2. Ejecutar `python verify_cmar_support.py spaphish_binary_folds.csv`
   para corroborar independientemente las cifras 1 / 0.
3. Donde estén instalados R, `arulesCBA`, `arules` y el JAR de CMAR,
   ejecutar `Rscript diagnostic_CMAR_fold1.R spaphish_binary_folds.csv output_cmar_fold1`.
4. Conservar `sessionInfo.txt`, `jar_info.csv`, las llamadas Java,
   las reglas, los soportes y las predicciones para cada soporte.
5. Si el resultado sigue produciendo las mismas 1.135 reglas a 0.50,
   comprobar si los soportes conjuntos recalculados violan el umbral
   y capturar el comando exacto ejecutado.

## Decisión editorial

No se modifica la tesis ni el 88.24 % de DMC-AC.
El resultado CMAR 82.01 % puede citarse **sólo como histórico y con la
advertencia sobre su configuración**, no como una nueva reproducción
verificada. No declarar que el parámetro no se transmite por R: el
código actual muestra que sí se transmite.
