odoo.define('binaural_sitio_web.website_sale_bin', function (require) {
    'use strict';

    var core = require('web.core');
    var config = require('web.config');
    var publicWidget = require('web.public.widget');
    var VariantMixin = require('sale.VariantMixin');
    var wSaleUtils = require('website_sale.utils');
    const wUtils = require('website.utils');
    require("web.zoomodoo");


    publicWidget.registry.WebsiteSaleBinauralSitioWeb = publicWidget.Widget.extend(VariantMixin, {
        selector: '.oe_website_sale',
        events: _.extend({}, VariantMixin.events || {}, {

            'change select[name="state_id"]': '_onChangeState',
            'change select[name="city_id"]': '_onChangeCity',
        }),
        /**
         * @constructor
         */
        init: function () {
            this._super.apply(this, arguments);
            this._changestate = _.debounce(this._changestate.bind(this), 500);
            this.isWebsite = true;
        },
        /**
         * @override
         */
        start() {
            const def = this._super(...arguments);
            this.$('select[name="state_id"]').change();
            return def;
        },
       



       
        /**
         * @private
         */
        _changestate: function () {
            
            if (!$("#state_id").val()) {
                return;
            }
            this._rpc({
                route: "/shop/city_infos/" + $("#state_id").val(),
                params: {
                    mode: $("#state_id").attr('mode'),
                },
            }).then(function (data) {
                // populate states and display
                var selectStates = $("select[name='city_id']");
                // dont reload state at first loading (done in qweb)
                if (selectStates.data('init') === 0 || selectStates.find('option').length === 1) {
                    if (data.states.length) {
                        selectStates.html('');
                        _.each(data.states, function (x) {
                            var opt = $('<option>').text(x[1])
                                .attr('value', x[0]).attr('name-bin', x[1])
                                
                            selectStates.append(opt);
                        });
                        selectStates.parent('div').show();
                    } else {
                        selectStates.val('').parent('div').hide();
                    }
                    selectStates.data('init', 0);
                } else {
                    selectStates.data('init', 0);
                }

                // manage fields order / visibility
                /*if (data.fields) {
                    var all_fields = ["street", "zip", "city", "country_name","city_id"]; // "state_code"];
                    _.each(all_fields, function (field) {
                        $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields) >= 0);
                    });
                }*/
            });
        },
        
       
        /**
         * @private
         * @param {Event} ev
         */
        _onChangeState: function (ev) {
            /*if (!this.$('.checkout_autoformat').length) {
                return;
            }*/
            console.log("CAMBIO EL ESTADO LLAMAR A _CHANGE")
            this._changestate();
        },
        /**
         * @private
         * @param {Event} ev
         */
        _onChangeCity: function (ev) {
            /*if (!this.$('.checkout_autoformat').length) {
                return;
            }*/
            console.log($("#city_id_bin option:selected").attr("name-bin"))
            $("#city_odoo").val($("#city_id_bin option:selected").attr("name-bin"))
            
        },
        
        
    });

  
});
