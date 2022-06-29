# -*- coding: utf-8 -*-
# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import models
from openerp.addons.l10n_it_account.tools.account_tools import encode_for_export
from openerp.tools.float_utils import float_round
from openerp.addons.l10n_it_fatturapa.bindings.fatturapa import (
    AltriDatiGestionaliType,
)


class WizardExportFatturapa(models.TransientModel):
    _inherit = "wizard.export.fatturapa"

    def setDettaglioLinea(self, line_no, line, body, price_precision, uom_precision):
        DettaglioLinea = super(WizardExportFatturapa, self).setDettaglioLinea(
            line_no, line, body, price_precision, uom_precision)

        invoice_line_tax = line.invoice_line_tax_id
        if invoice_line_tax.oss_country_id and invoice_line_tax.kind_id:
            dati_gestionali = AltriDatiGestionaliType(
                TipoDato="OSS",
                RiferimentoTesto=encode_for_export(
                    '%.2f' % float_round(invoice_line_tax.amount, 2), 60),
            )
            DettaglioLinea.AltriDatiGestionali.append(dati_gestionali)
            AliquotaIVA = '0.00'
            DettaglioLinea.AliquotaIVA = AliquotaIVA
            DettaglioLinea.Natura = invoice_line_tax.kind_id.code
        return DettaglioLinea

    def setDatiRiepilogo(self, invoice, body):
        res = super(WizardExportFatturapa, self).setDatiRiepilogo(invoice, body)
        obj_tax = self.env['account.tax']
        for tax_line in invoice.tax_line:
            if tax_line.tax_code_id:
                tax_id = tax_line.tax_code_id.get_tax_by_tax_code()
                tax = obj_tax.browse(tax_id)
                if any(
                    y.oss_country_id and y.kind_id for y in tax
                ):
                    body.DatiBeniServizi.DatiRiepilogo[0].Imposta = '0.00'
                    body.DatiBeniServizi.DatiRiepilogo[0].AliquotaIVA = '0.00'
                    body.DatiBeniServizi.DatiRiepilogo[0].Natura = \
                        tax.kind_id.code
                    body.DatiBeniServizi.DatiRiepilogo[0].RiferimentoNormativo = \
                        encode_for_export(
                            tax.law_reference, 100)
        return res
