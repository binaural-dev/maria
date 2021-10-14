// Ventas, compras, facturación -> probar presupuesto con diferentes tasas

odoo.define("account.tour_accounting", function (require) {
  "use strict";
  var core = require("web.core");
  var tour = require("web_tour.tour");
  var _t = core._t;
  //  Caso #3 :
  //   *Generar facturas de proveedores con retenciones validadas  (misma razón social)
  //   *Generar una factura de proveedores marcando el checkbox de retenciones para generar retención IVA automática. Luego ir al menú de retenciones IVA  - proveedores, validar secuencias.
  //  Features:
  //   *Usar la misma razón social
  //   *Generar facturas continuas, hasta llegar a 10 facturas.

  tour.register(
    "account_retenciones",
    {
      test: true,
      url: "/web",
      sequence: 65,
    },
    [
      tour.stepUtils.showAppsMenuItem(),
      //Entrar a modulo de Contabilidad
      {
        content: "open accounting",
        trigger: '.o_app[data-menu-xmlid="account_accountant.menu_accounting"]',
      },
      //Seleccionar submenu Proveedores
      {
        content: "Go to Providers",
        trigger: 'a:contains("Proveedores")',
      },
      //Seleccionar opcion Facturas
      {
        content: "Go to Invoices",
        trigger: 'span:contains("Facturas")',
      },
      // Seleccionar boton crear factura
      {
        trigger: ".o_list_button_add",
      },
      ///Escribir nombre de factura
      {
        content: "Writte Invoices Name ",
        trigger: "input#o_field_input_847",
        run: "text pruebaFactura",
      },
      ///Escribir numero de control
      {
        content: "Writte Control Number ",
        trigger: "input#o_field_input_770",
        run: "text 1231441",
      },
      //Escribir Daniela Gomez
      {
        content: "Add customer",
        trigger: "input.o_input.ui-autocomplete-input#o_field_input_771",
        run: "text Daniela Gomez",
      },
      // Validar que el proveedor exite
      {
        content: "Valid customer",
        trigger: '.ui-menu-item-wrapper:contains("Daniela Gomez")',
      },
      {
        // Validar retenciones
        content: "Valid retenciones",
        trigger:
          "div.custom-control.custom-checkbox.o_field_boolean.o_field_widget",
      },
      //Seleccionar link para añadir productos
      {
        content: "Click in add product",
        trigger: "a:contains('Agregar línea')",
      },
      //Añadir producto, en este caso Bombillos
      {
        content: "Add producto",
        trigger: ".o_data_cell.o_field_cell.o_list_many2one div div input",
        run: "text Bombillos",
      },
      //Validar que el producto existe
      {
        content: "Valid product",
        trigger: '.ui-menu-item-wrapper:contains("Bombillos")',
      },
      {
        content: "Change unit price",
        trigger: 'input[name="price_unit"]',
        run: "text 5",
      },
      //validar el valor
      {
        content: "Valid the new value",
        trigger: 'input[name="price_unit"]',
        run: function (actions) {
          var keydownEvent = jQuery.Event("keydown");
          keydownEvent.which = 13;
          this.$anchor.trigger(keydownEvent);
        },
      },
      //Save form
      {
        content: "Save invoice",
        trigger: ".o_form_button_save",
      },
      //Confirm form
      {
        content: "Confirm invoice",
        trigger: "span:contains('Confirmar')",
      },
    ]
  );
});
