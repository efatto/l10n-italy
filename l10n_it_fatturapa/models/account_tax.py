# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Lorenzo Battistini <lorenzo.battistini@agilebg.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _


class AccountTax(orm.Model):
    _inherit = 'account.tax'
    _columns = {
        'non_taxable_nature': fields.selection([
            ('N1', '[N1] excluding ex Art. 15'),
            ('N2', '[N2] not subject'),
            ('N2.1', '[N2.1] not subject ex Artt. from 7 to 7-septies of DPR 633/72'),
            ('N2.2', '[N2.2] not subject – other'),
            ('N3', '[N3] not taxable'),
            ('N3.1', '[N3.1] not taxable – export'),
            ('N3.2', '[N3.2] not taxable – intercommunity cession'),
            ('N3.3', '[N3.3] not taxable – cession to San Marino'),
            ('N3.4', '[N3.4] not taxable – operation similar to export cession'),
            ('N3.5', '[N3.5] not taxable – following declarations of intent'),
            ('N3.6', '[N3.6] not taxable – other operations that do not contribute '
                     'to the formation of the ceiling'),
            ('N4', '[N4] exempt'),
            ('N5', '[N5] margin regime'),
            ('N6', '[N6] reverse charge'),
            ('N6.1', '[N6.1] reverse charge – disposal of scrap and other recycled '
                     'materials'),
            ('N6.2', '[N6.2] reverse charge – supply of gold and pure silver'),
            ('N6.3', '[N6.3] reverse charge – subcontracting in the construction sector'),
            ('N6.4', '[N6.4] reverse charge – sale of buildings'),
            ('N6.5', '[N6.5] reverse charge – transfer of cell phones'),
            ('N6.6', '[N6.6] reverse charge – sale of electronic products'),
            ('N6.7', '[N6.7] reverse charge – construction sector and related sectors'),
            ('N6.8', '[N6.8] reverse charge – energy sector operations'),
            ('N6.9', '[N6.9] reverse charge – other cases'),
            ('N7', '[N7] VAT paid in another EU country')
            ], string="Non taxable nature"),
        'payability': fields.selection([
            ('I', 'Immediate payability'),
            ('D', 'Deferred payability'),
            ('S', 'Split payment'),
            ], string="VAT payability"),
        'law_reference': fields.char(
            'Law reference', size=128),
    }

    def get_tax_by_invoice_tax(self, cr, uid, invoice_tax, context=None):
        tax_ids = []
        if ' - ' in invoice_tax:
            tax_descr = invoice_tax.split(' - ')[0]
            tax_ids = self.search(cr, uid, [
                ('description', '=', tax_descr),
                ], context=context)
        if not tax_ids or len(tax_ids) > 1:
            tax_name = invoice_tax
            tax_ids = self.search(cr, uid, [
                ('name', '=', tax_name),
                ], context=context)
        if not tax_ids:
            raise orm.except_orm(
                _('Error'), _('No tax %s found') % invoice_tax)
        elif len(tax_ids) > 1:
            raise orm.except_orm(
                _('Error'), _('Too many tax %s found') % invoice_tax)
        return tax_ids[0]
