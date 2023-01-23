# -*- coding: utf-8 -*-

from odoo.tests import Form

from .test_sale_common import TestCommonSaleNoChart


class TestSaleOrder(TestCommonSaleNoChart):
    @classmethod
    def setUpClass(cls):
        super(TestSaleOrder, cls).setUpClass()
        super(TestSaleOrder, cls).setUpClassicProducts()
        cls.material_name = (
            cls.env["sale.order"]
            .with_context(tracking_disable=True)
            .get_material_name()
        )
        cls.work_load_name = (
            cls.env["sale.order"]
            .with_context(tracking_disable=True)
            .get_work_load_name()
        )

    def test_remove_section_and_product_sale_order_line(self):
        """Test sale order creation and remove section and product
        Expect section creation
        """
        section_1 = "section 1"
        note_1 = "note 1"
        note_2 = self.material_name
        note_3 = self.work_load_name

        expect_1_test = [
            (self.material_name, "line_section"),
            (self.product_stock_order.display_name, False),
            (note_1, "line_note"),
            (self.product_order.display_name, False),
            (note_2, "line_note"),
            (self.work_load_name, "line_section"),
            (self.service_deliver.display_name, False),
            (note_3, "line_note"),
            (section_1, "line_section"),
        ]

        expect_2_test = [
            (self.material_name, "line_section"),
            (self.product_stock_order.display_name, False),
            (note_1, "line_note"),
            (self.product_order.display_name, False),
            (note_2, "line_note"),
            (self.work_load_name, "line_section"),
            (note_3, "line_note"),
            (section_1, "line_section"),
        ]

        form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        form.partner_id = self.partner_customer_usd
        form.partner_invoice_id = self.partner_customer_usd
        form.partner_shipping_id = self.partner_customer_usd

        # Insert line order
        with form.order_line.new() as line:
            line.product_id = self.service_deliver

        with form.order_line.new() as line:
            line.display_type = "line_note"
            line.name = note_3

        with form.order_line.new() as line:
            line.display_type = "line_section"
            line.name = section_1

        with form.order_line.new() as line:
            line.product_id = self.product_stock_order

        with form.order_line.new() as line:
            line.display_type = "line_note"
            line.name = note_1

        with form.order_line.new() as line:
            line.product_id = self.product_order

        with form.order_line.new() as line:
            line.display_type = "line_note"
            line.name = note_2

        so = form.save()
        result = [(a.name, a.display_type) for a in so.order_line]
        self.assertEqual(expect_1_test, result, "Before writing")

        form = Form(so)

        # Remove all lines
        form.order_line.remove(6)
        form.order_line.remove(0)

        so = form.save()
        result = [(a.name, a.display_type) for a in so.order_line]
        self.assertEqual(expect_2_test, result, "After writing")
