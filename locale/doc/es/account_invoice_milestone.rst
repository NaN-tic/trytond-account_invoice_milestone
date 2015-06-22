Hitos
=====

Este módulo ofrece la opción de programar el momento de emisión de la 
factura/s, generada/s por una venta. Esta será emititada en función del tipo de 
hito, el disparador, el método de facturación y el cálculo de fechas para 
determinar el momento en que se realizará la facturación.

El tipo de hito será:
*Sistema
*Manual

El disparador de la factura podrá ser:
* Al confirmar el pedido	
* Al enviar un porcentaje
* Al enviar completamente el pedido

El método de facturación será: 
*Porcentaje sobre el total
*Fijo
*Líneas de venta
*Remanente

Cuando queramos crear un nuevo hito tendremos que crearlo en el menú 
Contabilidad / Configuración / Hitos / Tipos de grupo de hitos. En cada hito 
podremos crear tantas líneas como facturas queramos que se deriven de la venta. 
Siguiendo estas directrices podríamos crear un ejemplo como el que sigue:

Nombre: 50% por adelantado a los 10 días de confirmar el pedido y el resto al 
enviar completamente el pedido.
Líneas: 	Sistema, Al confirmar el pedido, Porcentaje sobre total  
		Sistema, Al enviar completamente el pedido, Remanente

En el momento en que procesamos la venta se creará un nuevo “Grupo de hitos” que 
dará número al grupo de facturas (hitos) que se generarán debido a la venta. De 
esta manera veremos como, siguiendo el caso del ejemplo, una factura por 
avanzado ha sido creada. La podremos ver en la pestaña “Facturas”, de la misma 
venta. 
Esta factura tendrá un número de hito, que es correlativo y sigue una secuencia. 
Pgual que el resto de facturas que haya sido creada por hitos, sigue las 
líneas del “Tipo de grupo de hitos” que hayamos seleccionado para la venta. En 
este caso, se generará de forma automática debido a que la función del tipo de 
hito es sistema, en lugar de manual.

Si queremos localizar el número de hito nos dirigiremos al menú: Factura / 
Información adicional / Hito. Este paso nos permitirá confirmar si una factura 
proviene de una venta o si forma parte de un grupo de futuras facturas (hitos). 

Por otro lado, si queremos localizar el grupo de hitos tendremos que acceder 
al menú: Ventas / Información adicional / Grupo de hitos

En el menú Grupo de hitos (Contabilidad / Hitos / Grupos de hitos) 
encontraremos los códigos de los hitos que hemos realizado, los importes totales 
de las factura, los importes meritados, por asignar, los facturados y el estado 
de cada Grupo de hitos.