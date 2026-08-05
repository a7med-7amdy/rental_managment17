/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class RentalDashboard extends Component {
    static template = "rental_management.RentalDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({ loading: true, error: null, stats: {} });
        onWillStart(() => this.loadDashboard());
    }

    async loadDashboard() {
        this.state.loading = true;
        this.state.error = null;
        try {
            this.state.stats = await this.orm.call("property.details", "get_property_stats", []);
        } catch (error) {
            this.state.error = error?.message || "Unable to load rental dashboard data.";
            this.notification.add(this.state.error, { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    openProperties(stage = null) {
        const domain = stage ? [["stage", "=", stage]] : [];
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: stage ? "Properties" : "All Properties",
            res_model: "property.details",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            target: "current",
            domain,
        });
    }

    openContracts(status = null) {
        const domain = status ? [["contract_type", "=", status]] : [];
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: "Rental Contracts",
            res_model: "tenancy.details",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            target: "current",
            domain,
        });
    }

    openInvoices(mode = "all") {
        let domain = [];
        if (mode === "outstanding") {
            domain = [["amount_residual", ">", 0], ["tenancy_id", "!=", false]];
        } else if (mode === "overdue") {
            domain = [
                ["amount_residual", ">", 0],
                ["invoice_date_due", "<", new Date().toISOString().slice(0, 10)],
                ["tenancy_id", "!=", false],
            ];
        }
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: "Rental Invoices",
            res_model: "account.move",
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain,
        });
    }

    openMaintenance() {
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: "Rental Maintenance Requests",
            res_model: "maintenance.request",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            target: "current",
            domain: [["tenancy_id", "!=", false]],
        });
    }
}

registry.category("actions").add("property_dashboard", RentalDashboard);
