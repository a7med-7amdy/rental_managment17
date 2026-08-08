/** @odoo-module **/

import {
    Component,
    onMounted,
    onWillStart,
    onWillUnmount,
    useRef,
    useState,
} from "@odoo/owl";
import { loadJS } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const LIBRARY_URLS = [
    "/rental_management/static/src/js/lib/index.js",
    "/rental_management/static/src/js/lib/map.js",
    "/rental_management/static/src/js/lib/xy.js",
    "/rental_management/static/src/js/lib/worldLow.js",
    "/rental_management/static/src/js/lib/Animated.js",
    "/rental_management/static/src/js/lib/apexcharts.js",
];

export class RentalDashboard extends Component {
    static template = "rental_management.rental_dashboard";

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.chartRoots = [];
        this.apexCharts = [];

        this.state = useState({
            propertyStats: {
                total_property: 0,
                avail_property: 0,
                sold_property: 0,
                booked_property: 0,
                sale_property: 0,
                lease_property: 0,
                sold_total: "0",
                sale_sold: 0,
                booked: 0,
                draft_contract: 0,
                running_contract: 0,
                expire_contract: 0,
                pending_invoice: 0,
                rent_total: "0",
                region_count: 0,
                project_count: 0,
                subproject_count: 0,
                landlord_count: 0,
                customer_count: 0,
                pending_invoice_sale: 0,
                close_contract: 0,
                extend_contract: 0,
                refund: 0,
            },
            propertyType: { "x-axis": [], "y-axis": [] },
            propertyStages: { "x-axis": [], "y-axis": [] },
            tenancyTopBroker: { "x-axis": [], "y-axis": [] },
            tenancyDuePaid: { "x-axis": [], "y-axis": [] },
            propertyMapData: [],
        });

        this.propertyType = useRef("propertyType");
        this.tenancyTopBroker = useRef("tenancyTopBroker");
        this.tenancyDuePaid = useRef("tenancyDuePaid");
        this.worldMap = useRef("worldMap");

