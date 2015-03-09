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

    def check_method(self):
        super(Sale, self).check_method()
        if (self.milestone_group and self.milestone_group.invoice_shipments
                and self.invoice_method == 'order'):
            self.raise_user_error('invalid_method', (self.rec_name,))

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
        pool = Pool()
        Invoice = pool.get('account.invoice')
        Milestone = pool.get('account.invoice.milestone')

        if self.milestone_group and not self.milestone_group.invoice_shipments:
            return

        invoice = super(Sale, self).create_invoice(invoice_type)

        if (invoice and self.milestone_group and
                self.milestone_group.invoice_shipments):
            milestone = self._get_invoice_milestone(invoice)
            if milestone:
                milestone.save()

                if invoice_type == 'out_invoice':
                    invoice_line = milestone.get_compensation_line(
                        invoice.untaxed_amount)
                    if invoice_line:
                        invoice.lines = invoice.lines + (invoice_line, )
                        invoice.save()
                        Invoice.update_taxes([invoice])

                Milestone.confirm([milestone])
                Milestone.proceed([milestone])
        return invoice

    def _get_invoice_milestone(self, invoice):
        'Returns a milestone for the current sale and invoice'
        pool = Pool()
        Date = pool.get('ir.date')
        Milestone = pool.get('account.invoice.milestone')
        assert self.milestone_group

        stock_moves = []
        for line in invoice.lines:
            stock_moves.extend(line.stock_moves)
        if not stock_moves:
            return

        milestone = Milestone()
        milestone.group = self.milestone_group
        # milestone.description =
        milestone.kind = 'manual'
        milestone.invoice_method = 'shipped_goods'
        milestone.moves_to_invoice = stock_moves
        milestone.planned_invoice_date = Date.today()
        milestone.invoice = invoice
        return milestone

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
        context = Transaction().context

        old_line_moves = None
        if (self.sale.milestone_group
                and self.sale.milestone_group.invoice_shipments
                and not context.get('invoicing_from_milestone')):
            # Don't invoice moves that are in some milestone
            old_line_moves = self.moves
            self.moves = [m for m in self.moves if not m.milestone]

        res = super(SaleLine, self).get_invoice_line(invoice_type)
        if context.get('milestone_invoice_line_description'):
            for l in res:
                l.description = context['milestone_invoice_line_description']

        if old_line_moves is not None:
            self.moves = old_line_moves
        return res

    def get_move(self, shipment_type):
        move = super(SaleLine, self).get_move(shipment_type)
        if (move and self.sale.milestone_group
                and not self.sale.milestone_group.invoice_shipments):
            if self.moves:
                milestones = list(set(m.milestone for m in self.moves
                        if m.milestone))
                if (len(milestones) == 1
                        and milestones[0].state in ('draft', 'confirmed')):
                    move.milestone = milestones[0]
        return move

    @classmethod
    def write(cls, *args):
        pool = Pool()
        Milestone = pool.get('account.invoice.milestone')

        actions = iter(args)
        sale_lines_to_check = []
        for records, values in zip(actions, actions):
            for action, moves_ignored in values.get('moves_ignored', []):
                if action == 'add' and moves_ignored:
                    sale_lines_to_check += [r.id for r in records]
        super(SaleLine, cls).write(*args)

        if sale_lines_to_check:
            milestones_done = []
            milestones_to_cancel = []
            for sale_line in cls.browse(list(set(sale_lines_to_check))):
                for move in sale_line.moves_ignored:
                    if (not move.milestone
                            or move.milestone.id in milestones_done):
                        continue
                    milestones_done.append(move.milestone.id)
                    if all(m in m.origin.moves_ignored
                            for m in move.milestone.moves_to_invoice):
                        # all moves_to_invoice are ignored
                        milestones_to_cancel.append(move.milestone)
            if milestones_to_cancel:
                Milestone.cancel(milestones_to_cancel)
