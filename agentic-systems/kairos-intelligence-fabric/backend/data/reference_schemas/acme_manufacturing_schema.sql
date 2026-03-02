-- ============================================================================
-- ACME Industrial Manufacturing — Master Database Schema
-- Database: PostgreSQL 15+
-- Version: 2.4.0
-- Last Updated: 2026-01-15
-- ============================================================================

-- ============================================================================
-- DOMAIN: HUMAN RESOURCES
-- ============================================================================

CREATE TABLE employees (
    employee_id       SERIAL PRIMARY KEY,
    employee_code     VARCHAR(20)  NOT NULL UNIQUE,           -- e.g. 'EMP-0042'
    first_name        VARCHAR(60)  NOT NULL,
    last_name         VARCHAR(60)  NOT NULL,
    email             VARCHAR(120) UNIQUE,
    department        VARCHAR(40)  NOT NULL,                  -- Engineering, Production, Quality, Maintenance, Supply Chain, Safety
    job_title         VARCHAR(80),
    hire_date         DATE         NOT NULL,
    certification     VARCHAR(120),                           -- e.g. 'AWS D1.1 Certified Welder', 'CNC Level III'
    shift_default     SMALLINT     CHECK (shift_default IN (1, 2, 3)),
    is_active         BOOLEAN      DEFAULT TRUE,
    created_at        TIMESTAMPTZ  DEFAULT now()
);
COMMENT ON TABLE employees IS 'All ACME Industrial Manufacturing employees across both Ohio plants. Includes operators, engineers, maintenance techs, and administrative staff (~800 total).';

-- ============================================================================
-- DOMAIN: SALES
-- ============================================================================

CREATE TABLE customers (
    customer_id       SERIAL PRIMARY KEY,
    customer_code     VARCHAR(20)  NOT NULL UNIQUE,           -- e.g. 'CUST-1001'
    company_name      VARCHAR(150) NOT NULL,
    contact_name      VARCHAR(120),
    contact_email     VARCHAR(120),
    phone             VARCHAR(30),
    address_line1     VARCHAR(200),
    city              VARCHAR(80),
    state             CHAR(2),
    zip               VARCHAR(10),
    payment_terms     VARCHAR(30)  DEFAULT 'Net 30',          -- Net 30, Net 45, Net 60, COD
    credit_limit      NUMERIC(12,2),
    is_active         BOOLEAN      DEFAULT TRUE,
    created_at        TIMESTAMPTZ  DEFAULT now()
);
COMMENT ON TABLE customers IS 'Customer master for ACME. Includes aerospace, automotive, and industrial OEM accounts.';

CREATE TABLE sales_orders (
    order_id          SERIAL PRIMARY KEY,
    order_number      VARCHAR(20)  NOT NULL UNIQUE,           -- e.g. 'SO-2026-0001'
    customer_id       INTEGER      NOT NULL REFERENCES customers(customer_id),
    order_date        DATE         NOT NULL,
    required_date     DATE         NOT NULL,
    promised_date     DATE,
    status            VARCHAR(20)  NOT NULL DEFAULT 'Open',   -- Open, In Production, Shipped, Closed, Cancelled
    priority          SMALLINT     DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),  -- 1=Critical, 5=Low
    total_amount      NUMERIC(12,2),
    notes             TEXT,
    created_by        INTEGER      REFERENCES employees(employee_id),
    created_at        TIMESTAMPTZ  DEFAULT now()
);

CREATE TABLE order_lines (
    line_id           SERIAL PRIMARY KEY,
    order_id          INTEGER      NOT NULL REFERENCES sales_orders(order_id),
    line_number       SMALLINT     NOT NULL,
    product_id        INTEGER      NOT NULL,  -- FK added after products table
    quantity          INTEGER      NOT NULL CHECK (quantity > 0),
    unit_price        NUMERIC(10,2) NOT NULL,
    discount_pct      NUMERIC(5,2) DEFAULT 0,
    line_status       VARCHAR(20)  DEFAULT 'Pending',         -- Pending, Released, Complete, Cancelled
    UNIQUE (order_id, line_number)
);

