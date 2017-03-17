# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Bool
from trytond.rpc import RPC
from trytond.transaction import Transaction

__all__ = ['Sale', 'SaleLine']


class Sale:
    __name__ = 'sale.sale'
    __metaclass__ = PoolMeta

    milestone_group_type = fields.Many2One(
        'account.invoice.milestone.group.type', 'Milestone Group Type (old)',
        readonly=True)
    milestone_group = fields.Many2One('account.invoice.milestone.group',
        'Milestone Group (old)', select=True, domain=[
            ('company', '=', Eval('company', -1)),
            ('currency', '=', Eval('currency', -1)),
            ('party', '=', Eval('party', -1)),
            ],
        states={
            'readonly': ((Eval('invoice_method') == 'manual') |
                ~Bool(Eval('party', 0)) |
                ~Eval('state').in_(['draft', 'quotation'])),
            },
        depends=['company', 'currency', 'party', 'invoice_method',
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

    @fields.depends('invoice_method')
    def on_change_invoice_method(self):
        if self.invoice_method == 'manual':
            self.milestone_group_type = None
            self.milestone_group = None

    @classmethod
    def search_invoices(cls, name, clause):
        """
        The invoices field searcher returns all invoices (also
        "advancement invoices") because all of them are invoices of this sale.
        In sale they are related in two different fields to make easy identify
        the invoice type.
        """
        domain = super(Sale, cls).search_invoices(name, clause)
        return [['OR',
            domain,
            [
                ('milestone_group.milestones.invoice_method', '=', 'amount'),
                ('milestone_group.milestones.invoice.id',)
                + tuple(clause[1:]),
                ]
            ]]

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
        if (invoice_state == 'none' and self.milestone_group
                and self.milestone_group.state != 'cancel'):
            invoice_state = 'waiting'
        return invoice_state

    @classmethod
    def create_milestones(cls, sales):
        pool = Pool()
        Milestone = pool.get('account.invoice.milestone')

        milestones_to_confirm = []
        sales_by_milestone_group = {}
        for sale in sales:
            group = None
            if sale.milestone_group:
                group = sale.milestone_group
            elif sale.milestone_group_type:
                group = sale.milestone_group_type.compute_milestone_group(sale)
            if group:
                milestones_to_confirm += [m for m in group.milestones
                    if m.state == 'draft']
                sales_by_milestone_group.setdefault(group, []).append(sale)

        Milestone.confirm(milestones_to_confirm)
        for group, group_sales in sales_by_milestone_group.iteritems():
            group.check_trigger_condition(group_sales)

    @classmethod
    def process(cls, sales):
        # We must create milestone group before processing otherwise invoices
        # are duplicated
        with Transaction().set_context(from_process_sales=True):
            cls.create_milestones(sales)
            super(Sale, cls).process(sales)

            sales_by_milestone_group = {}
            for sale in sales:
                if (sale.milestone_group and
                        sale.state in ('processing', 'done')):
                    sales_by_milestone_group.setdefault(sale.milestone_group,
                        []).append(sale)
            for group, group_sales in sales_by_milestone_group.iteritems():
                group.check_trigger_condition(group_sales)

    def create_invoice(self):
        if self.milestone_group:
            return
        return super(Sale, self).create_invoice()

    @classmethod
    def copy(cls, sales, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('remainder_milestones', [])
        default.setdefault('milestone_group', None)
        return super(Sale, cls).copy(sales, default=default)

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
    __metaclass__ = PoolMeta

    milestones = fields.Many2Many(
        'account.invoice.milestone-to_invoice-sale.line',
        'sale_line', 'milestone', 'Milestones (old)', readonly=True,
        states={
            'invisible': Eval('type', 'line') != 'line',
            }, depends=['type'])
    invoice_method = fields.Function(fields.Selection('get_invoice_methods',
            'Invoice Method'),
        'get_invoice_method')
    quantity_to_invoice = fields.Function(fields.Float('Quantity to invoice',
            digits=(16, Eval('unit_digits', 2)),
            states={
                'invisible': Eval('type') != 'line',
                },
            depends=['type', 'unit_digits']),
        'get_quantity_to_invoice')

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        cls.__rpc__.update({
                'get_invoice_methods': RPC(),
                })

    @staticmethod
    def get_invoice_methods():
        Sale = Pool().get('sale.sale')
        return Sale.invoice_method.selection

    def get_invoice_method(self, name):
        if self.sale:
            return self.sale.invoice_method

    def get_quantity_to_invoice(self, name):
        pool = Pool()
        Uom = pool.get('product.uom')

        if self.type != 'line':
            return 0.0

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

        skip_ids = set(l.id for i in self.sale.invoices_recreated
            for l in i.lines)
        for invoice_line in self.invoice_lines:
            if invoice_line.type != 'line':
                continue
            if invoice_line.id not in skip_ids:
                quantity -= Uom.compute_qty(invoice_line.unit,
                    invoice_line.quantity, self.unit)

        if self.unit:
            quantity = self.unit.round(quantity)
        return quantity

    @property
    def quantity_to_ship(self):
        pool = Pool()
        Uom = pool.get('product.uom')

        if self.sale.shipment_method == 'order':
            quantity = abs(self.quantity)
        else:
            quantity = 0.0
            for invoice_line in self.invoice_lines:
                if invoice_line.invoice.state == 'paid':
                    quantity += Uom.compute_qty(invoice_line.unit,
                        invoice_line.quantity, self.unit)

        ignored_ids = set(x.id for x in self.moves_ignored)
        for move in self.moves:
            if move.state == 'done' or move.id in ignored_ids:
                quantity -= Uom.compute_qty(move.uom, move.quantity,
                    self.unit)
        return self.unit.round(quantity)

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

    @property
    def ignored_moves_amount(self):
        pool = Pool()
        Currency = pool.get('currency.currency')

        ignored_amount = Decimal('0')
        for ignored_move in self.moves_ignored:
            sign = (Decimal('1')
                if ignored_move.to_location.type == 'customer'
                else Decimal('-1'))
            ignored_amount += (Decimal(str(ignored_move.quantity))
                * ignored_move.unit_price * sign)
            if ignored_move.currency:
                ignored_amount = Currency.compute(ignored_move.currency,
                    ignored_amount, self.sale.currency, round=False)
            elif self.sale.company:
                ignored_amount = Currency.compute(self.sale.company.currency,
                    ignored_amount, self.sale.currency, round=False)
        return ignored_amount

    def get_invoice_line(self):
        res = super(SaleLine, self).get_invoice_line()

        line_description = (
            Transaction().context.get('milestone_invoice_line_description'))
        if line_description:
            for l in res:
                l.description = line_description
        return res

    @classmethod
    def copy(cls, lines, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('milestones', [])
        return super(SaleLine, cls).copy(lines, default=default)
