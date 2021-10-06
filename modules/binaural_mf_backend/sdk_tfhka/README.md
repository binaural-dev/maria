# Instruccion de uso del demo (linux/Unix)

Para usar la primera vez la impresora en linux se debe agregar el usuario que ejecuta el demo (o el sdk) al grupo **dialout**,
el grupo **dialout** gestiona las conexiones al puerto serial en los equipos linux/unix, para esto ejecutar el siguiente comando como sudo

`sudo adduser $USER dialout`

Ingresar el password del usuario y luego hacer logout para que agregue el usuario activo al grupo dialout

Para ejecutar el demo, instalar virtualenv y crear un ambiente virtual, para distros deb usar

`sudo apt install python3-virtualenv`

Luego crear el virtualenv con

`virtualenv ruta_padre_del_proyecto`

y activar el virtualenv con 

`source /ruta_del_virtualenv/bin/activate`

Ejecutar archivo demo.py ubicado en la raiz del proyecto

## Uso de SDK
Para usar el SDK en cualquier aplicacion python se debe instanciar la clase `Tfhka()` la cual contempla todos los metodos para conectacte al puerto de la impresora

Para hacer cualquier comunicacion con la impresora es necesario llamar primero al metodo `OpenFpctrl` el cual abre el puerto de la impresora para comunicacines

Es importante (no obligatorio) usar el metodo `CloseFpctrl` el cual cierra la conexion con la impresora

La mayoria de los metodos devuelve exepciones con fallos a conexion y similares, la clase `tf_ve_ifpython` tiene 2 atributos (envio y error) que guardan informacion de conexion y estatus de la maquina

En el wiki https://dev.binaural.com.ve/binaural/ecosistema/backend/librerias-funciones/python/tfhka/-/wikis/Informacion-basica se encuentra la informacion detallada de los comandos del crudos y la descripcion de la clase Tfhka con sus atributos y metodos asociados