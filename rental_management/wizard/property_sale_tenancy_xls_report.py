# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import base64
from io import BytesIO

import xlsxwriter

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class PropertyXlsxReport(models.TransientModel):
    _name = "property.report.wizard"
    _description = "Create Property Report"
    _rec_name = "type"

    type = fields.Selection(
        [("tenancy", "Rent"), ("sold", "Property Sold")], string="Report For"
    )
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def _validate_period(self):
        self.ensure_one()
        if not self.start_date or not self.end_date:
            raise ValidationError(_("Select a start date and an end date."))
        if self.start_date > self.end_date:
            raise ValidationError(_("The start date cannot be after the end date."))

    def _new_workbook(self):
        stream = BytesIO()
        workbook = xlsxwriter.Workbook(stream, {"in_memory": True})
        formats = {
            "title": workbook.add_format(
                {
                    "bold": True,
                    "font_size": 18,
                    "align": "center",
                    "valign": "vcenter",
                    "bottom": 2,
                }
            ),
            "header": workbook.add_format(
                {
                    "bold": True,
                    "align": "center",
                    "valign": "vcenter",
                    "border": 1,
                    "bg_color": "#E9ECEF",
                    "text_wrap": True,
                }
            ),
            "text": workbook.add_format({"border": 1, "valign": "vcenter"}),
            "center": workbook.add_format(
                {"border": 1, "align": "center", "valign": "vcenter"}
            ),
            "date": workbook.add_format(
                {
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                    "num_format": "yyyy-mm-dd",
                }
            ),
            "money": workbook.add_format(
                {"border": 1, "align": "right", "num_format": "#,##0.00"}
            ),
            "total_label": workbook.add_format(
                {"bold": True, "border": 1, "align": "right", "bg_color": "#E9ECEF"}
            ),
            "total": workbook.add_format(
                {"bold": True, "border": 1, "align": "right", "num_format": "#,##0.00"}
            ),
        }
        return stream, workbook, formats

    def _download(self, stream, workbook, filename):
        workbook.close()
        attachment = self.env["ir.attachment"].create(
            {
                "name": filename,
                "type": "binary",
                "public": False,
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "datas": base64.b64encode(stream.getvalue()),
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % attachment.id,
            "target": "self",
        }

    @staticmethod
    def _selection_label(record, field_name):
        value = record[field_name]
        selection = record._fields[field_name]._description_selection(record.env)
        return dict(selection).get(value, value or "")

    def action_property_xls_report(self):
        self.ensure_one()
        self._validate_period()
        stream, workbook, formats = self._new_workbook()
        if self.type == "tenancy":
            domain = [
                ("start_date", ">=", self.start_date),
                ("start_date", "<=", self.end_date),
            ]
            sheets = [
                ("Rent Contracts", domain),
                ("Running Contracts", domain + [("contract_type", "=", "running_contract")]),
                ("Closed Contracts", domain + [("contract_type", "=", "close_contract")]),
                ("Expired Contracts", domain + [("contract_type", "=", "expire_contract")]),
            ]
            for name, sheet_domain in sheets:
                self._write_contract_sheet(
                    workbook, formats, name, self.env["tenancy.details"].search(sheet_domain)
                )
            return self._download(stream, workbook, "Rent Details.xlsx")

        domain = [("date", ">=", self.start_date), ("date", "<=", self.end_date)]
        self._write_sale_sheet(
            workbook,
            formats,
            "Property Sales",
            self.env["property.vendor"].search(domain),
        )
        self._write_sale_sheet(
            workbook,
            formats,
            "Sold Properties",
            self.env["property.vendor"].search(domain + [("stage", "=", "sold")]),
        )
        return self._download(stream, workbook, "Sold Information.xlsx")

    def _prepare_sheet(self, workbook, formats, name, title, headers):
        sheet = workbook.add_worksheet(name[:31])
        sheet.hide_gridlines(2)
        sheet.freeze_panes(2, 0)
        sheet.set_row(0, 28)
        sheet.set_row(1, 32)
        sheet.merge_range(0, 0, 0, len(headers) - 1, title, formats["title"])
        for column, header in enumerate(headers):
            sheet.write(1, column, header, formats["header"])
            sheet.set_column(column, column, max(14, min(len(header) + 4, 24)))
        sheet.autofilter(1, 0, 1, len(headers) - 1)
        return sheet

    def _write_contract_sheet(self, workbook, formats, name, records):
        headers = [
            "Reference",
            "Property",
            "Property Type",
            "Tenant",
            "Landlord",
            "Broker",
            "Total Area",
            "Start Date",
            "End Date",
            "Payment Term",
            "Rent",
            "Security Deposit",
            "Broker Commission",
            "Total Amount",
            "Paid Amount",
            "Remaining Amount",
            "Status",
            "Company",
        ]
        sheet = self._prepare_sheet(workbook, formats, name, "RENT CONTRACT DETAILS", headers)
        total_paid = total_remaining = 0.0
        for row, contract in enumerate(records, start=2):
            currency = contract.currency_id or contract.company_id.currency_id
            subtype = contract.property_subtype_id.display_name if contract.property_subtype_id else ""
            property_type = self._selection_label(contract, "property_type")
            unit = self._selection_label(contract, "measure_unit")
            values = [
                contract.tenancy_seq,
                contract.property_id.display_name,
                " / ".join(filter(None, [property_type, subtype])),
                contract.tenancy_id.display_name,
                contract.property_landlord_id.display_name,
                contract.broker_id.display_name if contract.broker_id else "",
                "%s %s" % (contract.total_area, unit),
                contract.start_date,
                contract.end_date,
                self._selection_label(contract, "payment_term"),
                contract.total_rent,
                contract.deposit_amount,
                contract.commission,
                contract.total_amount,
                contract.paid_tenancy,
                contract.remain_tenancy,
                self._selection_label(contract, "contract_type"),
                contract.company_id.display_name,
            ]
            total_paid += contract.paid_tenancy
            total_remaining += contract.remain_tenancy
            for column, value in enumerate(values):
                if column in (7, 8) and value:
                    sheet.write_datetime(row, column, fields.Date.to_date(value), formats["date"])
                elif column in (10, 11, 12, 13, 14, 15):
                    sheet.write_number(row, column, value or 0.0, formats["money"])
                else:
                    sheet.write(row, column, value or "", formats["center"])
            sheet.write_comment(row, 10, "Currency: %s" % currency.display_name)
        total_row = len(records) + 2
        sheet.write(total_row, 13, "Totals", formats["total_label"])
        sheet.write_number(total_row, 14, total_paid, formats["total"])
        sheet.write_number(total_row, 15, total_remaining, formats["total"])

    def _write_sale_sheet(self, workbook, formats, name, records):
        headers = [
            "Reference",
            "Property",
            "Property Type",
            "Total Area",
            "Customer",
            "Landlord",
            "Broker",
            "Broker Commission",
            "Selling Price",
            "Customer Ask Price",
            "Confirmed Sale Price",
            "Book Price",
            "Total Maintenance",
            "Utilities Cost",
            "Payable Amount",
            "Payment Term",
            "Paid Amount",
            "Remaining Amount",
            "Status",
            "Company",
        ]
        sheet = self._prepare_sheet(workbook, formats, name, "PROPERTY SALE INFORMATION", headers)
        total_paid = total_remaining = 0.0
        for row, sale in enumerate(records, start=2):
            subtype = sale.property_subtype_id.display_name if sale.property_subtype_id else ""
            property_type = self._selection_label(sale, "type")
            unit = self._selection_label(sale, "measure_unit")
            values = [
                sale.sold_seq,
                sale.property_id.display_name,
                " / ".join(filter(None, [property_type, subtype])),
                "%s %s" % (sale.total_area, unit),
                sale.customer_id.display_name,
                sale.landlord_id.display_name,
                sale.broker_id.display_name if sale.is_any_broker and sale.broker_id else "",
                sale.broker_final_commission,
                sale.price,
                sale.ask_price,
                sale.sale_price,
                sale.book_price,
                sale.total_maintenance,
                sale.total_service,
                sale.payable_amount,
                self._selection_label(sale, "payment_term"),
                sale.paid_amount,
                sale.remaining_amount,
                self._selection_label(sale, "stage"),
                sale.company_id.display_name,
            ]
            total_paid += sale.paid_amount
            total_remaining += sale.remaining_amount
            for column, value in enumerate(values):
                if column in (7, 8, 9, 10, 11, 12, 13, 14, 16, 17):
                    sheet.write_number(row, column, value or 0.0, formats["money"])
                else:
                    sheet.write(row, column, value or "", formats["center"])
        total_row = len(records) + 2
        sheet.write(total_row, 15, "Totals", formats["total_label"])
        sheet.write_number(total_row, 16, total_paid, formats["total"])
        sheet.write_number(total_row, 17, total_remaining, formats["total"])
