=============================================
Account Invoice Milestone - System Milestones
=============================================

System Amount based Milestones::
================================

Normal workflow with one sale and without invoice date gap
----------------------------------------------------------

Create a Sale with lines with service products and goods products::

Create a new Milestone Group and associate to the sale::

Add a System Milestone on 0% Shipped Amount of all sale's lines to invoice an
amount::

Add a System Milestone on 50% shipped Amount of some lines to invoice another
amount::

Add a System Milestone on 100% shipped Amount of all lins to invoice the
remainder::

Confirm all the group's milestones::

Confirm the Sale and check the first milestone is invoiced::

Ship some of the quantities and check any other milestone is invoiced::

Ship more than 50% of the amount of lines and check second milestone is
invoiced::

Ship the pending quantities and check the last milestone is invoiced::

Pay the invoices::

Check the group is completed and the sale is done::








Milestone Group Type with Amount based milestone types and the last remainder::
-------------------------------------------------------------------------------

Create a Milestone Group Type not *invoice shipments*::

Add a System Milestone Type on order accept to invoice 10% of sale order
amount::

Add a System Milestone Type on ship 50% of amount to invoice fixed amount::

Add a System Milestone Type on finish order to invoice the remainder::

Create a Sale with lines with service products and goods products::

Associate the Milestone Group Tye and confirm it::

Check a Milestone Group is created with the expected three confirmed
milestones::

Check the first milestone (10%) is invoiced::

