# Hospital Backend

A Django REST Framework–based backend for a hospital management system. This project provides APIs for user authentication, patient–doctor assignments, doctor note management (with LLM-based extraction of actionable steps), and actionable reminders. It is built using Django 4.2, PostgreSQL, Celery for asynchronous tasks, and Docker for containerization.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)
- [Authors](#authors)

---

## Overview

This project is a backend system for managing hospital operations. It supports:
- **User Management:** Registration, login, and profile management for both patients and doctors.
- **Patient–Doctor Assignment:** Listing available doctors, allowing patients to select a doctor, and enabling doctors to view their patients.
- **Doctor Notes & LLM Integration:** Submitting and updating doctor notes with asynchronous processing to extract actionable steps (using Celery).
- **Actionable Reminders:** Managing and updating tasks based on doctor notes.

The application is designed with scalability, security, and maintainability in mind.

---

## Features

- **User Management:**  
  - JWT-based authentication using Django REST Framework SimpleJWT.  
  - Endpoints for signup, login, and profile updates.

- **Patient–Doctor Assignment:**  
  - List available doctors with filtering and pagination.  
  - Enable patients to select a doctor.  
  - Doctors can view their assigned patients.

- **Doctor Notes & LLM Integration:**  
  - Asynchronous note processing to extract actionable steps.  
  - Automatic cancellation/rescheduling of tasks when notes are updated.

- **Actionable Reminders:**  
  - Retrieval of actionable checklists and plans.  
  - Status updates on tasks with support for recurring reminders.

- **Development & Deployment:**  
  - Containerized with Docker and managed with docker-compose.  
  - Comprehensive API documentation using drf-yasg (Swagger).  
  - Asynchronous task management with Celery, django-celery-beat, and django-celery-results.

---

## Prerequisites

- **Python:** 3.9 or later  
- **Database:** PostgreSQL  
- **Virtual Environment:** Recommended for dependency management  
- **Docker:** Optional (for containerized development)  
- **Redis:** Required for Celery and caching

---

## Getting Started

Follow these steps to set up the project locally:

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/YounoussaBen/hospital_backend.git
   cd hospital_backend
   ```

2. **Set Up a Virtual Environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**

   Create a `.env` file based on `.env.example` and set the necessary variables (e.g., `DEBUG`, `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CELERY_BROKER_URL`, etc.).

5. **Apply Database Migrations:**

   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser (optional):**

   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server:**

   ```bash
   python manage.py runserver
   ```

---

## Installation

For a standard installation, follow the [Getting Started](#getting-started) instructions. To use Docker:

1. **Build and Run with Docker Compose:**

   ```bash
   docker-compose up --build
   ```

2. **Access the Application:**

   The app will be available at [http://localhost:8000](http://localhost:8000).

---

## Running the Application

### Development Server

Start the Django development server with:

```bash
python manage.py runserver
```

### Celery Worker

Run the Celery worker to handle background tasks:

```bash
celery -A config worker -l info
```

### Celery Beat

For scheduled tasks (e.g., periodic task scheduling), start Celery Beat:

```bash
celery -A config beat -l info
```

---

## Running Tests

The project includes unit, integration, and performance tests using Django’s test framework along with Factory Boy and Faker. Run all tests with:

```bash
python manage.py test
```

---

## API Documentation

Interactive API documentation is automatically generated using drf-yasg. Once the server is running, access the documentation at:

```
http://localhost:8000/swagger/
```

This provides detailed information about each endpoint, required parameters, and expected responses.

---

## Deployment

For production deployment, consider these recommendations:

- **Environment:** Ensure all environment variables are correctly configured.
- **Containerization:** Use Docker and docker-compose for a consistent deployment environment.
- **Web Server:** Deploy with Gunicorn (or another WSGI HTTP server) behind a reverse proxy like Nginx.
- **Static Files:** Serve static files using WhiteNoise or an external CDN.
- **Scaling:** Leverage load balancing and horizontal scaling.
- **Security:** Enforce HTTPS, secure cookies, rate limiting on sensitive endpoints, and regular dependency updates.

---

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new feature branch:
   ```bash
   git checkout -b feature/YourFeature
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add feature: description"
   ```
4. Push your branch:
   ```bash
   git push origin feature/YourFeature
   ```
5. Open a pull request and provide a detailed description of your changes.

Please ensure that your code adheres to the project’s style guidelines and includes appropriate tests.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Authors

Younoussa Abdourhaman  
📧 [younoussaabdourhaman@gmail.com](mailto:younoussaabdourhaman@gmail.com)  
🔗 [Github](https://github.com/YounoussaBen)