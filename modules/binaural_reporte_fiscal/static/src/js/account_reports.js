odoo.define('binaural_reporte_fiscal.accountReportsWidget_inherit', function (require) {
'use strict';

var core = require('web.core');
var accountReportsWidget = require('account_reports.account_report').GeneratePriceList;

var accountReportsWidgetInherit = accountReportsWidget.include({
    hasControlPanel: true,
        custom_events: _.extend({}, accountReportsWidget.prototype.custom_events, {
             'click .o_action': '_onClickAction',
        }),
});

console.log('testinggggggggggggggg')
core.action_registry.add('account_report', accountReportsWidget);

return accountReportsWidgetInherit;

});