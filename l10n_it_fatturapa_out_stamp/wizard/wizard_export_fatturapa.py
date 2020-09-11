# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from openerp.osv import osv
from openerp.tools.float_utils import float_round, float_is_zero
from openerp.addons.l10n_it_fatturapa.bindings.fatturapa_v_1_2 import (
    DatiBolloType
)


class WizardExportFatturapa(osv.TransientModel):
    _inherit = "wizard.export.fatturapa"

    def setDatiGeneraliDocumento(self, cr, uid, invoice, body, context=None):
        res = super(WizardExportFatturapa, self).setDatiGeneraliDocumento(
            cr, uid, invoice, body, context=context)
        if invoice.tax_stamp:
            body.DatiGenerali.DatiGeneraliDocumento.DatiBollo = DatiBolloType(
                BolloVirtuale="SI")
            if invoice.company_id.tax_stamp_product_id:
                stamp_price = invoice.company_id.tax_stamp_product_id.list_price
                if not float_is_zero(stamp_price, precision_digits=2):
                    body.DatiGenerali.DatiGeneraliDocumento.DatiBollo.ImportoBollo = \
                        '%.2f' % float_round(stamp_price, 2)
        return res
