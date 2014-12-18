=============================================
Account Invoice Milestone - Manual Milestones
=============================================

.. Set the Planned Invoice Date in some miletones. It is used as Invoice Date
   without any other consequence

Manual Amount based Milestones
==============================

One Sale One Amount Milestone - Normal workflow
-----------------------------------------------

Create a Sale with lines with service products and goods products::

Create a Milestone Group with a manual amount based Milestone with an amount
less than sales amount::

Assign the Milestone Group to the Sale and confirm the Sale::

Check Milestone's amounts: Total Amount == Sale's Untaxed Amount, Merited
Amount, Invoiced Amount and Assigned Amount is 0.0::

Confirm and Invoice the Milestone::

Check an invoice with untaxed amount as Milestone's amount is created and
associated to milestone::

Confirm the invoice::

Check Invoiced Amount is the Invoice Untaxed Amount and the rest of Milestone's
amounts remain the same::

Process the Sale and it's Shipment::

Check Shipment State of sale is Sent and Invoice State is Waiting::

Check the Merited Amount is the Sale's Untaxed Amount::

Close the Milestone Group::

Check a Remainder Milestone is added to group with a Draft invoice with the
Sale's Untaxed Amount less previous invoice amount::

Confirm the invoice and check the Invoiced Amount and Assigned Amount are the
Total Amount and the Group's state is Completed::

Pay the invoices and check the Group's state is Completed::


One Sale One Amount Milestone - Close group before invoice Milestone
--------------------------------------------------------------------

Duplicate the Sale and create a Milestone Group with a Manual Amount based
Milestone and associate the Milestone Group to the Sale::

Process the Sale and its Shipment::

Close the Milestone Group: an User Error is raised

Cancel the milestone and close the group::

Check a remainder milestone is created with an associated invoice with the
sale's untaxed amount::


One Sale One Amount Milestone - Two closings and Credit Note
------------------------------------------------------------

Duplicate the sale and create a Milestone Group with a Manual Amount based
Milestone with an amount greater than Sale's Untaxed Amount::

Associate the Milestone Group to Sale and process the Sale::

Confirm and Invoice the Milestone. Confirm the associated invoice::

Close the Milestone Group::

Check a remainder Milestone is created with the service products and amount
0::

Process the Sale's Shipment::

Close the Milestone Group::

Check that another Remainder Milestone is created with a Credit Note Invoice
associated with the goods products and Untaxed Amount the difference between
advanced Milestone Amount and Sales amount::


Two Sales One Amount Milestone
------------------------------

Duplicate the sale twice and create a Milestone Group with a Manual Amount
based Milestone::

Associate the Milestone Group to the sales and process completly both::

Check group's amounts::

Confirm and Invoice the Milestone. Confirm the associated invoice::

Check group's amounts::

Close the group and confirm the invoice. Check the amounts::


Two Sales Two Amount Milestone
------------------------------

Duplicate the sale twice and create a Milestone Group with a Manual Amount
based Milestone::

Associate the Milestone Group to one sale and confirm it::

Check group's amounts::

Confirm and Invoice the Milestone. Confirm the associated invoice::

Add the second Sale to Milestone Group, add a second Amount based Milestone and
confirm the sale. Check amounts::

Confirm and invoice the second milestone::

Process both sales without process thier shipments::

Close (partialy) the group. Confirm invoice and check amounts::

Close again the group. Check new Remainder milestone is created but it doesn't
have invoice (and if you try to invoice the milestone it is not created). Check
the amounts (assigned amount must to be Total Amount)::

Cancel the pending remainder milestone. Check Assigned Amount is the same than
Merited Amount::

Process the shipment of first sale and close the group. Confirm invoice and
check amounts::

Process the shipment of second sale and close the group. Confirm the invoice.
Group must to be *completed*::


One Sale, One return Sale and Two Amount Milestone
--------------------------------------------------

Duplicate the sale and create a Milestone Group with two Manual Amount based
Milestone::

Associate the Milestone Group to the Sale and process it::

Confirm and Invoice the two Milestones::

Return some lines of the sale and associate the group to the new returning
sale::

Process the returning sale::

Check Milestone Group's amounts and close it. Confirm the invoice::

Repeat this test but returning more amount than advanced. It generates a Credit
Note on group closing::


Shipped Goods based Milestones
==============================

One Sale One Shipped Goods Milestone - Normal workflow
-------------------------------------------------------

Duplicate the sale and create a Milestone Group with a Shipped Goods based
Milestone::

Confirm and process the Sale. Add all sale's moves to the milestone, confirm it
and check group's amounts::

Process the sale's shipment::

Invoice the Shipped Goods Milestone. Confirm the invoice::

