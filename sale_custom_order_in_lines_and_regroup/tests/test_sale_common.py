# -*- coding: utf-8 -*-

from collections import OrderedDict

from odoo.addons.account.tests.account_test_no_chart import (
    TestAccountNoChartCommon,
)


class TestCommonSaleNoChart(TestAccountNoChartCommon):
    """This class should be extended for test suite of sale flows with a minimal chart of accounting
    installed. This test suite should be executed at module installation.
    This class provides some method to generate testing data well configured, according to the minimal
    chart of account, defined in `TestAccountNoChartCommon` class.
    """

    @classmethod
    def setUpClass(cls):
        super(TestCommonSaleNoChart, cls).setUpClass()

        # create a pricelist
        cls.pricelist_usd = cls.env["product.pricelist"].create(
            {
                "name": "USD pricelist",
                "active": True,
                "currency_id": cls.env.ref("base.USD").id,
                "company_id": cls.env.user.company_id.id,
            }
        )

    @classmethod
    def setUpClassicProducts(cls):
        # Create an expense journal
        user_type_income = cls.env.ref(
            "account.data_account_type_direct_costs"
        )
        cls.account_income_product = cls.env["account.account"].create(
            {
                "code": "INCOME_PROD111",
                "name": "Income - Test Account",
                "user_type_id": user_type_income.id,
            }
        )
        # Create category
        cls.product_category = cls.env["product.category"].create(
            {
                "name": "Product Category with Income account",
                "property_account_income_categ_id": cls.account_income_product.id,
            }
        )
        # Products
        uom_unit = cls.env.ref("uom.product_uom_unit")
        uom_hour = cls.env.ref("uom.product_uom_hour")
        cls.product_order = cls.env["product.product"].create(
            {
                "name": "Zed+ Antivirus",
                "standard_price": 235.0,
                "list_price": 280.0,
                "type": "consu",
                "uom_id": uom_unit.id,
                "uom_po_id": uom_unit.id,
                "invoice_policy": "order",
                "expense_policy": "no",
                "default_code": "PROD_ORDER",
                "service_type": "manual",
                "taxes_id": False,
                "categ_id": cls.product_category.id,
            }
        )
        cls.product_stock_order = cls.env["product.product"].create(
            {
                "name": "Chair",
                "standard_price": 27.0,
                "type": "product",
                "categ_id": cls.product_category.id,
            }
        )
        cls.service_deliver = cls.env["product.product"].create(
            {
                "name": "Cost-plus Contract",
                "standard_price": 200.0,
                "list_price": 180.0,
                "type": "service",
                "uom_id": uom_unit.id,
                "uom_po_id": uom_unit.id,
                "invoice_policy": "delivery",
                "expense_policy": "no",
                "default_code": "SERV_DEL",
                "service_type": "manual",
                "taxes_id": False,
                "categ_id": cls.product_category.id,
            }
        )
        cls.service_order = cls.env["product.product"].create(
            {
                "name": "Prepaid Consulting",
                "standard_price": 40.0,
                "list_price": 90.0,
                "type": "service",
                "uom_id": uom_hour.id,
                "uom_po_id": uom_hour.id,
                "invoice_policy": "order",
                "expense_policy": "no",
                "default_code": "PRE-PAID",
                "service_type": "manual",
                "taxes_id": False,
                "categ_id": cls.product_category.id,
            }
        )
        cls.product_deliver = cls.env["product.product"].create(
            {
                "name": "Switch, 24 ports",
                "standard_price": 55.0,
                "list_price": 70.0,
                "type": "consu",
                "uom_id": uom_unit.id,
                "uom_po_id": uom_unit.id,
                "invoice_policy": "delivery",
                "expense_policy": "no",
                "default_code": "PROD_DEL",
                "service_type": "manual",
                "taxes_id": False,
                "categ_id": cls.product_category.id,
            }
        )

        cls.product_map = OrderedDict(
            [
                ("prod_order", cls.product_order),
                ("serv_del", cls.service_deliver),
                ("serv_order", cls.service_order),
                ("prod_del", cls.product_deliver),
            ]
        )
