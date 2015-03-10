# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import If, Eval, Bool
from trytond.transaction import Transaction

__all__ = ['AccountInvoiceMilestoneGroupType', 'AccountInvoiceMilestoneType',
    'AccountInvoiceMilestoneGroup', 'AccountInvoiceMilestone',
    'AccountInvoiceMilestoneSaleLine', 'AccountInvoiceMilestoneRemainderSale']
__metaclass__ = PoolMeta


_ZERO = Decimal('0.0')
_KIND = [
    ('manual', 'Manual'),
    ('system', 'System'),
    ]


def d_round(number, digits):
    quantize = Decimal(10) ** -Decimal(digits)
    return Decimal(number).quantize(quantize)


class AccountInvoiceMilestoneGroupType(ModelSQL, ModelView):
    'Account Invoice Milestone Group Type'
    __name__ = 'account.invoice.milestone.group.type'
    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active')
    description = fields.Char('Description')
    lines = fields.One2Many('account.invoice.milestone.type',
        'milestone_group', 'Lines')

    @classmethod
    def __setup__(cls):
        super(AccountInvoiceMilestoneGroupType, cls).__setup__()
        cls._error_messages.update({
                'last_remainder': ('Last line of milestone group type "%s" '
                    'must be of invoice method remainder.'),
                })

    @staticmethod
    def default_active():
        return True

    @classmethod
    def validate(cls, groups):
        super(AccountInvoiceMilestoneGroupType, cls).validate(groups)
        for group in groups:
            group.check_remainder()

    def check_remainder(self):
        if not self.lines or not self.lines[-1].invoice_method == 'remainder':
            self.raise_user_error('last_remainder', self.rec_name)

    def compute_milestone_group(self, sale):
        """
        Calculate milestones for supplied sale based on this Group Type.
        If the sale already has a milestone group, extend it, otherwise create
        a new one.
        """
        # TODO implement business_days
        # http://pypi.python.org/pypi/BusinessHours/
        group = sale.milestone_group
        if not group:
            group = self._get_milestones_group(sale)
            group.save()
        sale.milestone_group = group
        sale.save()

        for line in self.lines:
            milestone = line.compute_milestone(sale)
            group.milestones = (list(group.milestones)
                if hasattr(group, 'milestones') else []) + [milestone]
        group.save()
        return group

    def _get_milestones_group(self, sale):
        pool = Pool()
        MilestoneGroup = pool.get('account.invoice.milestone.group')

        group = MilestoneGroup()
        group.company = sale.company
        group.currency = sale.currency
        group.party = sale.party
        group.sales = []
        group.sales.append(sale)
        return group