-- ============================================================================
-- DOMAIN: ENGINEERING / BOM
-- ============================================================================

CREATE TABLE products (
    product_id        SERIAL PRIMARY KEY,
    product_code      VARCHAR(30)  NOT NULL UNIQUE,           -- e.g. 'GEAR-ASSY-100'
    product_name      VARCHAR(150) NOT NULL,
    product_family    VARCHAR(60),                            -- Precision Gears, Hydraulic Components, Custom Brackets, Actuators
    unit_of_measure   VARCHAR(10)  DEFAULT 'EA',              -- EA, KG, M
    standard_cost     NUMERIC(10,2),
    lead_time_days    INTEGER,
    weight_kg         NUMERIC(8,3),
    drawing_number    VARCHAR(40),
    revision          VARCHAR(10)  DEFAULT 'A',
    is_active         BOOLEAN      DEFAULT TRUE,
    created_at        TIMESTAMPTZ  DEFAULT now()
);
COMMENT ON TABLE products IS 'Finished goods catalog. Main families: Precision Gear Assemblies, Hydraulic Actuator Blocks, Custom Mounting Brackets.';

ALTER TABLE order_lines
    ADD CONSTRAINT fk_order_lines_product FOREIGN KEY (product_id) REFERENCES products(product_id);

CREATE TABLE components (
    component_id      SERIAL PRIMARY KEY,
    component_code    VARCHAR(30)  NOT NULL UNIQUE,           -- e.g. 'STEEL-4140-ROD'
    component_name    VARCHAR(150) NOT NULL,
    component_type    VARCHAR(30)  NOT NULL,                  -- Raw Material, Purchased Part, Sub-Assembly, Consumable
    material_spec     VARCHAR(80),                            -- e.g. 'AISI 4140', 'AL 6061-T6', 'Brass C360'
    unit_of_measure   VARCHAR(10)  DEFAULT 'EA',
    standard_cost     NUMERIC(10,2),
    reorder_point     INTEGER,
    is_active         BOOLEAN      DEFAULT TRUE,
    created_at        TIMESTAMPTZ  DEFAULT now()
);

CREATE TABLE bom_headers (
    bom_id            SERIAL PRIMARY KEY,
    product_id        INTEGER      NOT NULL REFERENCES products(product_id),
    bom_revision      VARCHAR(10)  NOT NULL DEFAULT 'A',
    effective_date    DATE         NOT NULL,
    expiration_date   DATE,
    status            VARCHAR(20)  DEFAULT 'Active',          -- Draft, Active, Obsolete
    approved_by       INTEGER      REFERENCES employees(employee_id),
    created_at        TIMESTAMPTZ  DEFAULT now(),
    UNIQUE (product_id, bom_revision)
);

CREATE TABLE bom_details (
    bom_detail_id     SERIAL PRIMARY KEY,
    bom_id            INTEGER      NOT NULL REFERENCES bom_headers(bom_id),
    component_id      INTEGER      NOT NULL REFERENCES components(component_id),
    quantity_per       NUMERIC(10,4) NOT NULL,
    unit_of_measure   VARCHAR(10)  DEFAULT 'EA',
    scrap_factor_pct  NUMERIC(5,2) DEFAULT 0,                -- Expected scrap % for this component
    reference_designator VARCHAR(30),                         -- Position or operation reference
    notes             TEXT
);

-- ============================================================================
-- DOMAIN: SUPPLY CHAIN
-- ============================================================================

