# -*- coding: utf-8 -*-
from . import wizard
from openerp import api, SUPERUSER_ID


def _l10n_it_fatturapa_out_oss_post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    oss_taxes = env["account.tax"].search([("oss_country_id", "!=", False)])
    for oss_tax in oss_taxes:
        oss_tax.write({
            "kind_id": env.ref("l10n_it_account_tax_kind.n3_2").id,
            "law_reference": "Non imponibili - Cessioni Intracomunitarie",
        })
