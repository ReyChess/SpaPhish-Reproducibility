Historical CMAR excluded from primary comparison. Independent verification report supplied with the author archive, see separate downloadable evidence ZIP.

# Verificación del JAR de CMAR para JISA

Auditoría del fold 1 de SpaPhish. Se revisaron archivos existentes, se desensambló el JAR y se decodificaron reglas guardadas. No se entrenó ni se modificó ningún experimento histórico.

## 1. Versiones y procedencia

| Componente | Prueba corta | Histórico `results_cmar_tuned/r_session_info.txt` | Estado |
|---|---|---|---|
| R | 4.3.3 (2024-02-29 ucrt), Windows x64 | Misma versión y plataforma | Confirmada |
| arules | 1.7-7 | 1.7-7 | Confirmada |
| arulesCBA | 1.2.7 | 1.2.7 | Confirmada |
| Java | El ejecutable de la ruta registrada informa Microsoft OpenJDK 11.0.16.1 LTS, build 11.0.16.1+1-LTS, 64 bits | Sin versión ni ruta de Java en los artefactos revisados | Confirmada para el ejecutable consultado, no confirmada para el histórico |

El log de la prueba corta registró la ruta de Java, pero no guardó `java -version` al entrenar. La versión indicada se obtuvo consultando ese mismo ejecutable durante la auditoría. Su identidad binaria en la fecha de la prueba es **no confirmada** por falta de una huella contemporánea. Las sesiones también difieren en compilación de Windows (26300 frente a 26200) y configuración regional (C frente a English_United States.utf8).

**Confirmada.** Las cuatro llamadas apuntan a `[ruta local]/CMAR.jar`. El archivo instalado tiene SHA-256 `0A9EC7B1DD8677113106E1C5895A72DC10478DBCE23478B630DEEACE09FFB6D9`, obtenido con `Get-FileHash`. Su MD5 `2528C0EAF326DF04EBF95D7CE7151366` coincide con el que registró el script durante la prueba.

**No confirmada.** La identidad del JAR original. Se revisaron las carpetas históricas del proyecto y de ModelosAC y los inventarios de `results_cmar_tuned.zip` y `probarDataset.zip`. Los resultados, reglas, resúmenes y registros de sesión disponibles carecen de un binario histórico o una huella contemporánea comparable. Compartir la versión del paquete y producir las mismas reglas en el fold 1 no permite deducir un SHA-256. **Pendiente** si se consigue una copia archivada del entorno original o una huella de esa ejecución.

## 2. Llamadas exactas y soporte registrado

**Confirmada.** Las cuatro llamadas usaron `-S1`, `-S10`, `-S30` y `-S50`, respectivamente, con `-C80` en cada caso. El apéndice conserva el texto completo de las llamadas y de las dos líneas de soporte cero por ejecución, con números de línea del log original.

| Soporte solicitado | Mínimo al leer el archivo (registros) | Mínimo durante Apriori-TFP (registros) |
|---:|---:|---:|
| 1 % | 12.54 | 0.0 |
| 10 % | 125.4 | 0.0 |
| 30 % | 376.2 | 0.0 |
| 50 % | 627.0 | 0.0 |

## 3. Fase en la que se aplica el cero

**Confirmada.** El cero es el umbral usado durante la minería, incluida la poda del árbol de soportes. El desensamblado del JAR verificado con `javap -c -p` muestra esta secuencia:

1. `runCMAR.main` lee y reordena la entrada y llama a `AprioriTFP_CMAR.startClassification`. `startClassification2` llama a `AprioriTFP_CARgen.startCARgeneration2` antes de la poda por cobertura.
2. `AssocRuleMining.inputDataSet` calcula el umbral inicial a partir de `numRows`. `startCARgeneration2`, en los offsets 0–15, sobrescribe `minSupport` con `numRowsInTrainingSet * support / 100`. Después imprime `Minimum support` y llama a `createPtree` y `createTotalSupportTree` en los offsets 137 y 141 de la rama de consola.
3. `PartialSupportTree.createTotalSupportTree` lee ese campo en el offset 33 para imprimir `Minimum support threshold` y llama a `contCreateTtree` en el 80. `TotalSupportTree.pruneLevelN` compara el soporte del nodo con `minSupport` en los offsets 31–40. `AprioriTFP_CARgen.generateCARs(int)` también compara con ese campo en los offsets 120–129. Las cuatro corridas registraron 1.729.647 conjuntos frecuentes y detuvieron su generación en el nivel 5 tras superar el límite de 500.000.
4. El rótulo `Number of records in training set` imprime `numRows`, según `AprioriTFPclass.outputLimits()` (offset 32), mientras que el recálculo usa `numRowsInTrainingSet`. Son campos distintos. Con los porcentajes positivos registrados, el recálculo y el cero observado son coherentes con `numRowsInTrainingSet = 0` al entrar en esa rutina. Esta conclusión se limita a la ruta de consola inspeccionada y no atribuye un origen histórico al estado del campo.

## 4. Fold y comparación con el histórico

