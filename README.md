# AgriCore V1: Smart Agricore Management System


AgriCore is a modern, full-stack enterprise solution designed to streamline agricultural operations through secure user management, real-time activity tracking, and an intuitive administrative control panel. Built with a focus on security and performance, it provides a seamless experience for both farmers (Customers) and system operators (Admins).

## ✨ Key Features

### 🔐 Secure Identity & Access
*   **Dual Authentication**: Support for both standard Email/Password credentials and Google OAuth 2.0.
*   **RBAC (Role-Based Access Control)**: Granular permissions for Customers and Administrators.
*   **JWT Security**: Stateless authentication using secure JSON Web Tokens with automatic refresh logic.

### 📊 Administrative Intelligence
*   **Real-time Dashboard**: Track total users, customer/admin ratios, and platform traffic.
*   **Activity Monitoring**: Daily and Monthly login statistics to monitor platform engagement.
*   **User Governance**: Promote or demote users, manage account statuses, and oversee profiles.

### 🕵️ Audit & Tracking
*   **Full Session History**: Automatic logging of every login and logout event.
*   **Security Logs**: IP address tracking for every session to ensure account integrity.
*   **Targeted Auditing**: Admins can filter logs for specific users to investigate activity trails.

---

## 🚀 Tech Stack

### Backend (The Core)
*   **Django & DRF**: Robust API framework.
*   **SimpleJWT**: Industry-standard token authentication.
*   **PostgreSQL**: High-performance relational database.
*   **Google Auth**: Social authentication integration.

### Frontend (The Interface)
*   **Next.js 14**: Server-side rendering and optimized routing.
*   **TypeScript**: Type-safe development for reliable code.
*   **Tailwind CSS**: Modern, responsive styling with premium aesthetics.
*   **Lucide React**: Beautiful, consistent iconography.

---

## 🛠️ Getting Started

### 1. Prerequisites
*   Python 3.10+
*   Node.js 18+
*   PostgreSQL

### 2. Backend Setup
1. Navigate to `/backend`.
2. Create a virtual environment: `python -m venv venv`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Configure your `.env` file (see Environmental Variables below).
5. Run migrations: `python manage.py migrate`.
6. Start the server: `python manage.py runserver`.

### 3. Frontend Setup
1. Navigate to `/frontend`.
2. Install packages: `npm install`.
3. Configure your `.env.local` file.
4. Start the development server: `npm run dev`.

---

## 🔑 Environmental Variables

Create a `.env` file in the backend and a `.env.local` in the frontend with the following keys:

**Backend:**
* `SECRET_KEY`: Django secret key.
* `DEBUG`: Set to `True` for development.
* `DATABASE_URL`: Your PostgreSQL connection string.
* `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID.

**Frontend:**
* `NEXT_PUBLIC_API_URL`: `http://localhost:8000/api`
* `NEXT_PUBLIC_GOOGLE_CLIENT_ID`: Your Google OAuth Client ID.

---

## 📁 API Documentation

A complete Postman collection is included in the `/postman` directory. Import `agricore_auth_collection.json` into Postman to test:
*   Standard Registration & Login
*   Google OAuth Verification
*   System Audit Logs
*   Admin Stats & User Management

---

## 🛡️ Administrative Access

To maintain system security, default administrative credentials are not provided in this public documentation. 

**For initial setup:**
1. Create a user via the registration page.
2. Use the Django shell (`python manage.py shell`) to manually promote your first user to the `admin` role:
   ```python
   from users.models import User
   u = User.objects.get(email="your-email@example.com")
   u.role = 'admin'
   u.is_staff = True
   u.save()
   ```

**For ongoing support or access requests:**
Please contact the project maintainer directly via the internal messaging system or repository channels.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

Developed with ❤️ for the future of Agriculture.
