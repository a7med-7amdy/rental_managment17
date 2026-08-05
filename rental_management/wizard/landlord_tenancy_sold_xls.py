# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import base64
from io import BytesIO

import xlsxwriter

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class LandlordSaleTenancy(models.TransientModel):
    _name = "landlord.sale.tenancy"
    _description = "Landlord Tenancy And Sale Report"
    _rec_name = "landlord_id"

    landlord_id = fields.Many2one(
        "res.partner", domain="[('user_type','=','landlord')]", required=True
    )
    report_for = fields.Selection(
        [("tenancy", "Rent"), ("sold", "Property Sold")],
        string="Report For",
        required=True,
    )

    @staticmethod
    def _selection_label(record, field_name):
        value = record[field_name]
        return dict(record._fields[field_name]._description_selection(record.env)).get(
            value, value or ""
        )

    def _new_workbook(self):
        stream = BytesIO()
        workbook = xlsxwriter.Workbook(stream, {"in_memory": True})
        formats = {
            "title": workbook.add_format(
                {"bold": True, "font_size": 18, "align": "center", "bottom": 2}
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
            "cell": workbook.add_format({"border": 1, "align": "center"}),
            "date": workbook.add_format(
                {"border": 1, "align": "center", "num_format": "yyyy-mm-dd"}
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

    def _prepare_sheet(self, workbook, formats, name, title, headers):
        sheet = workbook.add_worksheet(name[:31])
        sheet.hide_gridlines(2)
        sheet.freeze_panes(2, 0)
        sheet.merge_range(0, 0, 0, len(headers) - 1, title, formats["title"])
        sheet.set_row(0, 28)
        sheet.set_row(1, 32)
        for column, header in enumerate(headers):
            sheet.write(1, column, header, formats["header"])
            sheet.set_column(column, column, max(14, min(len(header) + 4, 25)))
        sheet.autofilter(1, 0, 1, len(headers) - 1)
        return sheet

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

    def action_tenancy_sold_xls_report(self):
        self.ensure_one()
        if not self.landlord_id or not self.report_for:
            raise ValidationError(_("Select a landlord and report type."))
        stream, workbook, formats = self._new_workbook()
        safe_name = self.landlord_id.display_name.replace("/", "-")
        if self.report_for == "tenancy":
            domain = [("landlord_id", "=", self.landlord_id.id)]
            sheets = [
                ("All Rent Invoices", domain),
                ("Paid", domain + [("payment_state", "=", "paid")]),
                ("Not Paid", domain + [("payment_state", "=", "not_paid")]),
                ("Partial Paid", domain + [("payment_state", "=", "partial")]),
            ]
            for name, sheet_domain in sheets:
                self._write_rent_sheet(
                    workbook,
                    formats,
                    name,
                    "%s - %s" % (safe_name, name),
                    self.env["rent.invoice"].search(sheet_domain),
                )
            return self._download(stream, workbook, "%s Rent.xlsx" % safe_name)

        records = self.env["property.vendor"].search(
            [("landlord_id", "=", self.landlord_id.id)]
        )
        self._write_sale_sheet(
            workbook,
            formats,
            "Property Sales",
            "Sold Information - %s" % safe_name,
            records,
        )
        return self._download(stream, workbook, "%s Sold.xlsx" % safe_name)

    def _write_rent_sheet(self, workbook, formats, name, title, records):
        headers = [
            "Due Date",
            "Contract Reference",
            "Tenant",
            "Property",
            "Invoice Reference",
            "Payment Term",
            "Amount",
            "Payment Status",
            "Contract Status",
            "Company",
        ]
        sheet = self._prepare_sheet(workbook, formats, name, title, headers)
        total = 0.0
        for row, schedule in enumerate(records, start=2):
            move = schedule.rent_invoice_id
            values = [
                schedule.due_date or schedule.invoice_date,
                schedule.tenancy_id.tenancy_seq,
                schedule.customer_id.display_name,
                schedule.tenancy_id.property_id.display_name,
                move.display_name if move else "",
                self._selection_label(schedule.tenancy_id, "payment_term"),
                move.amount_total if move else schedule.amount,
                self._selection_label(schedule, "payment_state"),
                self._selection_label(schedule.tenancy_id, "contract_type"),
                schedule.company_id.display_name,
            ]
            total += values[6] or 0.0
            for column, value in enumerate(values):
                if column == 0 and value:
                    sheet.write_datetime(row, column, fields.Date.to_date(value), formats["date"])
                elif column == 6:
                    sheet.write_number(row, column, value or 0.0, formats["money"])
                else:
                    sheet.write(row, column, value or "", formats["cell"])
        total_row = len(records) + 2
        sheet.write(total_row, 5, "Total", formats["total_label"])
        sheet.write_number(total_row, 6, total, formats["total"])

    def _write_sale_sheet(self, workbook, formats, name, title, records):
        headers = [
            "Date",
            "Sequence",
            "Customer",
            "Property",
            "Sale Price",
            "Book Price",
            "Payable Amount",
            "Payment Term",
            "Paid Amount",
            "Remaining Amount",
            "Status",
            "Company",
        ]
        sheet = self._prepare_sheet(workbook, formats, name, title, headers)
        total_paid = total_remaining = 0.0
        for row, sale in enumerate(records, start=2):
            values = [
                sale.date,
                sale.sold_seq,
                sale.customer_id.display_name,
                sale.property_id.display_name,
                sale.total_sell_amount,
                sale.book_price,
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
                if column == 0 and value:
                    sheet.write_datetime(row, column, fields.Date.to_date(value), formats["date"])
                elif column in (4, 5, 6, 8, 9):
                    sheet.write_number(row, column, value or 0.0, formats["money"])
                else:
                    sheet.write(row, column, value or "", formats["cell"])
        total_row = len(records) + 2
        sheet.write(total_row, 7, "Totals", formats["total_label"])
        sheet.write_number(total_row, 8, total_paid, formats["total"])
        sheet.write_number(total_row, 9, total_remaining, formats["total"])
