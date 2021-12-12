# -*- coding: utf-8 -*-
# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade
from openerp import SUPERUSER_ID
from openerp.api import Environment

import logging
_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(cr, version):
    env = Environment(cr, SUPERUSER_ID, {})
    product_templates = env['product.template'].search([
        ('intrastat_hs_code', '!=', False),
    ])
    for template in product_templates:
        intrastat_code_ids = self.env['report.intrastat.code'].search([
            ('name', '=', template.intrastat_hs_code)
        ])
        if not intrastat_code_ids:
            _logger.info('Intrastat code not found %s for template %s' % (
                template.intrastat_hs_code,
                template.default_code,
            ))
        else:
            template.intrastat_code_id = intrastat_code_id[0]
            _logger.info('Updated intrastat code from %s to %s for product template %s' % (
                template.intrastat_hs_code,
                template.intrastat_code_id.name,
                template.default_code,
            ))
