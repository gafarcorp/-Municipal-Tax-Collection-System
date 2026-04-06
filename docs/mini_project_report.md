# MINI PROJECT REPORT

## 1. Title

**Municipal Tax Collection System**

Submitted in partial fulfillment of the requirements for the mini project.

**Prepared By:**  
- Name: ____________________  
- Roll Number: ____________________  
- Class / Semester: ____________________  

**Submitted To:**  
- Guide Name: ____________________  
- Department: ____________________  
- College Name: ____________________  

## 2. Index

1. Title  
2. Index  
3. Introduction  
4. Objectives of the Project  
5. System Overview  
6. Technologies Used  
7. System Architecture  
8. Database Description  
9. Implementation / Module Description  
10. Output Screenshots  
11. Testing and Results  
12. Conclusion  

## 3. Introduction

The **Municipal Tax Collection System** is a web-based application developed to simplify the process of managing municipal property tax operations. In many local government offices, tax records are often maintained manually or through disconnected tools, which can lead to calculation mistakes, delayed payments, difficulty in tracking records, and poor reporting.

This project provides a simple and beginner-friendly digital solution for managing taxpayers, registering properties, generating tax assessments, processing payments, calculating late penalties, and generating administrative reports. The system includes a frontend for user interaction, a Flask backend for handling business logic, and a MySQL database for secure and structured data storage.

The project is designed especially as a **college mini project**, so the code structure, logic, and interface remain easy to understand while still covering important full-stack development concepts such as authentication, CRUD operations, REST APIs, database triggers, stored procedures, and reports.

## 4. Objectives of the Project

The main objectives of this project are:

- To develop a web application for municipal tax management.
- To maintain taxpayer and property records in a structured database.
- To automate annual tax calculation based on property details.
- To provide an online payment recording system for tax collection.
- To calculate penalties automatically for late payments.
- To prevent duplicate property registration in the system.
- To allow administrators to monitor tax collection and generate reports.
- To create a simple and user-friendly system suitable for academic demonstration.

## 5. System Overview

The Municipal Tax Collection System consists of two main user roles:

### Admin

- Admin can log in to the system.
- Admin can add, update, and delete property records.
- Admin can monitor taxpayer records and overall collections.
- Admin can view recent payments and collection summaries.
- Admin can generate reports using database views and dashboard APIs.

### Taxpayer

- Taxpayer can register a new account.
- Taxpayer can log in securely.
- Taxpayer can view registered properties linked to the account.
- Taxpayer can check tax details, total due amount, and penalties.
- Taxpayer can make payments and view payment history.

### Main Functional Flow

1. Taxpayer registers and logs in.
2. Admin registers property details for the taxpayer.
3. The system calculates yearly tax using property data.
4. If payment is late, the database trigger adds a penalty.
5. Payment is recorded and tax status is updated.
6. Admin views reports and monitors tax collection.

## 6. Technologies Used

### Frontend

- HTML
- CSS
- JavaScript
- Bootstrap 5

### Backend

- Python
- Flask

### Database

- MySQL
- XAMPP phpMyAdmin

### Development Tools

- VS Code / Trae IDE
- Browser for testing
- MySQL via XAMPP

## 7. System Architecture

The application follows a simple **three-layer architecture**:

### 1. Presentation Layer

This layer contains the user interface pages built using HTML, CSS, JavaScript, and Bootstrap.

Main pages:

- Login / Register Page
- Dashboard
- Property Details
- Tax Payment
- Payment History

### 2. Application Layer

This layer is built using Flask. It handles:

- Authentication and session management
- REST API requests and responses
- Tax calculation logic
- Payment validation
- Report generation logic

### 3. Data Layer

This layer uses MySQL to store and manage:

- Taxpayer information
- Admin details
- Property records
- Tax records
- Payment history
- Penalty calculation logic through triggers

### Architecture Flow

```text
User Interface (HTML/CSS/JS/Bootstrap)
            ↓
      Flask Backend APIs
            ↓
         MySQL Database
```

