# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction

__all__ = ['Sale', 'SaleLine']
__metaclass__ = PoolMeta


class Sale:
    __name__ = 'sale.sale'

    milestone_group_type = fields.Many2One(
        'account.invoice.milestone.group.type', 'Milestone Group Type',
        states={
            # 'invisible': Eval('invoice_method') != 'milestone',
            'readonly': ~Eval('state').in_(['draft', 'quotation']),
            },
        depends=['state'])
    milestone_group = fields.Many2One('account.invoice.milestone.group',
        'Milestone Group', select=True, domain=[
            ('company', '=', Eval('company', -1)),
            ('currency', '=', Eval('currency', -1)),
            ('party', '=', Eval('party', -1)),
            ],
        states={
            # 'invisible': Eval('invoice_method') != 'milestone',
            'required': ((~Eval('state', '').in_(['draft', 'cancel']))
                # & (Eval('invoice_method') == 'milestone')
                & ~Bool(Eval('milestone_group_type', 0))),
            'readonly': (~Bool(Eval('party', 0)) |
                Bool(Eval('milestone_group_type')) |
                ~Eval('state').in_(['draft', 'quotation'])),
            },
        depends=['company', 'currency', 'party',
            'milestone_group_type', 'state'])
    remainder_milestones = fields.Many2Many(
        'account.invoice.milestone-remainder-sale.sale', 'sale', 'milestone',
        'Remainder Milestones', domain=[
            ('group', '=', Eval('milestone_group', -1)),
            ], readonly=True,
        states={
            'invisible': ~Bool(Eval('milestone_group')),
            }, depends=['milestone_group'])

    advancement_invoices = fields.Function(fields.One2Many('account.invoice',
            None, 'Advancement Invoices',
            states={
                'invisible': ~Bool(Eval('milestone_group')),
                }, depends=['milestone_group']),
        'get_advancement_invoices')

    def get_advancement_invoices(self, name):
        if not self.milestone_group:
            return
        invoices = set()
        for milestone in self.milestone_group.milestones:
            if milestone.invoice_method == 'amount' and milestone.invoice:
                invoices.add(milestone.invoice.id)
        return list(invoices)

    def get_invoice_state(self):
        '''
        Return the invoice state for the sale.
        '''
        invoice_state = super(Sale, self).get_invoice_state()
        if invoice_state == 'none' and self.milestone_group:
            invoice_state = 'waiting'
        return invoice_state

    @classmethod
    def confirm(cls, sales):
        pool = Pool()
        Milestone = pool.get('account.invoice.milestone')

        milestones_to_confirm = []
        sales_by_milestone_group = {}
        for sale in sales:
            group = None
            if sale.milestone_group_type:
                group = sale.milestone_group_type.compute_milestone_group(sale)
            elif sale.milestone_group:
                group = sale.milestone_group
            if group:
                milestones_to_confirm += [m for m in group.milestones
                    if m.kind == 'system' and m.state == 'draft']
                sales_by_milestone_group.setdefault(group, []).append(sale)

        super(Sale, cls).confirm(sales)

        Milestone.confirm(milestones_to_confirm)
        for group, group_sales in sales_by_milestone_group.iteritems():
            group.check_trigger_condition(group_sales)

    @classmethod
    def process(cls, sales):
        super(Sale, cls).process(sales)

        sales_by_milestone_group = {}
        for sale in sales:
            if sale.milestone_group and sale.state in ('processing', 'done'):
                sales_by_milestone_group.setdefault(sale.milestone_group,
                    []).append(sale)
        for group, group_sales in sales_by_milestone_group.iteritems():
            group.check_trigger_condition(group_sales)

    def create_invoice(self, invoice_type):
        if self.milestone_group:
            return
        return super(Sale, self).create_invoice(invoice_type)

    @classmethod
    def write(cls, *args):
        actions = iter(args)
        args = []
        for records, values in zip(actions, actions):
            if 'milestone_group' not in values:
                args.extend((records, values))
                continue

            records_wo_remainder_milestones = [r for r in records
                if not r.remainder_milestones]
            for record in records:
                if record in records_wo_remainder_milestones:
                    continue
                new_values = values.copy()
                new_values['remainder_milestones'] = [
                    ('remove', [m.id for m in record.remainder_milestones]),
                    ]
                args.extend(([record], new_values))
            if records_wo_remainder_milestones:
                args.extend((records_wo_remainder_milestones, values))
        super(Sale, cls).write(*args)


class SaleLine:
    __name__ = 'sale.line'
    milestone = fields.Many2One('account.invoice.milestone', 'Milestone',
        readonly=True)
    quantity_to_invoice = fields.Function(fields.Float('Quantity to invoice',
            digits=(16, Eval('unit_digits', 2)),
            states={
                'invisible': Eval('type') != 'line',
                },
            depends=['type', 'unit_digits']),
        'get_quantity_to_invoice')

    def get_quantity_to_invoice(self, name):
        pool = Pool()
        Uom = pool.get('product.uom')

        if (self.sale.invoice_method == 'order'
                or not self.product
                or self.product.type == 'service'):
            quantity = abs(self.quantity)
        else:
            quantity = 0.0
            for move in self.moves:
                if move.state == 'done':
                    quantity += Uom.compute_qty(move.uom, move.quantity,
                        self.unit)

        invoice_type = ('out_invoice' if self.quantity >= 0
            else 'out_credit_note')
        skip_ids = set(l.id for i in self.sale.invoices_recreated
            for l in i.lines)
        for invoice_line in self.invoice_lines:
            if invoice_line.type != 'line':
                continue
            if invoice_line.id not in skip_ids:
                sign = (1.0 if invoice_type == invoice_line.invoice_type
                    else -1.0)
                quantity -= Uom.compute_qty(invoice_line.unit,
                    sign * invoice_line.quantity, self.unit)

        rounding = self.unit.rounding if self.unit else 0.01
        return Uom.round(quantity, rounding)

    @property
    def shipped_amount(self):
        'The quantity from linked done moves in line unit'
        pool = Pool()
        Uom = pool.get('product.uom')
        quantity = 0.0
        for move in self.moves:
            if move.state == 'done':
                sign = 1.0 if move.to_location.type == 'customer' else -1.0
                quantity += Uom.compute_qty(move.uom, sign * move.quantity,
                    self.unit)
        return self.sale.currency.round(Decimal(str(quantity))
            * self.unit_price)

    def get_invoice_line(self, invoice_type):
        res = super(SaleLine, self).get_invoice_line(invoice_type)

        line_description = (
            Transaction().context.get('milestone_invoice_line_description'))
        if line_description:
            for l in res:
                l.description = line_description
        return res

    @classmethod
    def write(cls, *args):
        pool = Pool()
        Milestone = pool.get('account.invoice.milestone')

        actions = iter(args)
        sale_lines_to_check = []
        for records, values in zip(actions, actions):
            for action, moves_ignored in values.get('moves_ignored', []):
                if action == 'add' and moves_ignored:
                    sale_lines_to_check += [r.id for r in records
                        if r.milestone]
        super(SaleLine, cls).write(*args)

        if sale_lines_to_check:
            milestones_to_cancel = set()
            for sale_line in cls.browse(list(set(sale_lines_to_check))):
                if sale_line.quantity_to_invoice <= 0:
                    milestones_to_cancel.add(sale_line.milestone)
            if milestones_to_cancel:
                Milestone.cancel(list(milestones_to_cancel))
