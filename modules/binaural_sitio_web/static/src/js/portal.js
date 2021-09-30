odoo.define('binaural_sitio_web.portal', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    const Dialog = require('web.Dialog');
    const { _t, qweb } = require('web.core');
    const ajax = require('web.ajax');

    publicWidget.registry.portalDetailsBinauralSitioWeb = publicWidget.Widget.extend({
        selector: '.o_portal_details',
        events: {
            //'change select[name="country_id"]': '_onCountryChange',
            'change select[name="state_id"]': '_onStateChange',
        },

        /**
         * @override
         */
        start: function () {
            var def = this._super.apply(this, arguments);

            //this.$state = this.$('select[name="state_id"]');
            this.$city = this.$('select[name="city_id"]');
            //this.$stateOptions = this.$state.filter(':enabled').find('option:not(:first)');
            this.$cityOptions = this.$city.filter(':enabled').find('option:not(:first)');
            this._adaptAddressFormBin();

            return def;
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        _adaptAddressFormBin: function () {
            //var $country = this.$('select[name="country_id"]');
            var $state = this.$('select[name="state_id"]');
            //var countryID = ($country.val() || 0);
            var stateID = ($state.val() || 0);
            //this.$stateOptions.detach();
            this.$cityOptions.detach();
            //var $displayedState = this.$stateOptions.filter('[data-country_id=' + countryID + ']');
            var $displayedCity = this.$cityOptions.filter('[data-state_id=' + stateID + ']');
            //var nb = $displayedState.appendTo(this.$state).show().length;
            var nb = $displayedCity.appendTo(this.$city).show().length;
            //this.$state.parent().toggle(nb >= 1);
            this.$city.parent().toggle(nb >= 1);
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        _onStateChange: function () {
            this._adaptAddressFormBin();
        },
    });
});