CREATE TABLE suppliers (
    supplier_id       SERIAL PRIMARY KEY,
    supplier_code     VARCHAR(20)  NOT NULL UNIQUE,           -- e.g. 'SUPP-001'
    supplier_name     VARCHAR(150) NOT NULL,
    contact_name      VARCHAR(120),
    contact_email     VARCHAR(120),
    phone             VARCHAR(30),
    city              VARCHAR(80),
    state             CHAR(2),
    rating            CHAR(1)      CHECK (rating IN ('A', 'B', 'C', 'D')),  -- A=Preferred, D=Probation
    iso_certified     BOOLEAN      DEFAULT FALSE,
    lead_time_days    INTEGER,
    on_time_delivery_pct NUMERIC(5,2),
    is_active         BOOLEAN      DEFAULT TRUE,
    created_at        TIMESTAMPTZ  DEFAULT now()
);
COMMENT ON TABLE suppliers IS 'Approved vendor list. Rating: A=Preferred, B=Approved, C=Conditional, D=Probation. ISO 9001 certification tracked.';

CREATE TABLE purchase_orders (
    po_id             SERIAL PRIMARY KEY,
    po_number         VARCHAR(20)  NOT NULL UNIQUE,           -- e.g. 'PO-2026-0150'
    supplier_id       INTEGER      NOT NULL REFERENCES suppliers(supplier_id),
    component_id      INTEGER      NOT NULL REFERENCES components(component_id),
    quantity          INTEGER      NOT NULL CHECK (quantity > 0),
    unit_cost         NUMERIC(10,2) NOT NULL,
    order_date        DATE         NOT NULL,
    expected_date     DATE,
    received_date     DATE,
    received_qty      INTEGER,
    status            VARCHAR(20)  DEFAULT 'Open',            -- Open, Partial, Received, Closed, Cancelled
    created_by        INTEGER      REFERENCES employees(employee_id),
    created_at        TIMESTAMPTZ  DEFAULT now()
);

CREATE TABLE inventory (
    inventory_id      SERIAL PRIMARY KEY,
    component_id      INTEGER      NOT NULL REFERENCES components(component_id),
    warehouse_code    VARCHAR(10)  NOT NULL,                  -- PLANT-1, PLANT-2, WIP
    location_bin      VARCHAR(20),                            -- e.g. 'A-03-12'
    quantity_on_hand  INTEGER      NOT NULL DEFAULT 0,
    quantity_reserved INTEGER      DEFAULT 0,
    quantity_available INTEGER     GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
    last_count_date   DATE,
    updated_at        TIMESTAMPTZ  DEFAULT now(),
    UNIQUE (component_id, warehouse_code, location_bin)
);

-- ============================================================================
-- DOMAIN: PRODUCTION
-- ============================================================================

CREATE TABLE production_lines (
    line_id           SERIAL PRIMARY KEY,
    line_code         VARCHAR(20)  NOT NULL UNIQUE,           -- e.g. 'LINE-CNC-01'
    line_name         VARCHAR(80)  NOT NULL,                  -- e.g. 'CNC Machining Cell A'
    plant             VARCHAR(20)  NOT NULL,                  -- Plant 1 - Dayton, Plant 2 - Columbus
    line_type         VARCHAR(30),                            -- CNC Machining, Assembly, Welding, Coating
    capacity_per_shift INTEGER,
    is_active         BOOLEAN      DEFAULT TRUE
);

CREATE TABLE work_centers (
    work_center_id    SERIAL PRIMARY KEY,
    work_center_code  VARCHAR(20)  NOT NULL UNIQUE,           -- e.g. 'WC-TURN-01'
    work_center_name  VARCHAR(80)  NOT NULL,
    line_id           INTEGER      REFERENCES production_lines(line_id),
    operation_type    VARCHAR(40),                            -- Turning, Milling, Grinding, Assembly, Welding, Coating, Inspection
    hourly_rate       NUMERIC(8,2),                           -- Cost per hour
    setup_time_min    INTEGER,                                -- Standard setup time in minutes
    is_active         BOOLEAN      DEFAULT TRUE
);

