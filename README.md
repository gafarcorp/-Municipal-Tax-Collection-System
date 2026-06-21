# Municipal Tax Collection System

A full-stack web application designed to streamline the management of municipal property tax operations. This project serves as a comprehensive digital solution for taxpayers and administrators to manage property records, calculate taxes, process payments, and generate reports.

## 🚀 Features

### For Administrators
- **Property Management:** Add, update, and delete property records.
- **Taxpayer Monitoring:** View and manage taxpayer information.
- **Collection Dashboard:** Real-time summary of total collections, pending taxes, and recent payments.
- **Reports:** Generate detailed collection reports using database views.

### For Taxpayers
- **Secure Authentication:** User registration and login functionality.
- **Property Tracking:** View all registered properties linked to the account.
- **Tax Overview:** Check annual tax details, due dates, and accumulated penalties.
- **Online Payments:** Securely record tax payments and view historical transactions.

### Automated Logic
- **Automatic Tax Calculation:** Annual tax is computed based on property size, type, and valuation.
- **Penalty System:** Automatically applies a 2% penalty for every 30 days of delay beyond the due date via database triggers.
- **Duplicate Prevention:** Ensures data integrity by preventing duplicate property codes and taxpayer emails.

## 🛠️ Tech Stack

- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5
- **Backend:** Python, Flask
- **Database:** MySQL
- **Authentication:** Flask Session-based authentication

## 📂 Project Structure

```text
Municipal Tax Collection System/
├── app.py              # Main Flask application entry point
├── config.py           # Database and application configuration
├── db.py               # Database connection and helper functions
├── requirements.txt    # Python dependencies
├── database/
│   └── municipal_tax_collection.sql  # Database schema and initial data
├── docs/               # Project documentation and reports
├── static/             # Static assets (CSS, JS)
└── templates/          # HTML templates for Flask
```

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.x
- MySQL Server (or XAMPP/WAMP)

### 2. Clone the Repository
```bash
git clone <repository-url>
cd "Municipal Tax Collection System"
```

### 3. Set Up Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Database Configuration
1. Open your MySQL client (e.g., phpMyAdmin, MySQL Workbench).
2. Create a new database named `municipal_tax_collection`.
3. Import the SQL file located at `database/municipal_tax_collection.sql`.
4. Update `config.py` with your MySQL credentials (host, user, password).

### 6. Run the Application
```bash
python app.py
```
The application will be available at `http://127.0.0.1:5000`.

## 📝 License
This project is developed for academic purposes as part of the DBT Activity.
