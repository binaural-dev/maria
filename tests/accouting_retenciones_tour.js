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

  for (var i = 0; i < 10; i++) {
    tour.register(
      "account_retenciones",
      {
        test: true,
        url: "/web",
      },
      [
        tour.stepUtils.showAppsMenuItem(),
        //Entrar a modulo de Contabilidad
        {
          content: "open accounting",
          trigger:
            '.o_app[data-menu-xmlid="account_accountant.menu_accounting"]',
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
          content: "Create new Invoice",
          trigger: ".o_list_button_add",
        },
        ///Escribir nombre de factura
        {
          content: "Writte Invoices Name ",
          trigger: "input#o_field_input_905",
          run: "text pruebaFactura" + i,
        },
        ///Escribir numero de control
        {
          content: "Writte Control Number ",
          trigger:
            "input.o_field_char.o_field_widget.o_input.o_required_modifier",
          run: "text 1231441",
        },
        //Escribir EmpresaPrueba
        {
          content: "Add customer",
          trigger: "input.o_input.ui-autocomplete-input#o_field_input_2713",
          run: "text EmpresaPrueba",
        },
        // Validar que el proveedor exite
        {
          content: "Valid customer",
          trigger: '.ui-menu-item-wrapper:contains("EmpresaPrueba")',
        },
        {
          // Validar retenciones
          content: "Valid retenciones",
          trigger: "input#o_field_input_1092",
        },
        //Seleccionar link para añadir productos
        {
          content: "Click in add product",
          trigger: "a:contains('Agregar línea')",
        },
        //Seleccionar input
        {
          content: "Select input",
          trigger:
            'div[name="order_line"] .o_list_view .o_selected_row .o_list_many2one:first',
        },
        //Añadir producto, en este caso Bombillos
        {
          content: "Add producto",
          trigger:
            'div[name="order_line"] .o_list_view .o_selected_row .o_list_many2one:first',
          run: "text Bombillos",
        },
        //Validar que el producto existe
        {
          content: "Valid product",
          trigger: '.ui-menu-item-wrapper:contains("Bombillos")',
        },
        //Seleccionar input para cambiar cantidad
        {
          content: "Select item quantity",
          trigger:
            'div[name="order_line"] .o_list_view tbody tr.o_data_row .o_list_number input[name="product_uom_qty"]',
        },
        //seleccionar input precio unitario
        {
          content: "Select unit price ",
          trigger:
            'div[name="order_line"] .o_list_view tbody tr.o_data_row .o_list_number input[name="price_unit"]',
        },
        // cambiar precio unitario
        {
          content: "Change unit price",
          trigger:
            'div[name="order_line"] .o_list_view tbody tr.o_data_row .o_list_number input[name="price_unit"]',
          run: "text 5",
        },
        //validar el valor
        {
          content: "Valid the new value",
          trigger:
            'div[name="order_line"] .o_list_view tbody tr.o_data_row .o_list_number input[name="price_unit"]',
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
  }
});
