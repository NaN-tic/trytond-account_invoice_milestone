Hitos
=====

**Tryton** ofrece la opción de programar el momento de emisión de la 
factura/s, generada/s por una venta. Esta será emititada en función del tipo de 
hito, el disparador, el método de facturación y el cálculo de fechas para 
determinar el momento en que se realizará la facturación.

El tipo de hito será:

* Sistema

* Manual

El disparador de la factura podrá ser:

* Al confirmar el pedido	

* Al enviar un porcentaje

* Al enviar completamente el pedido

El método de facturación será: 

* Porcentaje sobre el total

* Fijo

* Líneas de venta

* Remanente


Cuando queramos crear un nuevo hito tendremos que crearlo en el menú 
|menu_milestone_group_type|. En cada hito podremos crear tantas líneas como 
facturas queramos que se deriven de la venta. 

Siguiendo estas directrices podríamos crear un ejemplo como el que sigue:

Nombre: 50% por adelantado a los 10 días de confirmar el pedido y el resto al 
enviar completamente el pedido.

Líneas: Línea 1: Sistema, Al confirmar el pedido, Porcentaje sobre total. 
Línea 2: Sistema, Al enviar completamente el pedido, Remanente

En el momento en que procesamos la venta se creará un nuevo “Grupo de hitos” 
que 
dará número al grupo de facturas (hitos) que se generarán debido a la venta. De 
esta manera veremos como, siguiendo el caso del ejemplo, una factura por 
avanzado ha sido creada. La podremos ver en la pestaña “Facturas”, de la misma 
venta. 

Esta factura tendrá un número de hito, que es correlativo y sigue una 
secuencia. Igual que el resto de facturas que haya sido creada por hitos, sigue 
las líneas del “Tipo de grupo de hitos” que hayamos seleccionado para la venta. 
En este caso, se generará de forma automática debido a que la función del tipo 
de hito es sistema, en lugar de manual.

Para introducir el decalaje de tiempo que queramos en una venta se pueden 
aplicar días, meses, semanas, etc. y el procedimiento seria:

 * Indicar en que mes queremos iniciar la cuenta, seleccionar cántos meses 
   posterior queremos que pasen después del seleccionado (si queremos meses)

 * Indicar en que dia de la semana queremos iniciar el hito y el número de 
   semanas posteriores

 * Y finalmente, indicar el número de dia del mes y la cantidad de días 
   posteriores a esta fecha para iniciar el cálculo de la data de facturación

Los hitos nos ofrecen varias opciones, como modificarlos, crearlos manualmente 
o cancelarlos, así pues podemos cancelar, modificar y añadir cualquier hito, 
aún y estando dentro de un grupo de hitos creado.

**Cancelar hitos**

En caso de cancelar una factura u otro motivo. Una vez tenemos todos los hitos 
de un grupo de hitos cancelados, este grupo quedará automáticamente cancelado. 

Así mismo, cuando cancelamos una factura generada desde un hito, esta quedará 
en estado "Fallado" indicándole al usuario que tienen pendiente un paso de 
control pendiente. Podrá llevar a cabo una de las siguientes acciones, antes de 
cancelar el hito:

 * Si no se ha de volver a facturar el hito, simplemente cancelarlo
 
 * Si queremos volver a facturarlo; duplicaremos, crearemos un nuevo hito con 
 las nuevas condiciones o tendremos un hito "remanente" no cancelado en el 
 grupo, para acabar cancelando el hito.

**Crear hitos manualmente**

Otra opción que nos ofrece el sistema es crearlos manualmente. En el momento 
de generar la venta, en la pestaña "Información adicional", podemos crear un 
grupo de hitos nuevo o bien, añadirle un grupo generado anteriormente para otra 
u otras ventas, con hitos. No será necesario vincularle un "Tipo de grupo de 
hitos". Esta opción nos facilitará casos en los que para un mismo Tercero 
tengamos ventas de diferentes fechas de aceptación pero con hitos iguales, así 
el control será más rápido y sencillo, reduciendo la cantidad de grupos de 
hitos creados. 

**Localizar hitos**

Si queremos localizar el número de hito nos dirigiremos a la *Información 
adicional* dentro de la *Factura*, al camppo *Hito*. Este paso nos permitirá 
confirmar si una factura proviene de una venta o si forma parte de un grupo de 
futuras facturas (hitos). 

Por otro lado, si queremos localizar el grupo de hitos tendremos que acceder 
des de las *Ventas*, en la pestaña *Información adicional* veremos los dos 
campos:

 * Grupo de hitos
 
 * Tipo de Grupo de hitos


Y finalmente, en el menú |menu_account_invoice_milestone_group| encontraremos 
los códigos de los hitos que hemos realizado, los importes totales de las 
factura, los importes meritados, por asignar, los facturados y el estado de cada
Grupo de hitos.


.. |menu_milestone_group_type| tryref:: account_invoice_milestone.menu_invoice_milestone_group_type/complete_name
.. |menu_account_invoice_milestone_group| tryref:: account_invoice_milestone.menu_invoice_milestone_group/complete_name