class AccountInvoiceMilestoneType(ModelSQL, ModelView):
    'Account Invoice Milestone Type'
    __name__ = 'account.invoice.milestone.type'
    milestone_group = fields.Many2One('account.invoice.milestone.group.type',
        'Milestone Group Type', required=True, select=True, ondelete='CASCADE')
    sequence = fields.Integer('Sequence',
        help='Use to order lines in ascending order')
    kind = fields.Selection(_KIND, 'Kind', required=True, select=True)
    trigger = fields.Selection([
            ('', ''),
            ('accept', 'On Order Accepted'),
            ('finish', 'On Order Finished'),
            ('percentage', 'On % sent'),
            ], 'Trigger', sort=False,
        states={
            'required': Eval('kind') == 'system',
            'invisible': Eval('kind') != 'system',
            }, depends=['kind'],
        help='Defines when the Milestone will be confirmed and its Planned '
        'Invoice Date calculated.')
    trigger_shipped_amount = fields.Numeric('On Shipped Amount',
        digits=(16, 8), states={
            'required': ((Eval('kind') == 'system')
                & (Eval('trigger') == 'percentage')),
            'invisible': ((Eval('kind') != 'system')
                | (Eval('trigger') != 'percentage')),
            }, depends=['kind', 'trigger'],
        help="The percentage of sent amount over the total amount of "
        "Milestone's Trigger Sale Lines.\n"
        "When the Milestone is computed for a Sale, all this sale lines are "
        "added as Milestone's Trigger Lines. You'll be able to change this.")

    invoice_method = fields.Selection([
            ('fixed', 'Fixed'),
            ('percent_on_total', 'Percentage on Total'),
            ('shipped_goods', 'Shipped Goods'),
            ('remainder', 'Remainder'),
            ], 'Invoice Method', required=True, sort=False)
    amount = fields.Numeric('Amount', digits=(16, Eval('currency_digits', 2)),
        states={
            'required': Eval('invoice_method', '') == 'fixed',
            'invisible': Eval('invoice_method', '') != 'fixed',
            }, depends=['invoice_method', 'currency_digits'])
    currency = fields.Many2One('currency.currency', 'Currency',
        states={
            'required': Eval('invoice_method', '') == 'fixed',
            'invisible': Eval('invoice_method', '') != 'fixed',
            }, depends=['invoice_method'])
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    percentage = fields.Numeric('Percentage', digits=(16, 8),
        states={
            'required': Eval('invoice_method', '') == 'percent_on_total',
            'invisible': Eval('invoice_method', '') != 'percent_on_total',
            }, depends=['invoice_method'])
    divisor = fields.Function(fields.Numeric('Divisor', digits=(16, 8),
        states={
            'required': Eval('invoice_method', '') == 'percent_on_total',
            'invisible': Eval('invoice_method', '') != 'percent_on_total',
            }, depends=['invoice_method']),
        'on_change_with_divisor', setter='set_divisor')

    day = fields.Integer('Day of Month')
    month = fields.Selection([
            (None, ''),
            ('1', 'January'),
            ('2', 'February'),
            ('3', 'March'),
            ('4', 'April'),
            ('5', 'May'),
            ('6', 'June'),
            ('7', 'July'),
            ('8', 'August'),
            ('9', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December'),
            ], 'Month', sort=False)
    weekday = fields.Selection([
            (None, ''),
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday'),
            ], 'Day of Week', sort=False)
    months = fields.Integer('Number of Months', required=True)
    weeks = fields.Integer('Number of Weeks', required=True)
    days = fields.Integer('Number of Days', required=True)

    @classmethod
    def __setup__(cls):
        super(AccountInvoiceMilestoneType, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))
        cls._sql_constraints += [
            ('trigger_shipped_amount',
                ('CHECK(trigger_shipped_amount IS NULL '
                    'OR trigger_shipped_amount BETWEEN 0.0 AND 1.0)'),
                'Trigger Percentage must to be between 0 and 100.0'),
            ('percentage',
                ('CHECK(percentage IS NULL '
                    'OR percentage BETWEEN 0.0 AND 1.0)'),
                'Percentage must to be between 0 and 100.0'),
            ('day', 'CHECK(day BETWEEN 1 AND 31)',
                'Day of month must be between 1 and 31.'),
            ]

    @staticmethod
    def order_sequence(tables):
        table, _ = tables[None]
        return [table.sequence == None, table.sequence]

    @staticmethod
    def default_currency_digits():
        return 2

    @fields.depends('currency')
    def on_change_with_currency_digits(self, name=None):
        if self.currency:
            return self.currency.digits
        return 2

    @staticmethod
    def default_kind():
        return 'manual'

    @staticmethod
    def default_invoice_method():
        return 'remainder'

    @fields.depends('invoice_method')
    def on_change_invoice_method(self):
        res = {}
        if self.invoice_method != 'fixed':
            res['amount'] = _ZERO
            res['currency'] = None
        if self.invoice_method != 'percent_on_total':
            res['percentage'] = _ZERO
            res['divisor'] = _ZERO
        return res

    @fields.depends('divisor')
    def on_change_with_percentage(self):
        return d_round(Decimal('1.0') / self.divisor,
            self.__class__.percentage.digits[1]) if self.divisor else _ZERO

    @fields.depends('percentage')
    def on_change_with_divisor(self, name=None):
        return d_round(Decimal('1.0') / self.percentage,
            self.__class__.divisor.digits[1]) if self.percentage else _ZERO

    @classmethod
    def set_divisor(cls, milestone_types, name, value):
        milestone = milestone_types[0]
        milestone.divisor = value
        percentage = milestone.on_change_with_percentage()
        cls.write(milestone_types, {
                'percentage': percentage,
                })

    @staticmethod
    def default_months():
        return 0

    @staticmethod
    def default_weeks():
        return 0

    @staticmethod
    def default_days():
        return 0

    def compute_milestone(self, sale):
        pool = Pool()
        Currency = pool.get('currency.currency')
        Milestone = pool.get('account.invoice.milestone')

        milestone = Milestone()
        # group.append(milestone)
        # milestone.description = ??
        milestone.kind = self.kind
        if self.kind == 'system':
            if self.trigger == 'accept':
                milestone.trigger_shipped_amount = _ZERO
            elif self.trigger == 'finish':
                milestone.trigger_shipped_amount = Decimal('1.0')
            else:
                milestone.trigger_shipped_amount = self.trigger_shipped_amount
            milestone.trigger_lines = list(sale.lines)

        if self.invoice_method in ('fixed', 'percent_on_total'):
            milestone.invoice_method = 'amount'
            if self.invoice_method == 'fixed':
                milestone.amount = Currency.compute(self.currency,
                    self.amount, sale.currency)
            else:
                milestone.amount = sale.currency.round(
                    sale.untaxed_amount * self.percentage)
        else:
            milestone.invoice_method = self.invoice_method
            if self.invoice_method == 'shipped_goods':
                milestone.sale_lines_to_invoice = [l for l in sale.lines
                    if l.type == 'line']
            elif self.invoice_method == 'remainder':
                milestone.sales_to_invoice = [sale]

        for fname in ('day', 'month', 'weekday', 'months', 'weeks', 'days'):
            setattr(milestone, fname, getattr(self, fname))

        return milestone


_TRIGGER_SALE_STATES = ('confirmed', 'processing', 'done')


