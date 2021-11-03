odoo.define("binaural_ventas.tour", function (require) {
  "use strict";

  var tour = require("web_tour.tour");

  var options = {
    test: true,
    url: "/web",
  };

  var tour_name = "test_facturacion";
  tour.register(tour_name, options, [
    tour.stepUtils.showAppsMenuItem(),
    {
      content: "select module",
      trigger: ".o_app[data-menu-xmlid='account_accountant.menu_accounting']",
    },
    //Seleccionar submenu Clientes
    {
      content: "Ir a Clientes",
      trigger: 'a:contains("Clientes")',
    },
    //Seleccionar opcion Facturas
    {
      content: "Ir a Facturas",
      trigger: 'span:contains("Facturas")',
    },
    // Seleccionar boton crear factura
    {
      content: "Crear una nueva Factura",
      trigger: ".o_list_button_add",
    },
    //Selecciono un contacto
    {
      content: "Selecciono contacto",
      trigger:
        "div.o_field_widget.o_field_many2one[name='partner_id'] div input",
      run: "text Daniela",
    },
    {
      content: "Validar contacto",
      trigger: '.ui-menu-item a:contains("Daniela")',
    },
    // //Seleccionar un contacto (cliente o proveedor)
    // {
    //   content: "Click en input ",
    //   trigger: 'select.o_input.o_field_widget[name="filter_partner"]',
    // },
    {
      content: "Añadir linea a factura",
      trigger:
        "div[name=invoice_line_ids] .o_field_x2many_list_row_add a:not([data-context])",
    },
    {
      content: "Seleccionar un producto",
      trigger: "div[name=invoice_line_ids] div[name=product_id] div input",
      run: "text Escritorio grande",
    },
    {
      content: "Presionar boton guardar",
      trigger: ".o_form_button_save ",
    },
  ]);
});
