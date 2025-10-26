 API Documentation: User Registration & KYC Module
 Objective

To develop a secure, scalable backend API that allows customers to register, submit KYC documents, and store validated user profiles in MongoDB — using Flask as the backend framework and HTML as the frontend interface.

 Actors

Actor	Description

Customer-	Registers and uploads KYC details.

Bank Admin-	Reviews/approves user KYC .

 Tech Stack

Component - Technology

Backend - Python + Flask

Database - MongoDB

Frontend - HTML + CSS (for forms)

Authentication - JWT (JSON Web Token)

Password Security - bcrypt

Rate Limiting - Flask-Limiter

Testing - pytest, coverage, locust (load testing)


API Endpoints:

1. POST /api/register

Description: Register a new customer and hash password before saving.

2. POST /api/login

Description: Authenticate user and issue JWT token.

3. POST /api/upload_kyc

Description: Upload (simulated) KYC document after authentication.

4. GET /api/profile

Description: Fetch user profile details.

5. PATCH /api/admin/verify_kyc/<user_id>

Description: Admin reviews and verifies a customer's KYC.

6. GET /api/admin/pending_kyc

Description: View all customers whose KYC is pending (Admin only).