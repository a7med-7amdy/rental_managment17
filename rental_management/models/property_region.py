# -*- coding: utf-8 -*-
# Copyright 2023-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class PropertyRegion(models.Model):
    _name = "property.region"
    _description = "Property Regions"

    name = fields.Char(string="Region")
    city_ids = fields.Many2many('property.res.city', string="Cities")
    project_count = fields.Integer(string="Project Count",
                                   compute="compute_count")
    subproject_count = fields.Integer(string="Subproject Count",
                                      compute="compute_count")
    unit_count = fields.Integer(string="Units Count",
                                compute="compute_count")

    def compute_count(self):
        project_groups = self.env["property.project"]._read_group(
            [("region_id", "in", self.ids)], ["region_id"], ["__count"]
        ) if self.ids else []
        subproject_groups = self.env["property.sub.project"]._read_group(
            [("region_id", "in", self.ids)], ["region_id"], ["__count"]
        ) if self.ids else []
        unit_groups = self.env["property.details"]._read_group(
            [("region_id", "in", self.ids)], ["region_id"], ["__count"]
        ) if self.ids else []
        project_map = {region.id: count for region, count in project_groups}
        subproject_map = {region.id: count for region, count in subproject_groups}
        unit_map = {region.id: count for region, count in unit_groups}
        for region in self:
            region.project_count = project_map.get(region.id, 0)
            region.subproject_count = subproject_map.get(region.id, 0)
            region.unit_count = unit_map.get(region.id, 0)

    def action_view_project(self):
        self.ensure_one()
        return {
            "name": "Projects",
            "type": "ir.actions.act_window",
            "domain": [("region_id", "=", self.id)],
            "view_mode": "list,form",
            'context': {'create': False},
            "res_model": "property.project",
            "target": "current",
        }

    def action_view_sub_project(self):
        self.ensure_one()
        return {
            "name": "Sub Projects",
            "type": "ir.actions.act_window",
            "domain": [("region_id", "=", self.id)],
            "view_mode": "list,form",
            'context': {'create': False},
            "res_model": "property.sub.project",
            "target": "current",
        }

    def action_view_properties(self):
        self.ensure_one()
        return {
            "name": "Units",
            "type": "ir.actions.act_window",
            "domain": [("region_id", "=", self.id)],
            "view_mode": "list,form",
            'context': {'create': False},
            "res_model": "property.details",
            "target": "current",
        }
