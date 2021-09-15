odoo.define('binaural_reporte_fiscal.accountReportsWidgetInherit', function (require) {
    'use strict';

    var core = require('web.core');
    var accountReportsWidget = require('account_reports.account_report');
    var QWeb = core.qweb;
    var _t = core._t;

    var accountReportsWidgetInherit = accountReportsWidget.extend({
        reload: function() {
            this._super.apply(this, arguments);
        },
        render: function() {
            this.render_searchview_buttons();
            this._super.apply(this, arguments);
        },
        render_searchview_buttons: function () {
            this._super.apply(this, arguments);
            var self = this;
            var report_options = this.report_options
            this.$searchview_buttons.find('.js_account_report_group_choice_currency_filter').click(function (event) {
                var option_value = $(this).data('filter');
                var option_id = $(this).data('id');
                update_currency_options(option_value, option_id, true, report_options)

                $(this).siblings().each(function (i, e) {
                    const op_value = $(e).data('filter');
                    const op_id = $(e).data('id');
                    update_currency_options(op_value, op_id, false, report_options)
                });
                self.reload();
            });

        },
    });

    function update_currency_options(option_value, option_id, value, report_options) {
        _.filter(report_options[option_value], function (el) {
            if (el.id == option_id) {
                el.selected = value
            }
            return el;
        });
    }

    core.action_registry.add('account_report', accountReportsWidgetInherit);

    return accountReportsWidgetInherit;

});