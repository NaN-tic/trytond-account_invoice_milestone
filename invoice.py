# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, fields, Unique
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval

__all__ = ['Invoice', 'InvoiceLine', 'InvoiceMilestoneRelation']


class Invoice:
    __name__ = 'account.invoice'
    __metaclass__ = PoolMeta

    milestone = fields.One2One('account.invoice-account.invoice.milestone',
        'invoice', 'milestone', 'Milestone (old)', domain=[
            ('company', '=', Eval('company', -1)),
            ('party', '=', Eval('party', -1)),
            ], readonly=True, depends=['company', 'party'])
    milestone_group = fields.Function(fields.Many2One(
            'account.invoice.milestone.group', 'Milestone Group'),
        'on_change_with_milestone_group', searcher='search_milestone_group')

    @classmethod
    def __setup__(cls):
        super(Invoice, cls).__setup__()
        cls._error_messages.update({
                'milestone_amount': ('Amount of invoice "%s" must be '
                    'equal than its milestone "%s" amount'),
                'reset_invoice_milestone': ('You cannot reset to draft '
                    'an invoice generated by a milestone.'),
                })


class InvoiceLine:
    __name__ = 'account.invoice.line'
    __metaclass__ = PoolMeta

    @classmethod
    def _get_origin(cls):
        models = super(InvoiceLine, cls)._get_origin()
        models.append('account.invoice.milestone')
        return models


class InvoiceMilestoneRelation(ModelSQL):
    'Invoice - Milestone'
    __name__ = 'account.invoice-account.invoice.milestone'
    invoice = fields.Many2One('account.invoice', 'Invoice', ondelete='CASCADE',
        required=True, select=True)
    milestone = fields.Many2One('account.invoice.milestone', 'Milestone',
        ondelete='CASCADE', required=True, select=True)

    @classmethod
    def __setup__(cls):
        super(InvoiceMilestoneRelation, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('invoice_unique', Unique(t, t.invoice),
                'The Invoice must be unique.'),
            ('milestone_unique', Unique(t, t.milestone),
                'The Milestone must be unique.'),
            ]