        onWillStart(async () => {
            await this._loadChartLibraries();
            await this._loadDashboardData();
        });
        onMounted(() => this._renderCharts());
        onWillUnmount(() => this._disposeCharts());
    }

    async _loadChartLibraries() {
        for (const url of LIBRARY_URLS) {
            await loadJS(url);
        }
        const requiredGlobals = [
            "am5",
            "am5xy",
            "am5map",
            "am5themes_Animated",
            "am5geodata_worldLow",
            "ApexCharts",
        ];
        const missing = requiredGlobals.filter((name) => !globalThis[name]);
        if (missing.length) {
            throw new Error(`Rental dashboard chart libraries failed to load: ${missing.join(", ")}`);
        }
    }

    async _loadDashboardData() {
        try {
            const propertyData = await this.orm.call("property.details", "get_property_stats", []);
            if (!propertyData) {
                return;
            }
            this.state.propertyStats = propertyData;
            this.state.propertyType = {
                "x-axis": propertyData.property_type?.[0] || [],
                "y-axis": propertyData.property_type?.[1] || [],
            };
            this.state.propertyStages = {
                "x-axis": propertyData.property_stage?.[0] || [],
                "y-axis": propertyData.property_stage?.[1] || [],
            };
            this.state.tenancyTopBroker = {
                "x-axis": propertyData.tenancy_top_broker?.[0] || [],
                "y-axis": propertyData.tenancy_top_broker?.[1] || [],
            };
            this.state.tenancyDuePaid = {
                "x-axis": propertyData.due_paid_amount?.[2] || [],
                "y-axis": propertyData.due_paid_amount?.[3] || [],
            };
            this.state.propertyMapData = propertyData.property_map_data || [];
        } catch (error) {
            const message = error?.message || "Unable to load rental dashboard data.";
            this.notification.add(message, { type: "danger" });
            throw error;
        }
    }

    _disposeCharts() {
        for (const chart of this.apexCharts.splice(0)) {
            try {
                chart.destroy();
            } catch {
                // The chart may already be destroyed by the browser during navigation.
            }
        }
        for (const root of this.chartRoots.splice(0)) {
            try {
                root.dispose();
            } catch {
                // The root may already be disposed by amCharts.
            }
        }
    }

    _renderCharts() {
        this._disposeCharts();
        if (this.propertyType.el) {
            this.renderPropertyType(this.propertyType.el, this.state.propertyType);
        }
        if (this.tenancyTopBroker.el) {
            this.renderTenancyTopBroker();
        }
        if (this.tenancyDuePaid.el) {
            this.renderTenancyDuePaid();
        }
        if (this.worldMap.el) {
            this.renderMapProperties(this.worldMap.el, this.state.propertyMapData);
        }
    }

    renderPropertyType(div, sessionData) {
        const { am5, am5xy, am5themes_Animated } = globalThis;
        const root = am5.Root.new(div);
        this.chartRoots.push(root);
        root.setThemes([am5themes_Animated.new(root)]);

        const values = sessionData["y-axis"] || [];
        const data = [
            {
                name: "Land",
                steps: Number(values[0] || 0),
                pictureSettings: { src: "/rental_management/static/src/img/land-dash.svg" },
            },
            {
                name: "Residential",
                steps: Number(values[1] || 0),
                pictureSettings: { src: "/rental_management/static/src/img/re-dash.svg" },
            },
            {
                name: "Commercial",
                steps: Number(values[2] || 0),
                pictureSettings: { src: "/rental_management/static/src/img/come-dash.svg" },
            },
            {
                name: "Industrial",
                steps: Number(values[3] || 0),
                pictureSettings: { src: "/rental_management/static/src/img/ind-dash.svg" },
            },
        ];

        const chart = root.container.children.push(
            am5xy.XYChart.new(root, {
                panX: false,
                panY: false,
                wheelX: "none",
                wheelY: "none",
                paddingBottom: 50,
                paddingTop: 40,
                paddingLeft: 0,
                paddingRight: 0,
            })
        );
        const xRenderer = am5xy.AxisRendererX.new(root, {
            minorGridEnabled: true,
            minGridDistance: 60,
        });
        xRenderer.grid.template.set("visible", false);
        const xAxis = chart.xAxes.push(
            am5xy.CategoryAxis.new(root, {
                paddingTop: 40,
                categoryField: "name",
                renderer: xRenderer,
            })
        );
        const yRenderer = am5xy.AxisRendererY.new(root, {});
        yRenderer.grid.template.set("strokeDasharray", [3]);
        const yAxis = chart.yAxes.push(
            am5xy.ValueAxis.new(root, {
                min: 0,
                renderer: yRenderer,
            })
        );
        const series = chart.series.push(
            am5xy.ColumnSeries.new(root, {
                name: "Properties",
                xAxis,
                yAxis,
                valueYField: "steps",
                categoryXField: "name",
                sequencedInterpolation: true,
                calculateAggregates: true,
                maskBullets: false,
                tooltip: am5.Tooltip.new(root, {
                    dy: -30,
                    pointerOrientation: "vertical",
                    labelText: "{valueY}",
                }),
            })
        );
        series.columns.template.setAll({
            strokeOpacity: 0,
            cornerRadiusBR: 10,
            cornerRadiusTR: 10,
            cornerRadiusBL: 10,
            cornerRadiusTL: 10,
            maxWidth: 50,
            fillOpacity: 0.8,
        });

        let currentlyHovered;
        const handleOut = () => {
            if (currentlyHovered) {
                const bullet = currentlyHovered.bullets?.[0];
                if (bullet) {
                    bullet.animate({
                        key: "locationY",
                        to: 0,
                        duration: 600,
                        easing: am5.ease.out(am5.ease.cubic),
                    });
                }
                currentlyHovered = null;
            }
        };
        const handleHover = (dataItem) => {
            if (dataItem && currentlyHovered !== dataItem) {
                handleOut();
                currentlyHovered = dataItem;
                const bullet = dataItem.bullets?.[0];
                if (bullet) {
                    bullet.animate({
                        key: "locationY",
                        to: 1,
                        duration: 600,
                        easing: am5.ease.out(am5.ease.cubic),
                    });
                }
            }
        };

        series.columns.template.events.on("pointerover", (event) => handleHover(event.target.dataItem));
        series.columns.template.events.on("pointerout", handleOut);

        const circleTemplate = am5.Template.new({});
        series.bullets.push((chartRoot) => {
            const bulletContainer = am5.Container.new(chartRoot, {});
            bulletContainer.children.push(
                am5.Circle.new(chartRoot, { radius: 34 }, circleTemplate)
            );
            const maskCircle = bulletContainer.children.push(
                am5.Circle.new(chartRoot, { radius: 27 })
            );
            const imageContainer = bulletContainer.children.push(
                am5.Container.new(chartRoot, { mask: maskCircle })
            );
            imageContainer.children.push(
                am5.Picture.new(chartRoot, {
                    templateField: "pictureSettings",
                    centerX: am5.p50,
                    centerY: am5.p50,
                    width: 60,
                    height: 60,
                })
            );
            return am5.Bullet.new(chartRoot, {
                locationY: 0,
                sprite: bulletContainer,
            });
        });
        series.set("heatRules", [
            {
                dataField: "valueY",
                min: am5.color(0xe5dc36),
                max: am5.color(0x5faa46),
                target: series.columns.template,
                key: "fill",
            },
            {
                dataField: "valueY",
                min: am5.color(0xe5dc36),
                max: am5.color(0x5faa46),
                target: circleTemplate,
                key: "fill",
            },
        ]);
        series.data.setAll(data);
        xAxis.data.setAll(data);
        const cursor = chart.set("cursor", am5xy.XYCursor.new(root, {}));
        cursor.lineX.set("visible", false);
        cursor.lineY.set("visible", false);
        cursor.events.on("cursormoved", () => {
            const dataItem = series.get("tooltip")?.dataItem;
            if (dataItem) {
                handleHover(dataItem);
            } else {
                handleOut();
            }
        });
        series.appear();
        chart.appear(1000, 100);
    }

    renderTenancyTopBroker() {
        const options = {
            series: [{
                name: "Rent Contracts",
                data: (this.state.tenancyTopBroker["y-axis"] || []).map((value) => Number(value || 0)),
            }],
            chart: { height: 200, type: "bar", toolbar: { show: false } },
            colors: ["#EF745C", "#D06257", "#B15052", "#923E4D", "#722B47"],
            plotOptions: { bar: { columnWidth: "40%", distributed: true } },
            dataLabels: { enabled: true },
            legend: { show: false },
            xaxis: {
                categories: this.state.tenancyTopBroker["x-axis"] || [],
                labels: { style: { fontSize: "12px" } },
            },
            noData: { text: "No broker data" },
        };
        this.renderGraph(this.tenancyTopBroker.el, options);
    }

    renderTenancyDuePaid() {
        const options = {
            series: (this.state.tenancyDuePaid["y-axis"] || []).map((value) => Number(value || 0)),
            chart: { type: "pie", height: 300 },
            colors: ["#FF884B", "#64E291"],
            dataLabels: { enabled: false },
            labels: this.state.tenancyDuePaid["x-axis"] || [],
            legend: { position: "bottom" },
            noData: { text: "No invoice data" },
        };
        this.renderGraph(this.tenancyDuePaid.el, options);
    }

    renderMapProperties(div, sessionData) {
        const { am5, am5map, am5themes_Animated, am5geodata_worldLow } = globalThis;
        const root = am5.Root.new(div);
        this.chartRoots.push(root);
        root.setThemes([am5themes_Animated.new(root)]);
        const chart = root.container.children.push(
            am5map.MapChart.new(root, {
                panX: "rotateX",
                panY: "translateY",
                projection: am5map.geoMercator(),
            })
        );
        chart.set("zoomControl", am5map.ZoomControl.new(root, {}));
        const polygonSeries = chart.series.push(
            am5map.MapPolygonSeries.new(root, {
                geoJSON: am5geodata_worldLow,
                exclude: ["AQ"],
            })
        );
        polygonSeries.mapPolygons.template.setAll({ fill: am5.color(0xdadada) });

        const pointSeries = chart.series.push(am5map.ClusteredPointSeries.new(root, {}));
        pointSeries.set("clusteredBullet", (chartRoot) => {
            const container = am5.Container.new(chartRoot, { cursorOverStyle: "pointer" });
            container.children.push(am5.Circle.new(chartRoot, {
                radius: 8,
                tooltipY: 0,
                fill: am5.color(0xff8c00),
            }));
            container.children.push(am5.Circle.new(chartRoot, {
                radius: 12,
                fillOpacity: 0.3,
                tooltipY: 0,
                fill: am5.color(0xff8c00),
            }));
            container.children.push(am5.Circle.new(chartRoot, {
                radius: 16,
                fillOpacity: 0.3,
                tooltipY: 0,
                fill: am5.color(0xff8c00),
            }));
            container.children.push(am5.Label.new(chartRoot, {
                centerX: am5.p50,
                centerY: am5.p50,
                fill: am5.color(0xffffff),
                populateText: true,
                fontSize: "8",
                text: "{value}",
            }));
            container.events.on("click", (event) => {
                pointSeries.zoomToCluster(event.target.dataItem);
            });
            return am5.Bullet.new(chartRoot, { sprite: container });
        });
        pointSeries.bullets.push((chartRoot) => {
            const circle = am5.Circle.new(chartRoot, {
                radius: 6,
                tooltipY: 0,
                fill: am5.color(0xff8c00),
                tooltipText: "{title}",
            });
            return am5.Bullet.new(chartRoot, { sprite: circle });
        });
        for (const location of sessionData || []) {
            const longitude = Number(location.longitude);
            const latitude = Number(location.latitude);
            if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
                continue;
            }
            pointSeries.data.push({
                geometry: { type: "Point", coordinates: [longitude, latitude] },
                title: location.title || "",
            });
        }
        chart.appear(1000, 100);
    }

    renderGraph(element, options) {
        if (!element) {
            return;
        }
        const graph = new globalThis.ApexCharts(element, options);
        this.apexCharts.push(graph);
        graph.render();
    }

    viewProperties(type) {
        const domain = type === "all" ? [] : [["stage", "=", type]];
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: this.getPropertyName(type),
            res_model: "property.details",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            target: "current",
            context: { create: false },
            domain,
        });
    }

    viewPartner(type) {
        const name = type === "customer" ? "Customers" : "Landlords";
        return this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "res.partner",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            target: "current",
            context: { create: false },
            domain: [["user_type", "=", type]],
        });
    }

    viewPropertyTenancies(type) {
        let domain;
        let model;
        if (type === "rent_total") {
            domain = ["|", ["type", "=", "rent"], ["type", "=", "full_rent"]];
            model = "rent.invoice";
        } else if (type === "not_paid") {
            domain = [["payment_state", "=", "not_paid"]];
            model = "rent.invoice";
        } else if (type === "extend_contract") {
            model = "tenancy.details";
            domain = [["is_extended", "=", true]];
        } else {
            model = "tenancy.details";
            domain = [["contract_type", "=", type]];
        }
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: this.getPropertyName(type),
            res_model: model,
            views: [[false, "list"], [false, "form"]],
            target: "current",
            context: { create: false },
            domain,
        });
    }

    viewStatistic(type) {
        const definitions = {
            region: ["Regions", "property.region"],
            project: ["Projects", "property.project"],
            sub_project: ["Sub Projects", "property.sub.project"],
        };
        const [name, model] = definitions[type] || ["Statistics", "property.details"];
        return this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: model,
            views: [[false, "list"], [false, "form"]],
            target: "current",
            context: { create: false },
        });
    }

    getPropertyName(type) {
        return {
            all: "All Properties",
            booked: "Booked Properties",
            sale: "On Sale Properties",
            on_lease: "On Leased Properties",
            sold: "Sold Properties",
            available: "Available Properties",
            sold_total: "Sold Properties Total",
            new_contract: "Draft Contract",
            running_contract: "Running Contract",
            expire_contract: "Expire Contract",
            rent_total: "Total Rent Amount",
            not_paid: "Pending Invoice",
            close_contract: "Close Contracts",
            extend_contract: "Extended Contracts",
            refund: "Refunded Sale Contracts",
        }[type] || "Properties";
    }
}

registry.category("actions").add("property_dashboard", RentalDashboard);
