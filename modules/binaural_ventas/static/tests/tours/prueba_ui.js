odoo.define("binaural_ventas.tour", function (require) {
  "use strict";

  var tour = require("web_tour.tour");

  var options = {
    test: true,
    url: "/web",
  };

  var tour_name = "test_ventas";
  tour.register(tour_name, options, [
    tour.stepUtils.showAppsMenuItem(),
    {
      content: "select module",
      trigger: "#result_app_1",
    },
    //Seleccionar submenu Orders
    {
      content: "Ir a ordenes",
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
      trigger: ".option:contains('Clientes')",
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
  ]);
});
