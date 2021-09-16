// Ventas, compras, facturación -> probar presupuesto con diferentes tasas

odoo.define("binaural_ventas.tour", function (require) {
  "use strict";
  var core = require("web.core");
  var tour = require("web_tour.tour");
  var _t = core._t;
  // var tasa = 4000000.0;
  // var price_unit = [0.1, 100, 50, 1450, 10000, 13523, 98, 0.3, 40, 2222222];
  // var quantity = 10;

  tour.register(
    "test_ventas_presupuesto",
    {
      test: true,
      url: "/web",
    },
    [
      tour.stepUtils.showAppsMenuItem(),
      //Entrar a modulo de Ventas
      {
        content: "open sales",
        trigger: '.o_app[data-menu-xmlid="sale.sale_menu_root"]',
      },
      //Seleccionar submenu Orders
      {
        content: "Go to Orders",
        trigger: 'a:contains("Pedidos")',
      },
      //Seleccionar opcion Quotations
      {
        content: "Go to Quotations",
        trigger: 'span:contains("Presupuestos")',
      },
      // Seleccionar boton crear cotización
      {
        content: "Create new Quotatins",
        trigger: ".o_list_button_add",
      },
      ////Seleccionar un tipo de contacto: Customers, Providers or Contacts
      {
        content: "Click in filter ",
        trigger:
          'select.o_input.o_field_widget.o_required_modifier[name="filter_partner"]',
      },
      //Para este caso se selecciono Customer
      {
        content: "Select a option",
        trigger: ".option:contains('Customer')",
      },
      //Buscar al customer Daniela Gomez
      {
        content: "Add customer",
        trigger: "input.o_input.ui-autocomplete-input#o_field_input_1103",
        run: "text Daniela Gomez",
      },
      // Validar que el cliente exite
      {
        content: "Valid customer",
        trigger: '.ui-menu-item-wrapper:contains("Daniela Gomez")',
      },
    ]
  );
});