Check the group's amounts. Merited amount is the Total Amount, the Invoiced
Amount is the amount of goods products (shipment amount). Pending amount is the
services lines amount::

Close the Milestone Group::

Check a Remainder Milestone is added to group with a Draft invoice with the
services lines amount::

Confirm the invoice and check the group is completed::


Multiple Sale Multiple Shipped Goods Milestone - Close before ship - Partial shipment
-------------------------------------------------------------------------------------

Duplicate the sale and create a Milestone Group with a Shipped Goods based
Milestone::

Confirm and process the Sale. Add all sale's moves to the milestone, confirm it
and check group's amounts::

Try to close the group. An User Error is raised.

Process partialy the sale's shipment::

Check the group's amounts. Check the new move with remaining quantity is in
milestone::

Remove the pending move from milestone and invoice the milestone::

Confirm the invoice and check amounts::

Add a Shipped Goods Milestone with the pending move and confirm it::

Cancel the pending shipment::

Handle the Shipment Exception of sale ignoring (no recreating) the cancelled
move::

The second Milestone is cancelled. Close the group. Check new Remainder
Milestone is created with an invoice with services lines. Confirm the invoice::

Duplicate the sale, remove services lines and confirm and process it (the same
Milestone Group is associated)::

Check the group's amounts. Add a Shipped Goods Milestone with the moves of the
new sale. Confirm it::

Ship some of the quantities of sale's shipment::

Cancel the pending quantities::

Handle the Shipment Exception ignoring the cancelled moves::

Check the group's amounts: Assigned Amount must to be 0.0 and Total Amount had
to be decreated with the canceled moves amount::

Close the group and confirm the invoice (the sale's amount without cancelled
amount)::

Duplicate the last sale (without services) and confirm and process it::

Create a new Shipped Goods Milestone with the new sale's moves. Confirm it::

Process partialy the sale's shipment. Process the new shipment::

Invoice the Milestone and confirm the invoice::

Check the group is completed::


Shipped Goods Milestone with Sale Return
----------------------------------------

Duplicate the original sale and create a Milestone Group with a Shipped Goods
based Milestone::

Confirm and process the Sale. Add all sale's moves to the milestone, confirm it
and check group's amounts::

Process the sale's shipment::

Create a Sale Return for some of products (services and no services)::

Process the sale. Add its moves to the milestone::

Process the Return Sale shipment::

Invoice the Milestone::

Close the group::


Mixed Manual Milestones
=======================

Duplicate the original sale and create a Milestone Group with an Amount
Milestone and a Shipped Goods Milestone. Confirm and process the Sale::

Confirm and invoice the Amount Milestone. Confirm its invoice::

Add all sale's moves to Shipped Goods Milestone. Confirm and invoice it.
Confirm the new invoice::

Close the Milestone Group and confirm the new invoice::

Create two new sales with new products and associate them to the Milestone
Group. Confirm and process the sales::

Add an Amount Milestone and two Shipped Goods Milestone to group. Associate all
the moves of one of the new sales and part of the moves of the other sale to
the first Shipped Goods Milestone. Associate the rest of the moves to the
second Shpped Goods Milestone::

Confirm and invoice the pending Amount Milestone and the first (of the new)
Shipped Goods Milestone::

Create a Sale Return, associate to the Milestone Group and confirm and process
it::

Add the return sale moves to the last Shipped Goods Milestone and invoice it::

Check the group is completed::


Mixed Manual Milestones invoiced from Shipments
===============================================

Duplicate the original sale and create a Milestone Group *invoice shipments*
with an Amount Milestone and a Shipped Goods Milestone::

Confirm and process the Sale::

Confirm and invoice the Amount Milestone. Confirm its invoice::

Add some of sale's moves to Shipped Goods Milestone. Confirm it::

Process the shipment::

Check a new Shipped Goods Milestone is created with the moves not added to the
other milestone and it has an Invoice. Confirm it::

Invoice the pending Shipped Goods Milestone and confirm its invoice::

Check the group is completed::

Create two new sales with new products and associate them to the Milestone
Group. Confirm and process the sales::

Add an Amount Milestone and a Shipped Goods Milestone to group. Associate some
of the moves of one of the sales to this milestone::

Confirm and invoice the pending Amount Milestone and the first (of the new)
Shipped Goods Milestone::

Process the new sales shipments::

Check a new Shiped Goods Milestone is created with the moves not manually added
to previous Shipped Goods Milestones::

Create a Sale Return, associate to the Milestone Group and confirm and process
it::

Add some of the the return sale moves to the last Shipped Goods Milestone::

Process the Sale Return shipment. Check a new Shipped Goods Milestone is
created::

Invoice the pending Shipped Goods Milestone::

Check the group is completed::

