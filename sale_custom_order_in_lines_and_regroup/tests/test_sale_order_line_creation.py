# -*- coding: utf-8 -*-

from odoo.tests import Form

from .test_sale_common import TestCommonSaleNoChart


class TestSaleOrder(TestCommonSaleNoChart):
    @classmethod
    def setUpClass(cls):
        super(TestSaleOrder, cls).setUpClass()
        super(TestSaleOrder, cls).setUpClassicProducts()
        cls.material_name = cls.env["sale.order"].get_material_name()
        cls.work_load_name = cls.env["sale.order"].get_work_load_name()

    def test_create_empty_sale_order_line(self):
        """Test sale order creation with nothing
        Expect section creation
        """
        expect_test = [
            (self.material_name, "line_section"),
            (self.work_load_name, "line_section"),
        ]

        form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        form.partner_id = self.partner_customer_usd
        form.partner_invoice_id = self.partner_customer_usd
        form.partner_shipping_id = self.partner_customer_usd
        so = form.save()

        result = [(a.name, a.display_type) for a in so.order_line]

        self.assertEqual(
            expect_test, result, "Empty create line_section at creation."
        )

    def test_create_empty_disable_sale_order_line(self):
        """Test sale order creation with nothing
        Expect section creation
        """
        expect_test = []

        form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        form.partner_id = self.partner_customer_usd
        form.partner_invoice_id = self.partner_customer_usd
        form.partner_shipping_id = self.partner_customer_usd

        form.automatic_group_sale_order_at_save = False
        so = form.save()

        result = [(a.name, a.display_type) for a in so.order_line]

        self.assertEqual(expect_test, result, "Empty order line")

    def test_create_only_service_sale_order_line(self):
        """Test sale order creation with only service
        Expect section creation
        """
        expect_test = [
            (self.material_name, "line_section"),
            (self.work_load_name, "line_section"),
            (self.service_deliver.display_name, False),
        ]

        form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        form.partner_id = self.partner_customer_usd
        form.partner_invoice_id = self.partner_customer_usd
        form.partner_shipping_id = self.partner_customer_usd

        # Insert line order
        with form.order_line.new() as line:
            line.product_id = self.service_deliver

        so = form.save()

        result = [(a.name, a.display_type) for a in so.order_line]

        self.assertEqual(expect_test, result, "One service")

    def test_create_only_product_consu_sale_order_line(self):
        """Test sale order creation with only product consu
        Expect section creation
        """
        expect_test = [
            (self.material_name, "line_section"),
            (self.product_order.display_name, False),
            (self.work_load_name, "line_section"),
        ]

        form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        form.partner_id = self.partner_customer_usd
        form.partner_invoice_id = self.partner_customer_usd
        form.partner_shipping_id = self.partner_customer_usd

        # Insert line order
        with form.order_line.new() as line:
            line.product_id = self.product_order

        so = form.save()

        result = [(a.name, a.display_type) for a in so.order_line]

        self.assertEqual(expect_test, result, "One product consu")

    def test_create_only_product_stockable_sale_order_line(self):
        """Test sale order creation with only product stockable
        Expect section creation
        """
        expect_test = [
            (self.material_name, "line_section"),
            (self.product_stock_order.display_name, False),
            (self.work_load_name, "line_section"),
        ]

        form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        form.partner_id = self.partner_customer_usd
        form.partner_invoice_id = self.partner_customer_usd
        form.partner_shipping_id = self.partner_customer_usd

        # Insert line order
        with form.order_line.new() as line:
            line.product_id = self.product_stock_order

        so = form.save()

        result = [(a.name, a.display_type) for a in so.order_line]

        self.assertEqual(expect_test, result, "One product stockable")

    def test_create_with_multiple_product_sale_order_line(self):
        """Test sale order creation with multiple product
        Expect section creation
        """
        expect_test = [
            (self.material_name, "line_section"),
            (self.product_stock_order.display_name, False),
            (self.product_order.display_name, False),
            (self.work_load_name, "line_section"),
            (self.service_deliver.display_name, False),
        ]

        form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        form.partner_id = self.partner_customer_usd
        form.partner_invoice_id = self.partner_customer_usd
        form.partner_shipping_id = self.partner_customer_usd

        # Insert line order
        with form.order_line.new() as line:
            line.product_id = self.service_deliver

        with form.order_line.new() as line:
            line.product_id = self.product_stock_order

        with form.order_line.new() as line:
            line.product_id = self.product_order

        so = form.save()

        result = [(a.name, a.display_type) for a in so.order_line]

        self.assertEqual(expect_test, result, "Multiple product")

    def test_create_with_notes_sale_order_line(self):
        """Test sale order creation with notes
        Expect section creation
        """
        note_1 = "note 1"
        note_2 = "note 2"
        note_3 = "note 3"
        expect_test = [
            (self.material_name, "line_section"),
            (note_3, "line_note"),
            (self.product_stock_order.display_name, False),
            (note_2, "line_note"),
            (self.product_order.display_name, False),
            (self.work_load_name, "line_section"),
            (self.service_deliver.display_name, False),
            (note_1, "line_note"),
        ]

        form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        form.partner_id = self.partner_customer_usd
        form.partner_invoice_id = self.partner_customer_usd
        form.partner_shipping_id = self.partner_customer_usd

        # Insert line order
        with form.order_line.new() as line:
            line.display_type = "line_note"
            line.name = note_3

        with form.order_line.new() as line:
            line.product_id = self.service_deliver

        with form.order_line.new() as line:
            line.display_type = "line_note"
            line.name = note_1

        with form.order_line.new() as line:
            line.product_id = self.product_stock_order

        with form.order_line.new() as line:
            line.display_type = "line_note"
            line.name = note_2

        with form.order_line.new() as line:
            line.product_id = self.product_order

        so = form.save()

        result = [(a.name, a.display_type) for a in so.order_line]

        self.assertEqual(expect_test, result, "With notes")

    def test_create_with_more_section_sale_order_line(self):
        """Test sale order creation with more section
        Expect section creation
        """
        section_1 = "section 1"
        section_2 = "section 2"
        expect_test = [
            (self.material_name, "line_section"),
            (self.product_stock_order.display_name, False),
            (self.product_order.display_name, False),
            (self.work_load_name, "line_section"),
            (self.service_deliver.display_name, False),
            (section_1, "line_section"),
            (section_2, "line_section"),
        ]

        form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        form.partner_id = self.partner_customer_usd
        form.partner_invoice_id = self.partner_customer_usd
        form.partner_shipping_id = self.partner_customer_usd

        # Insert line order
        with form.order_line.new() as line:
            line.display_type = "line_section"
            line.name = section_1

        with form.order_line.new() as line:
            line.product_id = self.service_deliver

        with form.order_line.new() as line:
            line.display_type = "line_section"
            line.name = section_2

        with form.order_line.new() as line:
            line.product_id = self.product_stock_order

        with form.order_line.new() as line:
            line.product_id = self.product_order

        so = form.save()

        result = [(a.name, a.display_type) for a in so.order_line]

        self.assertEqual(expect_test, result, "With sections")

    def test_create_with_same_section_sale_order_line(self):
        """Test sale order creation with more section and delete repeated supported section
        Expect section creation
        """
        section_1 = "section 1"
        section_2 = "section 2"
        section_material = "Material"
        section_material_2 = "Material"
        section_work_load = "Work load"
        section_work_load_2 = "Work load"
        expect_test = [
            (self.material_name, "line_section"),
            (self.product_stock_order.display_name, False),
            (self.product_order.display_name, False),
            (self.work_load_name, "line_section"),
            (self.service_deliver.display_name, False),
            (section_1, "line_section"),
            (section_2, "line_section"),
        ]

        form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        form.partner_id = self.partner_customer_usd
        form.partner_invoice_id = self.partner_customer_usd
        form.partner_shipping_id = self.partner_customer_usd

        # Insert line order
        with form.order_line.new() as line:
            line.display_type = "line_section"
            line.name = section_material

        with form.order_line.new() as line:
            line.display_type = "line_section"
            line.name = section_1

        with form.order_line.new() as line:
            line.product_id = self.service_deliver

        with form.order_line.new() as line:
            line.display_type = "line_section"
            line.name = section_material_2

        with form.order_line.new() as line:
            line.display_type = "line_section"
            line.name = section_2

        with form.order_line.new() as line:
            line.display_type = "line_section"
            line.name = section_work_load

        with form.order_line.new() as line:
            line.product_id = self.product_stock_order

        with form.order_line.new() as line:
            line.product_id = self.product_order

        with form.order_line.new() as line:
            line.display_type = "line_section"
            line.name = section_work_load_2

        so = form.save()

        result = [(a.name, a.display_type) for a in so.order_line]

        self.assertEqual(expect_test, result, "With sections")