CREATE TABLE work_orders (
    work_order_id     SERIAL PRIMARY KEY,
    work_order_number VARCHAR(20)  NOT NULL UNIQUE,           -- e.g. 'WO-2026-00345'
    order_line_id     INTEGER      REFERENCES order_lines(line_id),
    product_id        INTEGER      NOT NULL REFERENCES products(product_id),
    line_id           INTEGER      REFERENCES production_lines(line_id),
    planned_qty       INTEGER      NOT NULL,
    completed_qty     INTEGER      DEFAULT 0,
    scrap_qty         INTEGER      DEFAULT 0,
    planned_start     DATE,
    planned_end       DATE,
    actual_start      DATE,
    actual_end        DATE,
    status            VARCHAR(20)  DEFAULT 'Planned',         -- Planned, Released, In Progress, Complete, On Hold, Cancelled
    priority          SMALLINT     DEFAULT 3,
    created_at        TIMESTAMPTZ  DEFAULT now()
);

CREATE TABLE work_order_operations (
    operation_id      SERIAL PRIMARY KEY,
    work_order_id     INTEGER      NOT NULL REFERENCES work_orders(work_order_id),
    operation_seq     SMALLINT     NOT NULL,                  -- 10, 20, 30 ...
    work_center_id    INTEGER      NOT NULL REFERENCES work_centers(work_center_id),
    operation_name    VARCHAR(80)  NOT NULL,                  -- e.g. 'Rough Turning', 'Finish Milling'
    setup_time_min    INTEGER,
    run_time_min      INTEGER,                                -- Per unit
    status            VARCHAR(20)  DEFAULT 'Pending',         -- Pending, In Progress, Complete, Skipped
    actual_start      TIMESTAMPTZ,
    actual_end        TIMESTAMPTZ,
    operator_id       INTEGER      REFERENCES employees(employee_id),
    UNIQUE (work_order_id, operation_seq)
);

-- ============================================================================
-- DOMAIN: EQUIPMENT & MAINTENANCE
-- ============================================================================

CREATE TABLE equipment (
    equipment_id      SERIAL PRIMARY KEY,
    equipment_code    VARCHAR(30)  NOT NULL UNIQUE,           -- e.g. 'CNC-LATHE-01'
    equipment_name    VARCHAR(100) NOT NULL,
    equipment_type    VARCHAR(40)  NOT NULL,                  -- CNC Lathe, CNC Mill, Welding Robot, Coating Line, CMM
    manufacturer      VARCHAR(80),
    model_number      VARCHAR(60),
    serial_number     VARCHAR(60),
    line_id           INTEGER      REFERENCES production_lines(line_id),
    install_date      DATE,
    last_pm_date      DATE,                                   -- Last preventive maintenance
    next_pm_date      DATE,
    status            VARCHAR(20)  DEFAULT 'Operational',     -- Operational, Degraded, Down, Decommissioned
    criticality       CHAR(1)      CHECK (criticality IN ('A', 'B', 'C')),  -- A=Critical, C=Low
    created_at        TIMESTAMPTZ  DEFAULT now()
);
COMMENT ON TABLE equipment IS 'Equipment registry for CNC machines, welding robots, coating lines, and inspection systems across both ACME plants.';

CREATE TABLE maintenance_work_orders (
    maint_wo_id       SERIAL PRIMARY KEY,
    maint_wo_number   VARCHAR(20)  NOT NULL UNIQUE,           -- e.g. 'MWO-2026-0089'
    equipment_id      INTEGER      NOT NULL REFERENCES equipment(equipment_id),
    maint_type        VARCHAR(20)  NOT NULL,                  -- Preventive, Corrective, Predictive, Emergency
    description       TEXT         NOT NULL,
    priority          SMALLINT     DEFAULT 3,
    reported_by       INTEGER      REFERENCES employees(employee_id),
    assigned_to       INTEGER      REFERENCES employees(employee_id),
    scheduled_date    DATE,
    completed_date    DATE,
    downtime_minutes  INTEGER,
    root_cause        TEXT,
    corrective_action TEXT,
    parts_used        TEXT,                                    -- JSON array of component_ids and quantities
    status            VARCHAR(20)  DEFAULT 'Open',            -- Open, In Progress, Complete, Cancelled
    created_at        TIMESTAMPTZ  DEFAULT now()
);

