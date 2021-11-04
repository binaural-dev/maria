odoo.define('website_event.registration_form.instance', function (require) {
'use strict';

require('web_editor.ready');
var EventRegistrationForm = require('website_event.website_event');

var $form = $('#registration_form');
if (!$form.length) {
    return null;
}

var instance = new EventRegistrationForm();
return instance.appendTo($form).then(function () {
    return instance;
});
});

//==============================================================================

odoo.define('website_event.website_event', function (require) {

var ajax = require('web.ajax');
var core = require('web.core');
var Widget = require('web.Widget');

var _t = core._t;

// Catch registration form event, because of JS for attendee details
var EventRegistrationForm = Widget.extend({
    start: function () {
        var self = this;
        var res = this._super.apply(this.arguments).then(function () {
            $('#registration_form .a-submit')
                .off('click')
                .removeClass('a-submit')
                .click(function (ev) {
                    self.on_click(ev);
                });
        });
        return res;
    },

    on_click: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var $form = $(ev.currentTarget).closest('form');
        var $button = $(ev.currentTarget).closest('[type="submit"]');
        var post = {};
        $('#registration_form table').siblings('.alert').remove();
        console.log('Prueba3');
        $('#registration_form select').each(function () {
            post[$(this).attr('name')] = $(this).val();
        });
        var tickets_ordered = _.some(_.map(post, function (value, key) { return parseInt(value); }));
        if (!tickets_ordered) {
            $('<div class="alert alert-info"/>')
                .text(_t('Please select at least one ticket.'))
                .insertAfter('#registration_form table');
            return $.Deferred();
        } else {
            $button.attr('disabled', true);
            return ajax.jsonRpc($form.attr('action'), 'call', post).then(function (modal) {
                var $modal = $(modal);
                $modal.modal({backdrop: 'static', keyboard: false});
                $modal.find('.modal-body > div').removeClass('container'); // retrocompatibility - REMOVE ME in master / saas-19
                $modal.appendTo('body').modal();
                $modal.on('click', '.js_goto_event', function () {
                    $modal.modal('hide');
                    $button.prop('disabled', false);
                });
                $modal.on('click', '.clear-item', function (clicked) {
                    console.log('Pasoooo');
                    console.log(clicked.target.getAttribute('name'));
                    let $button_select = clicked.target.getAttribute('name').toString().slice(0, 1);
                    let $value_select = clicked.target.getAttribute('name').toString().slice(1,);
                    $("input[name=" + $value_select.toString().concat('-vat') + "]").val('');
                    $("input[name=" + $value_select.toString().concat('-name') + "]").val('');
                    $("input[name=" + $value_select.toString().concat('-email') + "]").val('');
                    $("input[name=" + $value_select.toString().concat('-phone') + "]").val('');

                });
                $modal.on('click', '.delete-cf', function (clicked) {
                    console.log('Pasoooo');
                    console.log(clicked.target.getAttribute('name'));
                    let $button_select = clicked.target.getAttribute('name').toString().slice(0, 1);
                    let $value_select = clicked.target.getAttribute('name').toString().slice(1,);
                    $("div[name=f" + $value_select.toString().concat('-div') + "]").hide();
                    $("input[name=f" + $value_select.toString().concat('-name') + "]").val('');

                });
                $modal.on('click', '.save-cf', function (clicked) {
                    console.log('Pasoooo');
                    console.log(clicked.target.getAttribute('name'));
                    let $button_select = clicked.target.getAttribute('name').toString().slice(0, 1);
                    let $value_select = clicked.target.getAttribute('name').toString().slice(1,);
                    //$("div[name=f" + $value_select.toString().concat('-div') + "]").hide();
                    $("input[name=a" + $value_select.toString().concat('-operation') + "]").val('save');

                });
                $modal.on('click', '.selection-cf', function (clicked) {
                    console.log('Pasoooo');
                    console.log(clicked.target.getAttribute('name'));
                    let $button_select = clicked.target.getAttribute('name').toString().slice(0, 1);
                    let $value_select = clicked.target.getAttribute('name').toString().slice(1,);
                    //let $f = 'f'.concat($value_select,'-vat');
                    let $r = $value_select.concat('-vat');

                    let $prefix_vat_select = $("input[name=" + 'f'.concat($value_select,'-prefix_vat') + "]").val();
                    let $vat_select = $("input[name=" + 'f'.concat($value_select,'-vat') + "]").val();
                    let $name_select = $("input[name=" + 'f'.concat($value_select,'-name') + "]").val();
                    let $email_select = $("input[name=" + 'f'.concat($value_select,'-email') + "]").val();
                    let $phone_select = $("input[name=" + 'f'.concat($value_select,'-phone') + "]").val();


                    //$vat_register = $("input[name=" + $r + "]").val($vat_select);
                    console.log('button selected');
                    console.log($button_select);
                    console.log('value selected');
                    console.log($value_select);
                    console.log('Buscar para');
                    //console.log($f);
                    console.log('Input prefix_vat');
                    console.log($prefix_vat_select);
                    console.log('Input vat');
                    console.log($vat_select);
                    console.log('Input name');
                    console.log($name_select);
                    console.log('Input email');
                    console.log($email_select);
                    console.log('Input phone');
                    console.log($phone_select);

                    var $iter = 1;
                    var $insert = false;
                    while ($iter < 10) {
                        if ($insert == false) {
                            console.log('NO INSERTADO');
                            if ($("input[name=" + $iter.toString().concat('-vat') + "]").val() == '') {
                                console.log('insertando');
                                $("input[name=" + $iter.toString().concat('-vat') + "]").val($vat_select);
                                $("input[name=" + $iter.toString().concat('-name') + "]").val($name_select);
                                $("input[name=" + $iter.toString().concat('-email') + "]").val($email_select);
                                $("input[name=" + $iter.toString().concat('-phone') + "]").val($phone_select);
                                $insert = true;
                                $iter = 10;
                            }
                        }
                        $iter++;
                    }

                });
                $modal.on('click', '.close', function () {
                    $button.prop('disabled', false);
                });
            });
        }
    },
});

return EventRegistrationForm;
});