- **Confirmada.** La prueba corta prepara una sola vez los 1.254 registros con `fold != 1` y pasa el mismo objeto de transacciones a los cuatro ajustes. Cada llamada serializa ese objeto en su propio archivo temporal y el JAR informa 1.254 registros en las cuatro llamadas. El CSV disponible reproduce el tamaño de la partición y los 141 identificadores y etiquetas de prueba. **No confirmada** la igualdad byte a byte de los cuatro archivos temporales, que ya no están disponibles.
- **Confirmada.** Los cuatro bloques Java contienen las mismas 1.135 líneas de reglas en el mismo orden, incluidos los conteos y confianzas impresos. Las cuatro configuraciones coinciden en las 141 predicciones (116 aciertos, exactitud 82.27 %, macro-F1 0.815416). Las seis comparaciones entre configuraciones dan cero diferencias.
- **Confirmada.** Al decodificar las reglas del log con el mapeo de ítems de `arulesCBA` y la partición disponible, las 1.135 reglas coinciden en texto y orden con `cmar_rules_fold_1.csv`. El máximo delta absoluto de soporte, confianza, lift y Laplace es 4.89 × 10⁻¹⁵. Las 141 predicciones históricas coinciden por identificador y clase real. El histórico declara soporte 4 % y confianza 80 %. El 4 % no fue una de las cuatro llamadas de la prueba corta.
- **Confirmada.** Los diez folds históricos seleccionaron 4 % de soporte y 80 % de confianza. En las 30 combinaciones de fold y confianza, los cinco soportes probados dieron exactamente la misma media y desviación estándar de macro-F1 interna y el mismo promedio de reglas. El script histórico ordena primero por macro-F1 y, en empate, favorece mayor soporte. El 4 % era el máximo de la rejilla.
- **Confirmada.** Todos los folds históricos exportaron reglas con soporte medido por debajo del 4 % seleccionado. En total son 6.663 reglas, incluidas 668 de las 1.135 del fold 1. El mínimo del fold 1 es 0.003189793 como proporción (4/1.254, aproximadamente 0.319 %). Los recuentos de reglas exportadas coinciden con los del resumen de cada fold.
- **No confirmada.** La identidad del JAR histórico y la traza interna de cada ejecución histórica. Los resultados históricos permiten evaluar el incumplimiento del filtro aun sin identificar el binario original.

## 5. Decisión editorial

**Confirmada la justificación técnica para excluir de la comparación principal de JISA esta ejecución histórica de CMAR ajustado por soporte.** La exclusión se puede fundamentar en los propios resultados históricos: la rejilla empata en todos los soportes para cada fold y confianza, y las reglas exportadas incumplen el soporte seleccionado en los diez folds. La prueba corta aporta evidencia adicional del mecanismo en el JAR inspeccionado y reproduce las reglas y predicciones del fold 1. La conclusión aplica a esta implementación y configuración experimental.

> Excluimos de la comparación principal los resultados de CMAR obtenidos con esta implementación porque el soporte seleccionado del 4 % no se reflejó en el filtrado de las reglas exportadas en ninguna de las diez particiones externas. En la primera partición, un diagnóstico posterior reprodujo las reglas y predicciones históricas con cuatro valores de soporte. El JAR inspeccionado aplicó un mínimo de cero registros durante la generación.

**Pendiente.** Si se decide reincorporar CMAR, validar primero el filtro con un control de soporte conocido y después repetir el protocolo experimental con una implementación que pase ese control.

## Apéndice. Extracto de cmar_stdout.log con rutas locales ocultas


~~~text
6 Testing support = 0.01, confidence = 0.8
8 Call: java -Xmx2048m -cp [ruta local]/CMAR.jar runCMAR -N2 -F[archivo temporal].num -S1 -C80
18    [9] "Number of records = 1254"
20   [11] "Min support       = 12.54 (records)"
29   [20] "Minimum support = 0.0 (Records)"
32   [23] "Number of records in training set = 1254"
36   [27] "Minimum support threshold = 1.0% (0.0 records)"
37   [28] "Level = 5, Number of frequent sets (1729647) generted so far exceeds limit of 500000, generation process stopped!"
44   [35] "Number of CMAR rules    = 1135"
1184 Rules used: 1135
1194 Testing support = 0.1, confidence = 0.8
1196 Call: java -Xmx2048m -cp [ruta local]/CMAR.jar runCMAR -N2 -F[archivo temporal].num -S10 -C80
1206    [9] "Number of records = 1254"
1208   [11] "Min support       = 125.4 (records)"
1217   [20] "Minimum support = 0.0 (Records)"
1220   [23] "Number of records in training set = 1254"
1224   [27] "Minimum support threshold = 10.0% (0.0 records)"
1225   [28] "Level = 5, Number of frequent sets (1729647) generted so far exceeds limit of 500000, generation process stopped!"
1232   [35] "Number of CMAR rules    = 1135"
2372 Rules used: 1135
2382 Testing support = 0.3, confidence = 0.8
2384 Call: java -Xmx2048m -cp [ruta local]/CMAR.jar runCMAR -N2 -F[archivo temporal].num -S30 -C80
2394    [9] "Number of records = 1254"
2396   [11] "Min support       = 376.2 (records)"
2405   [20] "Minimum support = 0.0 (Records)"
2408   [23] "Number of records in training set = 1254"
2412   [27] "Minimum support threshold = 30.0% (0.0 records)"
2413   [28] "Level = 5, Number of frequent sets (1729647) generted so far exceeds limit of 500000, generation process stopped!"
2420   [35] "Number of CMAR rules    = 1135"
3560 Rules used: 1135
3570 Testing support = 0.5, confidence = 0.8
3572 Call: java -Xmx2048m -cp [ruta local]/CMAR.jar runCMAR -N2 -F[archivo temporal].num -S50 -C80
3582    [9] "Number of records = 1254"
3584   [11] "Min support       = 627.0 (records)"
3593   [20] "Minimum support = 0.0 (Records)"
3596   [23] "Number of records in training set = 1254"
3600   [27] "Minimum support threshold = 50.0% (0.0 records)"
3601   [28] "Level = 5, Number of frequent sets (1729647) generted so far exceeds limit of 500000, generation process stopped!"
3608   [35] "Number of CMAR rules    = 1135"
4748 Rules used: 1135
~~~text
