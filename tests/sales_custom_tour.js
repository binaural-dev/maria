// Ventas, compras, facturación -> probar presupuesto con diferentes tasas

odoo.define("sale.tour_sale_signature", function (require) {
  "use strict";
  var core = require("web.core");
  var tour = require("web_tour.tour");
  var _t = core._t;
  var tasa = 4000000.0;
  var price_unit = [0.1, 100, 50, 1450, 10000, 13523, 98, 0.3, 40, 2222222];
  var quantity = 10;

  // This tour relies on data created on the Python test.

  for (var i = 0; i < 10; i++) {
    tour.register(
      "sale_signature",
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
          trigger: 'a:contains("Orders")',
        },
        //Seleccionar opcion Quotations
        {
          content: "Go to Quotations",
          trigger: 'span:contains("Quotations")',
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
        //Seleccionar link para añadir productos
        {
          content: "Click in add product",
          trigger: "a:contains('Add a product')",
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
        // Cambiar cantidad de productos
        {
          content: "Change item quantity",
          trigger:
            'div[name="order_line"] .o_list_view tbody tr.o_data_row .o_list_number input[name="product_uom_qty"]',
          run: "text " + quantity,
        },
        //Validar valor
        {
          content: "Valid the new value",
          trigger:
            'div[name="order_line"] .o_list_view tbody tr.o_data_row .o_list_number input[name="product_uom_qty"]',
          run: function (actions) {
            var keydownEvent = jQuery.Event("keydown");
            keydownEvent.which = 13;
            this.$anchor.trigger(keydownEvent);
          },
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
          run: "text " + price_unit[i],
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
          content: "Save the sale order",
          trigger: ".o_form_button_save",
        },
        // Check price alterno
        {
          content: "Check new value precio alterno",
          trigger: `span[name="foreign_price_unit"]:contains("${
            tasa * price_unit
          }")`,
        },
        // Check subtotal
        {
          content: "Check new value subtotal",
          trigger: `.oe_tax_group_amount_value:contains("${
            quantity * price_unit
          }")`,
        },
        // Check subtotal alterno
        {
          content: "Check new value subtotal alterno",
          trigger: `.oe_tax_group_amount_value:contains("${
            tasa * price_unit * quantity
          }")`,
        },
      ]
    );
  }
});