-- ============================================================================
-- DOMAIN: QUALITY
-- ============================================================================

CREATE TABLE quality_inspections (
    inspection_id     SERIAL PRIMARY KEY,
    work_order_id     INTEGER      REFERENCES work_orders(work_order_id),
    equipment_id      INTEGER      REFERENCES equipment(equipment_id),
    inspection_type   VARCHAR(30)  NOT NULL,                  -- Incoming, In-Process, Final, First Article
    inspection_date   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    inspector_id      INTEGER      REFERENCES employees(employee_id),
    sample_size       INTEGER,
    pass_count        INTEGER,
    fail_count        INTEGER,
    result            VARCHAR(10)  NOT NULL,                  -- Pass, Fail, Conditional
    notes             TEXT,
    created_at        TIMESTAMPTZ  DEFAULT now()
);

CREATE TABLE defect_records (
    defect_id         SERIAL PRIMARY KEY,
    inspection_id     INTEGER      REFERENCES quality_inspections(inspection_id),
    work_order_id     INTEGER      REFERENCES work_orders(work_order_id),
    product_id        INTEGER      REFERENCES products(product_id),
    defect_type       VARCHAR(40)  NOT NULL,                  -- Dimensional, Surface Finish, Porosity, Crack, Burr, Cosmetic, Material
    severity          VARCHAR(10)  NOT NULL,                  -- Critical, Major, Minor
    defect_count      INTEGER      DEFAULT 1,
    root_cause        VARCHAR(60),                            -- Tooling Wear, Operator Error, Material Defect, Setup Error, Machine Drift
    disposition       VARCHAR(20),                            -- Rework, Scrap, Use As-Is, Return to Vendor
    corrective_action TEXT,
    detected_date     DATE         NOT NULL,
    created_at        TIMESTAMPTZ  DEFAULT now()
);

CREATE TABLE spc_measurements (
    measurement_id    SERIAL PRIMARY KEY,
    equipment_id      INTEGER      REFERENCES equipment(equipment_id),
    product_id        INTEGER      REFERENCES products(product_id),
    work_order_id     INTEGER      REFERENCES work_orders(work_order_id),
    characteristic    VARCHAR(80)  NOT NULL,                  -- e.g. 'Bore Diameter', 'Surface Roughness Ra'
    nominal_value     NUMERIC(12,6) NOT NULL,
    upper_spec_limit  NUMERIC(12,6) NOT NULL,
    lower_spec_limit  NUMERIC(12,6) NOT NULL,
    measured_value    NUMERIC(12,6) NOT NULL,
    measurement_unit  VARCHAR(10)  NOT NULL,                  -- mm, μm, Ra, Rz
    in_spec           BOOLEAN      GENERATED ALWAYS AS (measured_value BETWEEN lower_spec_limit AND upper_spec_limit) STORED,
    measured_by       INTEGER      REFERENCES employees(employee_id),
    measured_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);
COMMENT ON TABLE spc_measurements IS 'Statistical Process Control measurement data. Used for CPK calculations and control chart analysis.';

-- ============================================================================
-- DOMAIN: SHIPPING
-- ============================================================================