## 8. Database Description

The database used in this project is `municipal_tax_collection`.

### Main Tables

#### 1. Taxpayer

Stores taxpayer registration details.

Fields:

- id
- full_name
- email
- phone
- address
- password_hash
- created_at

#### 2. Admin

Stores admin login details.

Fields:

- id
- username
- full_name
- password_hash
- created_at

#### 3. Property

Stores registered property details.

Fields:

- id
- taxpayer_id
- property_code
- property_type
- address
- area_sqft
- property_value
- created_at

#### 4. Tax

Stores yearly property tax details.

Fields:

- id
- property_id
- tax_year
- base_tax
- penalty_amount
- total_due
- due_date
- status
- generated_at

#### 5. Payment

Stores payment transaction records.

Fields:

- id
- tax_id
- taxpayer_id
- amount_paid
- payment_method
- payment_reference
- payment_status
- paid_at

### Relationships

- One taxpayer can own many properties.
- One property can have many yearly tax records.
- One tax record can have many payment records.
- One taxpayer can make many payments.

### Constraints Used

- Primary Key
- Foreign Key
- NOT NULL
- UNIQUE
- CHECK constraints

### Indexing

Indexes are created to improve performance for:

- taxpayer email search
- property to taxpayer mapping
- tax status lookup
- payment history lookup

### Trigger Used

**Trigger Name:** `trg_before_payment_insert_penalty`

Purpose:

- Automatically calculates penalty if tax payment is made after due date.
- Updates the `penalty_amount` and `total_due` in the tax table.

### Second Trigger

**Trigger Name:** `trg_after_payment_insert_update_tax`

Purpose:

- Updates tax status to `UNPAID`, `PARTIAL`, or `PAID` after payment entry.

### Stored Procedure

**Procedure Name:** `sp_generate_property_tax`

Purpose:

- Calculates annual tax based on property value, area, and property type.
- Creates or updates yearly tax record automatically.

### View Used

**View Name:** `vw_tax_collection_report`

Purpose:

- Provides combined data for reports using taxpayer, property, tax, and payment details.

### ER Description

```text
Taxpayer (1) ----- (M) Property
Property  (1) ----- (M) Tax
Tax       (1) ----- (M) Payment
Taxpayer  (1) ----- (M) Payment
Admin table works independently for system administration.
```

## 9. Implementation / Module Description

### 9.1 Taxpayer Management Module

This module handles taxpayer registration and login.

Functions:

- Register new taxpayers
- Validate unique email
- Login using email and password
- Maintain user session
- Logout from system

### 9.2 Property Management Module

This module is used by the admin.

Functions:

- Add property details
- Update property records
- Delete property records
- Link property to a taxpayer
- Prevent duplicate property entries using unique property code

### 9.3 Property Tax Assessment Module

This module generates tax amount based on property details.

Formula used:

```text
Base Tax = (Property Value × 1%) + (Area × 2)

Residential = Base Tax × 1.00
Commercial  = Base Tax × 1.20
Industrial  = Base Tax × 1.35
```

### 9.4 Tax Payment Module

This module manages tax payments.

Functions:

- View pending taxes
- Select tax record for payment
- Record payment method and amount
- Generate payment reference
- Update paid amount and tax status

### 9.5 Fine / Penalty Calculation Module

This module handles late payment penalty.

Formula used:

```text
Penalty = Base Tax × 2% × Number of delayed 30-day periods
```

Functions:

- Check due date
- Add penalty for delayed payment
- Update total due automatically

### 9.6 Report Generation Module

This module helps admin view summaries and collection reports.

Functions:

- Dashboard summary
- Recent payments
- Pending tax count
- Collection report using SQL view
- Month-wise payment summary

## 10. Output Screenshots

Add screenshots in this section before final printing or PDF conversion.

### Screenshot 1: Login Page

**Description:** Shows admin and taxpayer login form.

**Insert Screenshot Here**

```text
[Paste Screenshot of Login Page Here]
```

### Screenshot 2: Taxpayer Registration Page

