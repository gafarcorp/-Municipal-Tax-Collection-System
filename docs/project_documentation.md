# Municipal Tax Collection System

## 1. Project Overview

This is a beginner-friendly full-stack college mini project built using:

- Frontend: HTML, CSS, JavaScript, Bootstrap
- Backend: Python Flask
- Database: MySQL (XAMPP compatible)

The system helps a municipality manage taxpayers, register properties, calculate annual tax, accept online payments, and apply late penalties.

## 2. Folder Structure

```text
Municipal Tax Collection System/
├── app.py
├── config.py
├── db.py
├── requirements.txt
├── database/
│   └── municipal_tax_collection.sql
├── docs/
│   └── project_documentation.md
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── app.js
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── history.html
    ├── login.html
    ├── payment.html
    ├── properties.html
    └── register.html
```

## 3. Modules Explanation

### 3.1 Taxpayer Management

- Taxpayer registration is available from the register page.
- Login supports taxpayer and admin roles.
- Session-based authentication is used in Flask.
- Taxpayer email is unique to avoid duplicate accounts.

### 3.2 Property Tax Assessment

- Admin can add, update, and delete properties.
- Each property is linked to one taxpayer.
- Property code is unique, so duplicate property entries are prevented.
- A stored procedure calculates annual property tax automatically.

### 3.3 Tax Payment Processing

- Tax records are displayed in the tax payment page.
- Users can select an unpaid or partially paid tax entry and submit payment.
- Payment history is saved with payment reference, method, amount, and date.

### 3.4 Fine / Penalty Calculation

- Late payment penalty is calculated at 2% of base tax for every 30 days of delay.
- Penalty is handled in the database using a trigger before payment insertion.
- Flask also calculates current penalty to show updated values in the user interface.

### 3.5 Report Generation

- Admin dashboard shows counts, collections, and recent payments.
- A database view is used for the collection report.
- Monthly payment summary is returned through the report API.

## 4. Database Design

### 4.1 Main Tables

#### Taxpayer

- `id` as primary key
- `email` as unique field
- Stores taxpayer profile and password hash

#### Property

- `id` as primary key
- `taxpayer_id` as foreign key
- `property_code` as unique field
- Stores property size, type, address, and value

#### Tax

- `id` as primary key
- `property_id` as foreign key
- Unique combination of `property_id + tax_year`
- Stores base tax, penalty, due amount, due date, and status

#### Payment

- `id` as primary key
- `tax_id` and `taxpayer_id` as foreign keys
- `payment_reference` as unique field
- Stores payment amount, method, timestamp, and payment status

#### Admin

- `id` as primary key
- `username` as unique field
- Stores admin login credentials

### 4.2 Relationships

- One taxpayer can own many properties.
- One property can have many yearly tax records.
- One tax record can have many payment records.
- One taxpayer can make many payments.

### 4.3 Constraints

- Primary keys on all tables
- Foreign keys for table relationships
- `NOT NULL` on required fields
- `UNIQUE` on taxpayer email, admin username, property code, and payment reference
- Check constraints on area, property value, and payment amount

### 4.4 Indexing

Indexes are created on:

- taxpayer email
- property taxpayer mapping
- tax property and status
- payment taxpayer and payment date
- payment tax id

### 4.5 Trigger

`trg_before_payment_insert_penalty`

- Checks whether tax due date has already passed
- Calculates penalty before payment is inserted
- Updates `penalty_amount` and `total_due` in the tax table

`trg_after_payment_insert_update_tax`

- Calculates how much has been paid for a tax entry
- Sets tax status to `UNPAID`, `PARTIAL`, or `PAID`

### 4.6 View

`vw_tax_collection_report`

- Combines taxpayer, property, tax, and payment data
- Helps the admin dashboard and reports module

### 4.7 Stored Procedure

`sp_generate_property_tax`

- Reads property details
- Applies a tax formula based on value, area, and property type
- Inserts or updates the yearly tax record

## 5. ER Diagram Explanation in Text Form

The entity relationship design is:

- Taxpayer (1) → (M) Property
- Property (1) → (M) Tax
- Tax (1) → (M) Payment
- Taxpayer (1) → (M) Payment
- Admin is independent and only used for system administration

This means each citizen can own multiple properties, each property can generate multiple yearly taxes, and each tax can be paid in one or more transactions.

## 6. Business Logic

### Tax Formula

```text
Base Tax = (Property Value × 1%) + (Area in sq.ft × 2)

Residential = Base Tax × 1.00
Commercial  = Base Tax × 1.20
Industrial  = Base Tax × 1.35
```

### Penalty Formula

```text
Penalty = Base Tax × 2% × Number of delayed 30-day periods
```

## 7. REST API Summary

### Authentication APIs

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/session`

### Dashboard API

- `GET /api/dashboard/summary`

### Property APIs

- `GET /api/properties`
- `POST /api/properties`
- `PUT /api/properties/<id>`
- `DELETE /api/properties/<id>`

### Tax and Payment APIs

- `GET /api/taxes`
- `POST /api/payments`
- `GET /api/payments/history`

### Report API

- `GET /api/reports/collection`

## 8. Step-by-Step Setup

### Step 1: Start XAMPP

- Start Apache
- Start MySQL

### Step 2: Create Database

- Open phpMyAdmin
- Import `database/municipal_tax_collection.sql`

### Step 3: Install Python Packages

```bash
pip install -r requirements.txt
```

### Step 4: Configure Database

Default database values in `config.py` are:

- Host: `localhost`
- Port: `3306`
- User: `root`
- Password: empty string
- Database: `municipal_tax_collection`

Change these values if your MySQL setup is different.

### Step 5: Run Flask Project

```bash
flask --app app run
```

Or:

```bash
python app.py
```

### Step 6: Open Browser

Visit:

```text
http://127.0.0.1:5000
```

## 9. Sample Login Details

### Admin

- Username: `admin`
- Password: `admin123`

### Taxpayer

- Email: `gafar@example.com`
- Password: `user123`

## 10. Testing Cases and Expected Outputs

| Test Case | Input / Action | Expected Output |
|---|---|---|
| Register taxpayer | Enter new taxpayer details | New record created and success message shown |
| Duplicate taxpayer email | Register with same email twice | Error message: email already exists |
| Admin login | `admin / admin123` | Admin redirected to dashboard |
| Invalid login | Wrong password | Error message for invalid credentials |
| Add property | Admin adds unique property code | Property saved and yearly tax generated |
| Duplicate property | Admin uses same property code again | Error message for duplicate property code |
| View taxes | Taxpayer opens payment page | Tax list with base tax, penalty, paid amount, and balance |
| Late payment | Pay overdue tax | Trigger updates penalty before payment insertion |
| Partial payment | Pay less than balance | Tax status changes to PARTIAL |
| Full payment | Pay complete remaining balance | Tax status changes to PAID |
| Payment history | Open history page | Previous payment records displayed |
| Report generation | Admin loads reports | Monthly collection summary displayed |

## 11. Notes for Viva / Presentation

- The project uses both backend logic and database logic.
- Tax is generated using a stored procedure.
- Penalty is generated using MySQL triggers.
- Reports use a SQL view.
- The system follows a simple, beginner-friendly design suitable for mini projects.
