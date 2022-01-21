from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    is_advance = fields.Boolean(string="Is advance invoice")

    def _get_document_fiscal_type(self, type=None, partner=None,
                                  fiscal_position=None, journal=None):
        dt = super()._get_document_fiscal_type(
            type=type, partner=partner, fiscal_position=fiscal_position,
            journal=journal
        )
        if self.is_advance and self.journal_id:
            doc_id = self.journal_id.advance_fiscal_document_type_id.id
            if doc_id:
                dt = [doc_id]
        return dt
