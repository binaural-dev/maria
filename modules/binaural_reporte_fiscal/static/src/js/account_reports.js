odoo.define('binaural_reporte_fiscal.accountReportsWidgetInherit', function (require) {
'use strict';

var core = require('web.core');
var accountReportsWidgetinh = require('account_reports.account_report');
var QWeb = core.qweb;
var _t = core._t;

var accountReportsWidgetInherit = accountReportsWidgetinh.extend({
    init: function(parent, action) {
        console.log(parent);
        return this._super.apply(this, arguments);
    },

});

core.action_registry.add('account_report', accountReportsWidgetInherit);

return accountReportsWidgetInherit;

});