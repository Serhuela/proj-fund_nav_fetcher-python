
Con solo el ISIN puedes localizar el valor liquidativo y su fecha en varias páginas oficiales y APIs.[14][23][24] No he encontrado un feed público, gratuito y oficial que cubra de forma uniforme todos los fondos comercializables en España.[1][14][15] Para el Docker, usaría una API autorizada como fuente principal y las webs de las gestoras para verificar los datos.[14][24]

Comprobaciones con ING y MyInvestor

- ING — ES0152769032, ING Direct Fondo Naranja S&P 500: la ficha oficial de Amundi muestra el ISIN y un valor de 45,6705203 €, fechado 08/10/2026.[24]
- MyInvestor — ES0165243025, MyInvestor Value clase C: la CNMV identifica a Andbank Wealth Management como gestora.[2] La tabla oficial de Andbank muestra 1,3068903, fechado 05/10/2026.[23]

Así que el flujo ISIN → gestora → fuente oficial funciona para estos ejemplos. La diferencia entre fecha de valoración y fecha de consulta es importante: guarda la primera, no solo cuándo recogiste el dato.[2][23][24]

Dónde consultarlos

- CNMV: sirve para resolver el fondo y su gestora por ISIN y consultar documentación oficial.[2] La CNMV explica que, normalmente, el valor aplicable a una operación se publica al día siguiente; no encontré en las páginas revisadas una API pública consolidada de series diarias.[1][2]
- Web de la gestora: mi primera opción para validar el valor; los ejemplos son Amundi para el fondo de ING y Andbank para MyInvestor Value.[23][24]
- Inversis: su ayuda describe valores diarios e históricos para los fondos que comercializa, con consulta por gestora, fondo y periodo. No encontré una API pública directa basada solo en ISIN.[22]
- Quefondos/VDOS y Finect/Morningstar: útiles para contrastar valor, fecha e histórico por ISIN, pero los trataría como fuentes secundarias, no como backend. En el ejemplo consultado, Finect mostraba fecha 07/10 y Amundi 08/10.[9][28][24]
- ING y MyInvestor: sus páginas sirven para ver catálogo y rentabilidades, pero MyInvestor indica que puede mostrar los datos con dos días de retraso y que algunos fondos tienen menor frecuencia.[6]

APIs para automatizar

1. Allfunds API — mejor encaje funcional sobre el papel. Documenta históricos de NAV y un endpoint con la serie diaria del último mes; acepta ISIN y devuelve fecha, valor y divisa.[14] Requiere token y permisos de acceso; no encontré precio público ni confirmación de cobertura para tus ISIN concretos.[14]
2. Twelve Data Mutual Funds API. Ofrece series históricas y permite filtrar por ISIN mediante un complemento de datos.[15][16] Anuncia más de 300.000 fondos globales con actualizaciones diarias y un precio inicial de US$329/mes para datos de fondos.[15] Hay que probar la cobertura de cada ISIN español antes de contratar.[15][16]
3. FactSet o FE fundinfo. FactSet anuncia series históricas para más de 161.000 clases de fondos en Europa; FE fundinfo anuncia más de 100.000 fondos activos y más de 300.000 clases globalmente.[17][18] Sus páginas invitan a solicitar demo o muestra; confirmaría precio, acceso y licencia directamente con cada proveedor.[17][18]

No hice pruebas autenticadas contra estas APIs; la cobertura real de tus ISIN queda pendiente de validar con acceso del proveedor.[14][15]

Recomendación: probar primero Allfunds y Twelve Data con los dos ISIN anteriores, y comparar fecha, valor y divisa con las páginas de Amundi y Andbank.[14][15][24] En la base de datos guardaría ISIN, fecha_valor, valor, divisa, fuente y fecha_consulta; consultaría en días laborables y deduplicaría por (ISIN, fecha_valor), porque el NAV puede publicarse después de su fecha de valoración y algunas clases no publican diariamente.[1][6][14]

Fuentes

[1] https://www.cnmv.es/portal/inversor/fondos-como-invertir?lang=en  
[2] https://www.cnmv.es/portal/consultas/iic/fondo?isin=ES0165243025&lang=es   (1/2)
[6] https://myinvestor.es/inversion/fondos-inversion  
[9] https://www.finect.com/fondos-inversion/ES0152769032-Ing_direct_fn_sp_500_fi  
[14] https://api.allfunds.dev  
[15] https://twelvedata.com/mutual-funds  
[16] https://twelvedata.com/docs/mutual-funds  
[17] https://developer.factset.com/api-catalog/factset-funds-api  
[18] https://www.fefundinfo.com/products/institutions/data-feeds  
[22] https://www.inversis.com/ayuda/co_pr_busfon.html  
[23] https://www.andbank.es/andbank-wealth-management/fondos-y-sicav/valores-liquidativos  
[24] https://www.amundi.es/retail/product/view/ES0152769032  
[28] https://www.quefondos.com/es/fondos/ficha/index.html?isin=ES0152769032 (2/2)