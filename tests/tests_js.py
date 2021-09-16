import odoo.tests


@odoo.tests.common.at_install(False)
@odoo.tests.common.post_install(True)
class TestUi(odoo.tests.HttpCase):
    def test_01_accouting_retenciones(self):
        # Este fragmento aun esta en prueba (variable code luego de link)
        # code = """
        #     setTimeout(function () {
        #         $(".account_accountant").click();
        #         setTimeout(function () {console.log('ok');}, 3000);
        #     }, 1000);
        # """
        link = '/web'
            self.phantom_js(link, "odoo.__DEBUG__.services['web_tour.tour'].run('account_retenciones')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.account_retenciones.ready",  login="admin")

