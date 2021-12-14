# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        product_templates = env['product.template'].search([
            ('intrastat_hs_code', '!=', False),
        ])
        for template in product_templates:
            intrastat_code_ids = env['report.intrastat.code'].search([
                ('name', '=', template.intrastat_hs_code)
            ])
            if not intrastat_code_ids:
                _logger.info('Intrastat code not found %s for template %s' % (
                    template.intrastat_hs_code,
                    template.default_code,
                ))
            else:
                template.intrastat_code_id = intrastat_code_id[0]
                _logger.info(
                    'Updated intrastat code from %s to %s for product template %s' % (
                        template.intrastat_hs_code,
                        template.intrastat_code_id.name,
                        template.default_code,
                    ))
