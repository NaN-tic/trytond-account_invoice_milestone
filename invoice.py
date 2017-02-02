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

    @classmethod
    def validate(cls, invoices):
        super(Invoice, cls).validate(invoices)
        for record in invoices:
            record.check_milestone_amount()

    def check_milestone_amount(self):
        if not self.milestone:
            return
        if (self.milestone.invoice_method == 'amount' and
                self.milestone.amount != self.untaxed_amount):
            self.raise_user_error('milestone_amount',
                                (self.rec_name, self.milestone.rec_name))

    @fields.depends('milestone')
    def on_change_with_milestone_group(self):
        if self.milestone:
            return self.milestone.group.id
        return None

    @classmethod
    def search_milestone_group(cls, name, clause):
        return [('milestone.group',) + tuple(clause[1:])]

    @classmethod
    def draft(cls, invoices):
        pool = Pool()
        Milestone = pool.get('account.invoice.milestone')

        milestone_to_proceed = []
        for invoice in invoices:
            if invoice.state == 'cancel' and invoice.milestone:
                cls.raise_user_error('reset_invoice_milestone')
            elif invoice.state == 'posted' and invoice.milestone:
                milestone_to_proceed.append(invoice.milestone)

        res = super(Invoice, cls).draft(invoices)
        if milestone_to_proceed:
            Milestone.proceed(milestone_to_proceed)
        return res

    @classmethod
    def post(cls, invoices):
        pool = Pool()
        Milestone = pool.get('account.invoice.milestone')
        super(Invoice, cls).post(invoices)
        Milestone.succeed([i.milestone for i in invoices if i.milestone])

    @classmethod
    def cancel(cls, invoices):
        pool = Pool()
        Milestone = pool.get('account.invoice.milestone')
        super(Invoice, cls).cancel(invoices)
        Milestone.fail([i.milestone for i in invoices if i.milestone])

    @classmethod
    def copy(cls, invoices, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default['milestone'] = None
        return super(Invoice, cls).copy(invoices, default=default)


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
