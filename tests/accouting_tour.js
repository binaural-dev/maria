odoo.define('account.tour.tests', function (require) {
    "use strict";

    var core = require('web.core');
    var tour = require('web_tour.tour');
    var _t = core._t;

    tour.register('accouting_test_tour', {
        test: true,
        url: "/web",
    }, [tour.stepUtils.showAppsMenuItem(),
        {
            content: "Go to Accounting",
            trigger: '.o_app[data-menu-xmlid="account_accountant.menu_accounting"]',
            edition: 'enterprise',
        },
        {
            content: "Go to Customers",
            trigger: 'a:contains("Customers")',
        },
        {
            content: "Go to Contingency invoices",
            trigger: 'span:contains("Contingency")',
        },
        {
            content: "Create new Contingency invoices",
            trigger: '.o_list_button_add',
        },
        // Set a Number Control
        {
            content: "Add N° Control",
            trigger: 'input.o_field_char.o_field_widget.o_input.o_required_modifier',
            run: 'text 23',
        },
        {
            content: "Add N° Customer",
            trigger: 'input#o_field_input_1104',
            run: 'text Daniela Gomez',
        },
        {
            content: "Valid Customer",
            trigger: '.ui-menu-item a:contains("Daniela Gomez")',
        },

        // Add First product
        {
            content: "Add items",
            trigger: 'div[name="invoice_line_ids"] .o_field_x2many_list_row_add a:contains("Add a line")',
        },
        {
            content: "Select input",
            trigger: 'div[name="invoice_line_ids"] .o_list_view .o_selected_row .o_list_many2one:first input',
        },
        {
            content: "Type item",
            trigger: 'div[name="invoice_line_ids"] .o_list_view .o_selected_row .o_list_many2one:first input',
            run: "text Large Desk",
        },
        {
            content: "Valid item",
            trigger: '.ui-menu-item-wrapper:contains("Large Desk")',
        },
        // Save account.move
        {
            content: "Save the account move",
            trigger: '.o_form_button_save',
        },
        // Edit account.move
        {
            content: "Edit the account move",
            trigger: '.o_form_button_edit',
        },
        // Edit tax group amount
        {
            content: "Edit tax group amount",
            trigger: '.oe_tax_group_amount_value',
        },
        {
            content: "Modify the input value",
            trigger: '.tax_group_edit_input input',
            run: function (actions) {
                $('.tax_group_edit_input input').val(200);
                $('.tax_group_edit_input input').select();
                var keydownEvent = jQuery.Event('keydown');
                keydownEvent.which = 13;
                this.$anchor.trigger(keydownEvent);
            },
        },
        // Check new value for total (with modified tax_group_amount).
        {
            content: "Valid total amount",
            trigger: 'span[name="amount_total"]:contains("1,499.00")',
        },
        // Modify the quantity of the object
        {
            content: "Select item quantity",
            trigger: 'div[name="invoice_line_ids"] .o_list_view tbody tr.o_data_row .o_list_number[title="1.000"]',
        },
        {
            content: "Change item quantity",
            trigger: 'div[name="invoice_line_ids"] .o_list_view tbody tr.o_data_row .o_list_number[title="1.000"] input',
            run: 'text 2',
        },
        {
            content: "Valid the new value",
            trigger: 'div[name="invoice_line_ids"] .o_list_view tbody tr.o_data_row .o_list_number[title="1.000"] input',
            run: function (actions) {
                var keydownEvent = jQuery.Event('keydown');
                keydownEvent.which = 13;
                this.$anchor.trigger(keydownEvent);
            },
        },
        // Save form
        {
            content: "Save the account move",
            trigger: '.o_form_button_save',
        },
        // Check new tax group value
        {
            content: "Check new value of tax group",
            trigger: '.oe_tax_group_amount_value:contains("389.70")',
        },
    ]);
});