**Description:** Shows the taxpayer registration form.

**Insert Screenshot Here**

```text
[Paste Screenshot of Register Page Here]
```

### Screenshot 3: Admin Dashboard

**Description:** Shows overall system summary such as number of taxpayers, properties, collections, and pending taxes.

**Insert Screenshot Here**

```text
[Paste Screenshot of Admin Dashboard Here]
```

### Screenshot 4: Property Details Page

**Description:** Shows property list and property management form.

**Insert Screenshot Here**

```text
[Paste Screenshot of Property Details Page Here]
```

### Screenshot 5: Tax Payment Page

**Description:** Shows assessed tax details, balance due, and payment form.

**Insert Screenshot Here**

```text
[Paste Screenshot of Tax Payment Page Here]
```

### Screenshot 6: Payment History Page

**Description:** Shows previous payment records and references.

**Insert Screenshot Here**

```text
[Paste Screenshot of Payment History Page Here]
```

### Screenshot 7: Database Tables in phpMyAdmin

**Description:** Shows created tables in MySQL database.

**Insert Screenshot Here**

```text
[Paste Screenshot of Database Tables Here]
```

### Screenshot 8: SQL Trigger / Procedure / View

**Description:** Shows trigger, procedure, or SQL script execution result in phpMyAdmin.

**Insert Screenshot Here**

```text
[Paste Screenshot of Trigger or Procedure Here]
```

## 11. Testing and Results

The project was tested using sample admin and taxpayer accounts.

### Sample Login Credentials

#### Admin

- Username: `admin`
- Password: `admin123`

#### Taxpayer

- Email: `gafar@example.com`
- Password: `user123`

### Test Cases

| Test Case | Input / Action | Expected Result | Actual Result |
|---|---|---|---|
| Taxpayer registration | Enter valid user details | New account should be created | Passed |
| Duplicate email check | Register with same email again | System should show duplicate email error | Passed |
| Admin login | Enter valid admin username and password | Admin dashboard should open | Passed |
| Taxpayer login | Enter valid taxpayer credentials | Taxpayer dashboard should open | Passed |
| Add property | Admin adds a unique property | Property should be stored successfully | Passed |
| Duplicate property code | Admin enters same property code again | System should reject duplicate entry | Passed |
| Tax generation | Property is saved | Annual tax record should be created | Passed |
| Penalty calculation | Pay overdue tax | Penalty should be added automatically | Passed |
| Partial payment | Pay less than full balance | Tax status should become PARTIAL | Passed |
| Full payment | Pay remaining balance | Tax status should become PAID | Passed |
| Payment history | Open history page | Previous payments should be displayed | Passed |
| Report generation | Admin loads report | Collection summary should appear | Passed |

### Result Summary

The system performed successfully for the major functional requirements:

- Registration worked correctly
- Login validation worked correctly
- Property records were managed properly
- Duplicate property prevention worked correctly
- Tax was generated successfully
- Late penalty calculation worked correctly
- Payment history was stored properly
- Reports were generated successfully

## 12. Conclusion

The **Municipal Tax Collection System** successfully demonstrates how a full-stack web application can be used to manage local property tax operations in a structured and efficient way. The system reduces manual work by automating taxpayer registration, property management, tax calculation, late penalty calculation, payment recording, and reporting.

This mini project also demonstrates important technical concepts such as:

- frontend development
- backend API development
- database integration
- session-based authentication
- CRUD operations
- triggers
- stored procedures
- views

Overall, the project meets the required functional objectives and serves as a good academic model for a beginner-friendly municipal e-governance system.

## Appendix

### Important Project Files

- Main backend file: `app.py`
- Database helper: `db.py`
- Configuration file: `config.py`
- SQL script: `database/municipal_tax_collection.sql`
- Frontend templates: `templates/`
- Frontend assets: `static/`

### Suggested Final Submission Format

For final college submission, you can:

- keep this report as the main written document
- paste real screenshots in Section 10
- convert this document to PDF
- attach source code and SQL file separately