class AccountInvoiceMilestoneGroup(ModelSQL, ModelView):
    'Account Invoice Milestone Group'
    __name__ = 'account.invoice.milestone.group'
    _rec_name = 'code'

    code = fields.Char('Code', required=True, readonly=True)
    company = fields.Many2One('company.company', 'Company', required=True,
        select=True, ondelete='CASCADE', states={
            'readonly': Bool(Eval('milestones', [])),
            }, depends=['milestones'])
    currency = fields.Many2One('currency.currency', 'Currency', required=True,
        states={
            'readonly': Bool(Eval('milestones', [])),
            }, depends=['milestones'])
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    party = fields.Many2One('party.party', 'Party', required=True, states={
            'readonly': Bool(Eval('milestones', [])),
            }, depends=['milestones'])
    milestones = fields.One2Many('account.invoice.milestone', 'group',
        'Milestones',
        context={
            'party': Eval('party'),
            },
        states={
            'readonly': ~Bool(Eval('party')),
            },
        depends=['party'])
    state = fields.Function(fields.Selection([
                ('to_assign', 'To assign'),
                ('pending', 'Pending'),
                ('completed', 'Completed'),
                ('paid', 'Paid'),
                ], 'State'),
        'get_state')

    sales = fields.One2Many('sale.sale', 'milestone_group', 'Sales',
        readonly=True,
        domain=[
            ('company', '=', Eval('company', -1)),
            ('currency', '=', Eval('currency', -1)),
            ('party', '=', Eval('party', -1)),
            ],
        depends=['company', 'currency', 'party'])

    total_amount = fields.Function(fields.Numeric('Total Amount',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits'],
            help="The Untaxed Amount of all Group's Sales"),
        'get_amounts')
    merited_amount = fields.Function(fields.Numeric('Merited Amount',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits'],
            help="The Amount of all shipped moves and supplied services (it "
            "calculates the service's sale lines as supplied if the sale is "
            "processing or done)."),
        'get_amounts')
    amount_to_assign = fields.Function(fields.Numeric('Amount to Assign',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits'],
            help="The amount of Sales lines whose movements are not "
            "associated with any Milestone nor their Sales are associated "
            "with any remainder Milestone."),
        'get_amounts')
    assigned_amount = fields.Function(fields.Numeric('Assigned Amount',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits', 'state']),
        'get_amounts')
    amount_to_invoice = fields.Function(fields.Numeric('Amount to Invoice',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_amounts')
    invoiced_amount = fields.Function(fields.Numeric('Invoiced Amount',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_amounts')

    @classmethod
    def __setup__(cls):
        super(AccountInvoiceMilestoneGroup, cls).__setup__()
        cls._buttons.update({
                'check_triggers': {
                    'readonly': Eval('state').in_(['completed', 'paid']),
                    'icon': 'tryton-executable',
                    },
                'close': {
                    'readonly': Eval('state').in_(['completed', 'paid']),
                    'icon': 'tryton-ok',
                    },
                })
        cls._error_messages.update({
                'group_with_pending_milestones': (
                    'The Milestone Group "%s" has some pending milestones.\n'
                    'Please, process or cancel all milestones before close '
                    'the group.'),
                'missing_milestone_sequence': ('There is no milestone sequence'
                    'defined. Please define one in account configuration'),
                'delete_cancel_draft': ('Can not delete milestone group "%s" '
                    'because it\'s milestone "%s" is not in draft or cancel '
                    'state.'),
                })

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_currency():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.id

    @staticmethod
    def default_currency_digits():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.digits
        return 2

    @fields.depends('currency')
    def on_change_with_currency_digits(self, name=None):
        if self.currency:
            return self.currency.digits
        return 2

    def get_state(self, name):
        if not self.sales:
            return 'to_assign'
        if self.amount_to_assign > _ZERO:
            return 'to_assign'

        paid = True
        completed = True
        for milestone in self.milestones:
            if milestone.state in ('failed', 'cancel'):
                continue
            if (milestone.state in ('draft', 'confirmed')
                    and ((milestone.invoice_method == 'shipped_goods'
                            and not milestone.sale_lines_to_invoice)
                        or (milestone.invoice_method == 'remainder'
                            and not milestone.sales_to_invoice))):
                return 'to_assign'
            if not milestone.invoice or milestone.invoice.state != 'paid':
                paid = False
            if (not milestone.invoice
                    or milestone.invoice.state not in ('posted', 'paid')):
                completed = False
        if paid:
            return 'paid'
        if completed and self.total_amount == self.invoiced_amount:
            return 'completed'
        return 'pending'

    @classmethod
    def get_amounts(cls, groups, names):
        result = {}
        for name in names:
            result[name] = {}

        for group in groups:
            group_amounts = group._get_amounts(names)
            for fname in names:
                result[fname][group.id] = group_amounts[fname]
        return result

    def _get_amounts(self, names):
        """
        Any of these amounts take care about advancement amounts.
        total_amount is the sum of sale's untaxed amount
        amount_to_assign is the sale's untaxed amount for sales without
            remainder milestone substracting the amount of stock moves assigned
            to any milestone
        assigned_amount is the difference between total and to assign amount
        invoiced_amount is the sum of milestone's invoices (included draft
            invoices)
        amount_to_invoice is the difference between total and invoiced amount
        """
        pool = Pool()
        Milestone = pool.get('account.invoice.milestone')
        Uom = pool.get('product.uom')
        SaleLine = pool.get('sale.line')

        names_set = set(names)
        sales_in_live_remainders = []
        res = {}.fromkeys(['total_amount', 'merited_amount',
                'amount_to_assign', 'assigned_amount', 'amount_to_invoice',
                'invoiced_amount'],
            _ZERO)
        for sale in self.sales:
            if sale.state not in ('confirmed', 'processing', 'done'):
                continue
            res['total_amount'] += sale.untaxed_amount
            if {'amount_to_assign', 'assigned_amount'} & names_set:
                if sale.remainder_milestones and any(m.state == 'confirmed'
                        for m in sale.remainder_milestones):
                    res['assigned_amount'] += sale.untaxed_amount
                    sales_in_live_remainders.append(sale.id)

            # skip_inv_line_ids = set(l.id for i in sale.invoices_recreated
            #     for l in i.lines)
            for sale_line in sale.lines:
                for ignored_move in sale_line.moves_ignored:
                    sign = (Decimal('1.0')
                        if ignored_move.to_location.type == 'customer'
                        else Decimal('-1.0'))
                    move_qty = Uom.compute_qty(ignored_move.uom,
                        ignored_move.quantity, ignored_move.origin.unit)
                    res['total_amount'] -= (Decimal(str(move_qty))
                                * ignored_move.unit_price * sign)
                if (sale_line.product
                        and sale_line.product.type != 'service'):
                    res['merited_amount'] += sale_line.shipped_amount
                elif sale.state in ('processing', 'done'):
                    res['merited_amount'] += sale_line.amount

        if {'amount_to_assign', 'assigned_amount', 'invoiced_amount',
                'amount_to_invoice'} & names_set:
            for milestone in self.milestones:
                if milestone.state in ('draft', 'failed', 'cancel'):
                    continue

                if milestone.invoice and milestone.invoice.state != 'cancel':
                    for inv_line in milestone.invoice.lines:
                        if (not (isinstance(inv_line.origin, Milestone)
                                    and inv_line.origin == milestone)
                                and not (isinstance(inv_line.origin, SaleLine)
                                    and inv_line.origin.sale in self.sales)):
                            # exclude invoice lines not related to this
                            # milestone group
                            continue

                        sign = (Decimal('1.0')
                            if inv_line.invoice_type == 'out_invoice'
                            else Decimal('-1.0'))
                        res['invoiced_amount'] += inv_line.amount * sign

                        if (milestone.invoice_method == 'remainder'
                                and isinstance(inv_line.origin, SaleLine)
                                and (inv_line.origin.sale.id
                                    not in sales_in_live_remainders)):
                            # not advancement invoice/compensation
                            res['assigned_amount'] += inv_line.amount * sign

                if ({'amount_to_assign', 'assigned_amount'} & names_set
                        and milestone.invoice_method == 'shipped_goods'):
                    for sale_line in milestone.sale_lines_to_invoice:
                        for move in sale_line.moves:
                            if (move.state != 'cancel'
                                    and move not in sale_line.moves_ignored
                                    and move not in sale_line.moves_recreated):
                                sign = (Decimal('1.0')
                                    if move.to_location.type == 'customer'
                                    else Decimal('-1.0'))
                                move_qty = Uom.compute_qty(move.uom,
                                    move.quantity, sale_line.unit)
                                res['assigned_amount'] += (
                                    Decimal(str(move_qty))
                                    * move.unit_price
                                    * sign)

        if 'amount_to_invoice' in names:
            res['amount_to_invoice'] = (res['total_amount']
                - res['invoiced_amount'])
        if 'amount_to_assign' in names:
            res['amount_to_assign'] = (res['total_amount']
                - res['assigned_amount'])

        for fname in res.keys():
            if fname not in names:
                del res[fname]
        return res

    @property
    def invoiced_advancement_amount(self):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')

        advancement_milestone_ids = [m.id for m in self.milestones
            if m.invoice_method == 'amount']
        if not advancement_milestone_ids:
            return _ZERO

        advancement_invoice_lines = InvoiceLine.search([
                ('invoice.state', '!=', 'cancel'),
                ('origin.group', '=', self.id, 'account.invoice.milestone'),
                ])
        if not advancement_invoice_lines:
            return _ZERO
        return sum(il.amount for il in advancement_invoice_lines)

    @classmethod
    @ModelView.button
    def check_triggers(cls, groups):
        for group in groups:
            sales_from = [s for s in group.sales
                if s.state in _TRIGGER_SALE_STATES]
            group.check_trigger_condition(sales_from)

    def check_trigger_condition(self, sales_from):
        pool = Pool()
        Milestone = pool.get('account.invoice.milestone')

        assert all(s.state in _TRIGGER_SALE_STATES for s in sales_from)

        todo = []
        for milestone in self.milestones:
            if (milestone.state != 'confirmed' or milestone.kind == 'manual'
                    or milestone.invoice):
                continue
            if milestone.trigger_shipped_amount == _ZERO:
                # Milestones on order accepted
                if all(l.sale in sales_from for l in milestone.trigger_lines):
                    todo.append(milestone)
            elif milestone.trigger_shipped_amount == Decimal('1.0'):
                # Milestones on order sent
                if all(l.move_done for l in milestone.trigger_lines):
                    todo.append(milestone)
            else:
                # compute as shipped lines the lines without product or with
                # service product only if line's sale is processing or done
                shipped_amount = total_amount = _ZERO
                for sale_line in milestone.trigger_lines:
                    if (sale_line.product
                            and sale_line.product.type != 'service'
                            and sale_line.amount != _ZERO):
                        shipped_amount += sale_line.shipped_amount
                        total_amount += sale_line.amount
                    else:
                        if sale_line.sale.state in ('processing', 'done'):
                            shipped_amount += sale_line.amount
                        total_amount += sale_line.amount
                shipped_percentage = d_round(shipped_amount / total_amount,
                    Milestone.trigger_shipped_amount.digits[1])
                if shipped_percentage >= milestone.trigger_shipped_amount:
                    todo.append(milestone)
        Milestone.do_invoice(todo)

    @classmethod
    @ModelView.button
    def close(cls, groups):
        pool = Pool()
        Milestone = pool.get('account.invoice.milestone')

        to_create = []
        for group in groups:
            if any(m.state not in ('succeeded', 'failed', 'cancel')
                    for m in group.milestones):
                cls.raise_user_error('group_with_pending_milestones',
                    (group.rec_name,))

            milestone = group._get_closing_milestone()
            if milestone:
                to_create.append(milestone._save_values)
        if to_create:
            milestones = Milestone.create(to_create)
            Milestone.confirm(milestones)
            Milestone.do_invoice(milestones)

    def _get_closing_milestone(self):
        'Returns the milestone needed to fill all the amount of the group'
        pool = Pool()
        Date = pool.get('ir.date')
        Milestone = pool.get('account.invoice.milestone')

        sales_to_invoice = [s for s in self.sales]
        if not sales_to_invoice:
            return

        milestone = Milestone()
        milestone.group = self
        # milestone.description =
        milestone.kind = 'manual'
        milestone.invoice_method = 'remainder'
        milestone.sales_to_invoice = sales_to_invoice
        milestone.planned_invoice_date = Date.today()
        return milestone

    @classmethod
    def copy(cls, groups, default=None):
        if default is None:
            default = {}
        default.setdefault('code', None)
        default['sales'] = None
        return super(AccountInvoiceMilestoneGroup, cls).copy(groups, default)

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('account.configuration')

        config = Config(1)
        if not config.milestone_group_sequence:
            cls.raise_user_error('missing_milestone_sequence')
        for value in vlist:
            if value.get('code'):
                continue
            value['code'] = Sequence.get_id(config.milestone_group_sequence.id)
        return super(AccountInvoiceMilestoneGroup, cls).create(vlist)

    @classmethod
    def delete(cls, groups):
        pool = Pool()
        Milestone = pool.get('account.invoice.milestone')
        milestones = Milestone.search([
                ('group', 'in', [g.id for g in groups]),
                ('state', 'not in', ['cancel', 'draft']),
                ], limit=1)
        if milestones:
            milestone, = milestones
            cls.raise_user_error('delete_cancel_draft', (
                    milestone.group.rec_name, milestone.rec_name))
        super(AccountInvoiceMilestoneGroup, cls).delete(groups)


_STATES = {
    'readonly': Eval('state') != 'draft',
    }
_DEPENDS = ['state']
_STATES_INV_DATE_CALC = {
    'readonly': (Bool(Eval('planned_invoice_date'))
        | (~Eval('state', '').in_(['draft', 'confirmed']))),
    # 'required': ((Eval('kind', '') == 'system')
    #     & (Eval('state', '') == 'confirmed')
    #     & (~Bool(Eval('planned_invoice_date')))),
    'invisible': Eval('kind', '') == 'manual',
    }
_DEPENDS_INV_DATE_CALC = ['planned_invoice_date', 'kind', 'state']


class AccountInvoiceMilestone(Workflow, ModelSQL, ModelView):
    'Account Invoice Milestone'
    __name__ = 'account.invoice.milestone'
    _rec_name = 'code'

    group = fields.Many2One('account.invoice.milestone.group',
        'Milestone Group', required=True, select=True, states=_STATES,
        depends=_DEPENDS, ondelete='CASCADE')
    company = fields.Function(fields.Many2One('company.company', 'Company'),
        'on_change_with_company', searcher='search_company')
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    party = fields.Function(fields.Many2One('party.party', 'Party'),
        'on_change_with_party', searcher='search_party')

    code = fields.Char('Code', required=True, readonly=True)
    description = fields.Char('Description', states=_STATES, depends=_DEPENDS,
        help='It will be used to prepare the description field of invoice '
        'lines.\nYou can use the next tags and they will be replaced by these '
        'fields from the sale\'s related to milestone: {sale_description}, '
        '{sale_reference}.')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('processing', 'Processing'),
            ('succeeded', 'Succeeded'),
            ('failed', 'Failed'),
            ('cancel', 'Cancel'),
            ], 'State', readonly=True, select=True)
    processed_date = fields.Date('Processed Date', readonly=True)

    kind = fields.Selection(_KIND, 'Kind', required=True, select=True,
        states=_STATES, depends=_DEPENDS)
    trigger_shipped_amount = fields.Numeric('On Shipped Amount',
        digits=(16, 8), states={
            'readonly': Eval('state') != 'draft',
            'required': Eval('kind') == 'system',
            'invisible': Eval('kind') == 'manual',
            },
        depends=['state', 'party', 'invoice_method', 'kind'],
        help="The percentage of sent amount over the total amount of "
        "Milestone's Trigger Sale Lines.")
    trigger_lines = fields.Many2Many('account.invoice.milestone-sale.line',
        'milestone', 'sale_line', 'Trigger Lines',
        domain=[
            ('sale.milestone_group', '=', Eval('group', -1)),
            ('type', '=', 'line'),
            ],
        states={
            'readonly': Eval('state') != 'draft',
            'required': Eval('kind') == 'system',
            'required': ((Eval('state') == 'confirmed') &
                (Eval('kind') == 'system')),
            'invisible': Eval('kind') == 'manual',
            }, depends=['group', 'state', 'kind'])

    invoice_method = fields.Selection([
            ('amount', 'Amount'),
            ('shipped_goods', 'Shipped Goods'),
            ('remainder', 'Remainder'),
            ], 'Invoice Method', required=True, select=True, sort=False,
        states=_STATES, depends=_DEPENDS)
    amount = fields.Numeric('Amount', digits=(16, Eval('currency_digits', 2)),
        states={
            'readonly': Eval('state') != 'draft',
            'required': Eval('invoice_method') == 'amount',
            'invisible': Eval('invoice_method') != 'amount',
            }, depends=['currency_digits', 'state', 'invoice_method'])
    sale_lines_to_invoice = fields.One2Many('sale.line', 'milestone',
        'Sale Lines to Invoice', domain=[
            ('type', '=', 'line'),
            ('sale.milestone_group', '=', Eval('group', -1)),
            # company domain is "inherit" from milestone_group
            If(~Bool(Eval('invoice', 0)),
                ('invoice_lines', '=', None),
                ()),
            ],
        add_remove=[
            ('milestone', '=', None),
            ('state', '!=', 'cancel'),
            ],
        states={
            'readonly': ~Eval('state').in_(['draft', 'confirmed']),
            'required': ((Eval('state') == 'processing') &
                (Eval('invoice_method') == 'shipped_goods')),
            'invisible': Eval('invoice_method') != 'shipped_goods',
            },
        depends=['invoice', 'group', 'state', 'invoice_method'])
    sales_to_invoice = fields.Many2Many(
        'account.invoice.milestone-remainder-sale.sale', 'milestone', 'sale',
        'Sales to Invoice', domain=[
            ('milestone_group', '=', Eval('group', -1)),
            # company domain is "inherit" from milestone_group
            ],
        states={
            'readonly': ~Eval('state').in_(['draft', 'confirmed']),
            'required': ((Eval('state') == 'processing') &
                (Eval('invoice_method') == 'remainder')),
            'invisible': Eval('invoice_method') != 'remainder',
            },
        depends=['group', 'state', 'invoice_method'])

    day = fields.Integer('Day of Month', states=_STATES_INV_DATE_CALC,
        depends=_DEPENDS_INV_DATE_CALC)
    month = fields.Selection([
            (None, ''),
            ('1', 'January'),
            ('2', 'February'),
            ('3', 'March'),
            ('4', 'April'),
            ('5', 'May'),
            ('6', 'June'),
            ('7', 'July'),
            ('8', 'August'),
            ('9', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December'),
            ], 'Month', sort=False, states=_STATES_INV_DATE_CALC,
        depends=_DEPENDS_INV_DATE_CALC)
    weekday = fields.Selection([
            (None, ''),
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday'),
            ], 'Day of Week', sort=False, states=_STATES_INV_DATE_CALC,
        depends=_DEPENDS_INV_DATE_CALC)
    months = fields.Integer('Number of Months', required=True,
        states=_STATES_INV_DATE_CALC, depends=_DEPENDS_INV_DATE_CALC)
    weeks = fields.Integer('Number of Weeks', required=True,
        states=_STATES_INV_DATE_CALC, depends=_DEPENDS_INV_DATE_CALC)
    days = fields.Integer('Number of Days', required=True,
        states=_STATES_INV_DATE_CALC, depends=_DEPENDS_INV_DATE_CALC)
    planned_invoice_date = fields.Date('Planned Invoice Date', states={
            'readonly': ~Eval('state', '').in_(['draft', 'confirmed']),
            'required': Eval('state', '').in_(['processing', 'succeeded']),
            }, depends=['state'])

    invoice = fields.One2One('account.invoice-account.invoice.milestone',
        'milestone', 'invoice', 'Invoice', readonly=True,
        domain=[
            ('company', '=', Eval('company')),
            ('party', '=', Eval('party')),
            ],
        states={
            'required': Eval('state', '').in_(['processing', 'succeeded']),
            },
        depends=['company', 'party', 'state'])

    @classmethod
    def __setup__(cls):
        super(AccountInvoiceMilestone, cls).__setup__()
        cls._sql_constraints += [
            ('trigger_shipped_amount',
                ('CHECK(trigger_shipped_amount IS NULL '
                    'OR trigger_shipped_amount BETWEEN 0.0 AND 1.0)'),
                'Trigger Percentage must to be between 0 and 100.0'),
            ('day', 'CHECK(day BETWEEN 1 AND 31)',
                'Day of month must be between 1 and 31.'),
            ]
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('confirmed', 'processing'),
                ('processing', 'succeeded'),
                ('processing', 'failed'),
                ('succeeded', 'failed'),  # If invoice is cancelled after post
                ('draft', 'cancel'),
                ('confirmed', 'cancel'),
                ('cancel', 'draft'),
                ))
        cls._buttons.update({
                'draft': {
                    'invisible': Eval('state') != 'cancel',
                    'icon': 'tryton-clear',
                    },
                'confirm': {
                    'invisible': Eval('state') != 'draft',
                    'icon': 'tryton-ok',
                    },
                'do_invoice': {
                    'invisible': ((Eval('state') != 'confirmed') |
                        (Eval('kind') != 'manual')),
                    'icon': 'tryton-ok',
                    },
                'cancel': {
                    'invisible': ~Eval('state').in_(['draft', 'confirmed']),
                    'icon': 'tryton-cancel',
                    },
                })
        cls._error_messages.update({
                'reset_milestone_in_closed_group': (
                    'You cannot reset to draft the Milestone "%s" because it '
                    'belongs to a closed Milestone Group.'),
                'invoice_not_done_move': ('Milestone "%(milestone)s" can not '
                    'be invoiced because its move "%(move)s is not done.'),
                'no_advancement_product': ('An advancement product must be '
                    'defined in order to generate advancement invoices.\n'
                    'Please define one in account configuration.'),
                'missing_milestone_sequence': ('There is no milestone sequence'
                    'defined. Please define one in account configuration'),
                })

    @fields.depends('group')
    def on_change_with_company(self, name=None):
        return (self.group.company.id if self.group and self.group.company
            else None)

    @classmethod
    def search_company(cls, name, clause):
        return [('group.company',) + tuple(clause[1:])]

    @fields.depends('group')
    def on_change_with_currency_digits(self, name=None):
        if self.group:
            return self.group.currency_digits
        return 2

    @staticmethod
    def default_party():
        return Transaction().context.get('party')

    @fields.depends('group')
    def on_change_with_party(self, name=None):
        return self.group.party.id if self.group else None

    @classmethod
    def search_party(cls, name, clause):
        return [('group.party',) + tuple(clause[1:])]

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_kind():
        return 'manual'

    @staticmethod
    def default_invoice_method():
        return 'amount'

    @staticmethod
    def default_months():
        return 0

    @staticmethod
    def default_weeks():
        return 0

    @staticmethod
    def default_days():
        return 0

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, milestones):
        for milestone in milestones:
            if milestone.group.state in ('completed', 'paid'):
                cls.raise_user_error('reset_milestone_in_closed_group', (milestone.rec_name,))

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, milestones):
        pass

    @classmethod
    @ModelView.button
    def do_invoice(cls, milestones):
        pool = Pool()
        Date = pool.get('ir.date')

        today = Date.today()
        to_proceed = []
        for milestone in milestones:
            if milestone.state != 'confirmed' or milestone.invoice:
                continue
            save_milestone = False
            if not milestone.planned_invoice_date:
                milestone.planned_invoice_date = (
                    milestone._calc_planned_invoice_date())
                save_milestone = True
            if (milestone.kind == 'system' and
                    milestone.planned_invoice_date > today):
                # Don't create invoices if it's not the time
                if save_milestone:
                    milestone.save()
                continue
            invoice = milestone.create_invoice()
            if invoice:
                milestone.invoice = invoice
                milestone.save()
                to_proceed.append(milestone)
            elif save_milestone:
                milestone.save()
        cls.proceed(to_proceed)

    @classmethod
    @Workflow.transition('processing')
    def proceed(cls, milestones):
        pool = Pool()
        Date = pool.get('ir.date')
        cls.write(milestones, {
                'processed_date': Date.today(),
                })

    @classmethod
    @Workflow.transition('succeeded')
    def succeed(cls, milestones):
        pass

    @classmethod
    @Workflow.transition('failed')
    def fail(cls, milestones):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('cancel')
    def cancel(cls, milestiones):
        pass

    def _calc_planned_invoice_date(self):
        pool = Pool()
        Date = pool.get('ir.date')
        today = Date.today()
        return today + relativedelta(**self._calc_delta())

    def _calc_delta(self):
        return {
            'day': self.day,
            'month': int(self.month) if self.month else None,
            'days': self.days,
            'weeks': self.weeks,
            'months': self.months,
            'weekday': int(self.weekday) if self.weekday else None,
            }

    def create_invoice(self):
        pool = Pool()
        Invoice = pool.get('account.invoice')

        invoice_type, invoice_lines = self._get_invoice_type_and_lines()
        if not invoice_lines:
            return

        invoice = self._get_invoice(invoice_type)
        invoice.lines = ((list(invoice.lines)
                if hasattr(invoice, 'lines') else [])
            + invoice_lines)
        invoice.save()

        Invoice.update_taxes([invoice])
        return invoice

    def _get_invoice(self, invoice_type):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        Journal = pool.get('account.journal')
        PaymentTerm = pool.get('account.invoice.payment_term')

        journals = Journal.search([
                ('type', '=', 'revenue'),
                ], limit=1)
        if journals:
            journal, = journals
        else:
            journal = None

        payment_term = self.party.customer_payment_term
        if not payment_term:
            terms = PaymentTerm.search([], limit=1)
            if terms:
                payment_term = terms[0]

        invoice = Invoice()
        invoice.company = self.group.company
        invoice.type = invoice_type
        invoice.journal = journal
        invoice.party = self.party
        invoice.invoice_address = self.party.address_get(type='invoice')
        invoice.currency = self.group.currency
        invoice.account = self.party.account_receivable
        invoice.payment_term = payment_term
        invoice.invoice_date = self.planned_invoice_date

        if getattr(self.party, 'agent'):
            # Compatibility with commission_party
            invoice.agent = self.party.agent

        return invoice

    def _get_invoice_type_and_lines(self):
        lines = []
        amount = _ZERO
        if self.invoice_method == 'amount':
            for invoice_type in ('out_invoice', 'out_credit_note'):
                line = self._get_advancement_invoice_line(invoice_type)
                if line:
                    amount += (self.amount if invoice_type == 'out_invoice'
                        else -self.amount)
                    lines.append(line)
        else:
            if self.invoice_method == 'shipped_goods':
                lines += self._get_shipped_goods_invoice_lines()
            else:  # remainder
                for sale in self.sales_to_invoice:
                    inv_line_desc = self.calc_invoice_line_description([sale])
                    with Transaction().set_context(
                            milestone_invoice_line_description=inv_line_desc):
                        for sale_line in sale.lines:
                            lines += sale_line.get_invoice_line('out_invoice')
                            lines += sale_line.get_invoice_line(
                                'out_credit_note')

            if lines:
                amount = sum((Decimal(str(l.quantity)) * l.unit_price
                        * (Decimal('1.0') if l.invoice_type == 'out_invoice'
                            else Decimal('-1.0'))) for l in lines)
                compensation_line = self.get_compensation_line(amount)
                if compensation_line:
                    amount += (Decimal(str(compensation_line.quantity))
                        * compensation_line.unit_price)
                    lines.append(compensation_line)

        invoice_type = ('out_credit_note' if amount < _ZERO
            else 'out_invoice')
        for line in lines:
            if line.invoice_type != invoice_type:
                line.invoice_type = invoice_type
                line.quantity *= -1

        return invoice_type, lines

    def _get_advancement_invoice_line(self, invoice_type):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')

        if self.state != 'confirmed' or self.invoice_method != 'amount':
            return
        if invoice_type == 'out_credit_note' and self.amount > _ZERO:
            return
        if invoice_type == 'out_invoice' and self.amount < _ZERO:
            return

        product = self.advancement_product
        sales = list(set(l.sale for l in self.trigger_lines))

        with Transaction().set_user(0, set_context=True):
            invoice_line = InvoiceLine()
        invoice_line.invoice_type = invoice_type
        invoice_line.party = self.party
        invoice_line.type = 'line'
        invoice_line.sequence = 1

        invoice_line.product = product
        invoice_line.description = self.calc_invoice_line_description(sales)
        invoice_line.quantity = 1.0
        invoice_line.unit = product.default_uom
        for key, value in invoice_line.on_change_product().iteritems():
            setattr(invoice_line, key, value)
        invoice_line.unit_price = abs(self.amount)
        invoice_line.origin = self

        return invoice_line

    def _get_shipped_goods_invoice_lines(self):
        invoice_lines = []
        for sale_line in self.sale_lines_to_invoice:
            invoice_type = ('out_credit_note' if sale_line.quantity < 0.0
                else 'out_invoice')
            inv_line_desc = self.calc_invoice_line_description(
                [sale_line.sale])
            with Transaction().set_context(
                    milestone_invoice_line_description=inv_line_desc):
                invoice_lines += sale_line.get_invoice_line(invoice_type)
        return invoice_lines

    def calc_invoice_line_description(self, sales):
        if (not self.description or not sales
                or ('sale_reference' not in self.description
                    and 'sale_description' not in self.description)):
            return self.description
        if not sales:
            return self.description

        description = self.description
        if '{sale_reference}' in description:
            description = description.replace('{sale_reference}',
                ", ".join(s.reference for s in sales))
        if '{sale_description}' in description:
            description = description.replace('{sale_description}',
                ", ".join(s.description for s in sales if s.description))
        return description

    def get_compensation_line(self, invoice_amount):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')

        amount = self.group.invoiced_advancement_amount
        if self.invoice_method == 'remainder':
            if (self.group.merited_amount == self.group.total_amount
                    and (self.group.invoiced_amount - amount + invoice_amount)
                        == self.group.merited_amount):
                # It closes the milestone group
                invoice_amount = None

        if invoice_amount is not None and invoice_amount < amount:
            amount = invoice_amount
        if amount == _ZERO:
            return

        with Transaction().set_user(0, set_context=True):
            invoice_line = InvoiceLine()
        invoice_line.invoice_type = 'out_invoice'
        invoice_line.type = 'line'
        invoice_line.sequence = 1
        invoice_line.description = ''
        invoice_line.origin = self
        invoice_line.party = self.group.party
        product = self.advancement_product
        invoice_line.product = product
        invoice_line.unit = product.default_uom
        for key, value in invoice_line.on_change_product().iteritems():
            setattr(invoice_line, key, value)
        invoice_line.quantity = -1.0
        invoice_line.unit_price = amount

        return invoice_line

    @property
    def advancement_product(self):
        pool = Pool()
        Config = pool.get('account.configuration')
        config = Config.get_singleton()
        if not config.milestone_advancement_product:
            self.raise_user_error('no_advancement_product')
        return config.milestone_advancement_product

    @classmethod
    def copy(cls, milestones, default=None):
        if default is None:
            default = {}
        default.setdefault('code', None)
        default.setdefault('processed_date', None)
        default.setdefault('trigger_lines', [])
        default.setdefault('sale_lines_to_invoice', [])
        default.setdefault('sales_to_invoice', [])
        default.setdefault('planned_invoice_date', None)
        default.setdefault('invoice', None)
        return super(AccountInvoiceMilestone, cls).copy(milestones, default)

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('account.configuration')

        config = Config(1)
        if not config.milestone_sequence:
            cls.raise_user_error('missing_milestone_sequence')
        for value in vlist:
            if value.get('code'):
                continue
            value['code'] = Sequence.get_id(config.milestone_sequence.id)
        return super(AccountInvoiceMilestone, cls).create(vlist)


class AccountInvoiceMilestoneSaleLine(ModelSQL):
    'Account Invoice Milestone - Sale Line'
    __name__ = 'account.invoice.milestone-sale.line'
    milestone = fields.Many2One('account.invoice.milestone',
        'Account Invoice Milestone', ondelete='CASCADE', required=True,
         select=True)
    sale_line = fields.Many2One('sale.line', 'Sale Line', ondelete='CASCADE',
        required=True, select=True)


class AccountInvoiceMilestoneRemainderSale(ModelSQL):
    'Account Invoice Milestone - Remainder - Sale'
    __name__ = 'account.invoice.milestone-remainder-sale.sale'
    milestone = fields.Many2One('account.invoice.milestone',
        'Account Invoice Milestone', ondelete='CASCADE', required=True,
        select=True)
    sale = fields.Many2One('sale.sale', 'Sale', ondelete='CASCADE',
        required=True, select=True)
