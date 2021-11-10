Para la carpeta enterprise descargar aparte dicha carpeta dentro del directorio raiz de este proyecto
Nota: se tenia anteriormente el submodulo pero el mismo causaba conflicto en odoo.sh y se removio

Para verificar que el contenedor este corriendo satisfactoriamente ejecutar ./test_deploy_local.sh

El contenedor corre por el puerto : 15000

Enlace con Tutorial para correr pruebas unitarias: https://reedrehg.medium.com/writing-tests-in-odoo-4355f33e4a36

Los modulos deberan tener el estilo Snake case ejemplo:
    binaural_*

    Recordar que los nombres deben ser todos en minuscula y en español asi como el nombre debera ser corto

En el archivo manifest colocar la descripcion de lo que hace el modulo asi como llenar la informacion y colocar logo (se encuentra en el proyecto con el nombre: icon.png), todo esto es obligatorio

Los nombre de las clases seran estilo Camel case y el nombre debera contener la clase a la que se hereda mas el nombre del modulo ejemplo:

    AccountMoveBinauralFacturacion

    Recordar que se debe evitar en la medida de lo posible tener la misma funcion en modulos diferentes ya que pueden perderse funcionalidades

Para el manejo de Gitlab considerar:
Commit message: ^((Merge branch '(.*)' into '(.*)')\n\n)?(fix|feat|BREAKING CHANGE|build|ci|docs|perf|refactor|style|test|revert)\(?.*\)?:((.|\n)*)$ 
Branch name: (hotfix_([a-zA-Z_-]*)|fix_([a-zA-Z_-]*)|feature_([a-zA-Z_-]*)|issue_([a-zA-Z_-]*)|test_([a-zA-Z_-]*)|cicd_([a-zA-Z_-]*))