CREATE TABLE shipments (
    shipment_id       SERIAL PRIMARY KEY,
    shipment_number   VARCHAR(20)  NOT NULL UNIQUE,           -- e.g. 'SHIP-2026-0200'
    order_id          INTEGER      NOT NULL REFERENCES sales_orders(order_id),
    ship_date         DATE         NOT NULL,
    carrier           VARCHAR(60),                            -- UPS, FedEx, LTL Carrier, Customer Pickup
    tracking_number   VARCHAR(60),
    weight_kg         NUMERIC(8,2),
    freight_cost      NUMERIC(10,2),
    status            VARCHAR(20)  DEFAULT 'Pending',         -- Pending, Shipped, In Transit, Delivered, Returned
    delivered_date    DATE,
    created_at        TIMESTAMPTZ  DEFAULT now()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_sales_orders_customer    ON sales_orders(customer_id);
CREATE INDEX idx_sales_orders_status      ON sales_orders(status);
CREATE INDEX idx_order_lines_product      ON order_lines(product_id);
CREATE INDEX idx_work_orders_product      ON work_orders(product_id);
CREATE INDEX idx_work_orders_status       ON work_orders(status);
CREATE INDEX idx_work_orders_line         ON work_orders(line_id);
CREATE INDEX idx_maint_wo_equipment       ON maintenance_work_orders(equipment_id);
CREATE INDEX idx_maint_wo_status          ON maintenance_work_orders(status);
CREATE INDEX idx_quality_insp_wo          ON quality_inspections(work_order_id);
CREATE INDEX idx_defects_product          ON defect_records(product_id);
CREATE INDEX idx_spc_equipment            ON spc_measurements(equipment_id);
CREATE INDEX idx_spc_product              ON spc_measurements(product_id);
CREATE INDEX idx_purchase_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_inventory_component      ON inventory(component_id);
CREATE INDEX idx_equipment_line           ON equipment(line_id);
CREATE INDEX idx_shipments_order          ON shipments(order_id);

-- ============================================================================
-- BUSINESS VIEWS
-- ============================================================================

-- View: Order fulfillment status with on-time delivery tracking
CREATE OR REPLACE VIEW vw_order_fulfillment AS
SELECT
    so.order_number,
    c.company_name                                         AS customer,
    so.order_date,
    so.required_date,
    so.promised_date,
    sh.ship_date,
    sh.delivered_date,
    so.status                                              AS order_status,
    sh.status                                              AS shipment_status,
    CASE
        WHEN sh.ship_date IS NULL                THEN 'Not Shipped'
        WHEN sh.ship_date <= so.required_date    THEN 'On Time'
        ELSE 'Late'
    END                                                    AS otd_status,
    so.total_amount
FROM sales_orders so
JOIN customers c          ON c.customer_id  = so.customer_id
LEFT JOIN shipments sh    ON sh.order_id    = so.order_id;

COMMENT ON VIEW vw_order_fulfillment IS 'Order fulfillment pipeline with on-time delivery (OTD) classification. Used by Sales and Operations for KPI dashboards.';

-- View: Production yield and scrap summary by product and line
CREATE OR REPLACE VIEW vw_production_yield AS
SELECT
    wo.work_order_number,
    p.product_code,
    p.product_name,
    pl.line_name,
    wo.planned_qty,
    wo.completed_qty,
    wo.scrap_qty,
    CASE WHEN wo.planned_qty > 0
         THEN ROUND(100.0 * wo.completed_qty / wo.planned_qty, 2)
         ELSE 0 END                                        AS yield_pct,
    CASE WHEN (wo.completed_qty + wo.scrap_qty) > 0
         THEN ROUND(100.0 * wo.scrap_qty / (wo.completed_qty + wo.scrap_qty), 2)
         ELSE 0 END                                        AS scrap_pct,
    wo.status,
    wo.actual_start,
    wo.actual_end
FROM work_orders wo
JOIN products p           ON p.product_id  = wo.product_id
LEFT JOIN production_lines pl ON pl.line_id = wo.line_id;

COMMENT ON VIEW vw_production_yield IS 'Work order yield and scrap analysis. Supports scrap <2% target and first-pass yield tracking.';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
