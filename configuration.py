# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import Model, ModelSQL, fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all_ = ['AccountConfiguration', 'AccountConfigurationCompany']


class AccountConfiguration:
    __name__ = 'account.configuration'
    __metaclass__ = PoolMeta

    milestone_advancement_product = fields.Function(fields.Many2One(
            'product.product', 'Milestone Advancement Product'),
        'get_company_config', 'set_company_config')
    milestone_sequence = fields.Function(fields.Many2One('ir.sequence',
            'Milestone Sequence',
            domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('code', '=', 'account.invoice.milestone'),
                ]),
        'get_company_config', 'set_company_config')
    milestone_group_sequence = fields.Function(fields.Many2One('ir.sequence',
            'Milestone Group Sequence',
            domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('code', '=', 'account.invoice.milestone.group'),
                ]),
        'get_company_config', 'set_company_config')

    @classmethod
    def get_company_config(cls, configs, names):
        pool = Pool()
        CompanyConfig = pool.get('account.configuration.company')

        company_id = Transaction().context.get('company')
        company_configs = CompanyConfig.search([
                ('company', '=', company_id),
                ])

        res = {}
        for fname in names:
            res[fname] = {
                configs[0].id: None,
                }
            if company_configs:
                if fname == 'milestone_advancement_product':
                    name = 'milestone_adv_product'
                else:
                    name = fname
                val = getattr(company_configs[0], name)
                if isinstance(val, Model):
                    val = val.id
                res[fname][configs[0].id] = val
        return res

    @classmethod
    def set_company_config(cls, configs, name, value):
        pool = Pool()
        CompanyConfig = pool.get('account.configuration.company')

        company_id = Transaction().context.get('company')
        company_configs = CompanyConfig.search([
                ('company', '=', company_id),
                ])
        if company_configs:
            company_config = company_configs[0]
        else:
            company_config = CompanyConfig(company=company_id)
        if name == 'milestone_advancement_product':
            name = 'milestone_adv_product'
        setattr(company_config, name, value)
        company_config.save()


class AccountConfigurationCompany(ModelSQL):
    'Account Configuration per Company'
    __name__ = 'account.configuration.company'

    company = fields.Many2One('company.company', 'Company', required=True,
        ondelete='CASCADE', select=True)
    milestone_adv_product = fields.Many2One('product.product',
        'Milestone Advancement Product')
    milestone_sequence = fields.Many2One('ir.sequence',
        'Milestone Sequence',
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'account.invoice.milestone'),
            ])
    milestone_group_sequence = fields.Many2One('ir.sequence',
        'Milestone Group Sequence',
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'account.invoice.milestone.group'),
            ])
