# AzmoonGir

An open-source online examination platform built with Flask.

AzmoonGir is a web-based examination system designed for schools, teachers, and educational institutions. It supports both multiple-choice and descriptive exams, automatic grading, AI-assisted evaluation of descriptive answers, student result analysis, and a complete teacher administration panel.

---

## Features

### Student

* User registration and login
* Participate in online exams
* Multiple-choice examinations
* Descriptive examinations
* Image upload for descriptive answers
* Automatic grading
* View detailed exam reports

### Teacher

* Create and manage exams
* Add multiple-choice questions
* Add descriptive questions
* Upload images for questions
* Manage students
* View submissions
* AI-assisted grading for descriptive answers
* Publish results

### Automatic Grading

* Instant grading for multiple-choice exams
* AI-assisted grading for descriptive exams
* Percentage calculation
* Standard score (Z-Score)
* Ranking among participants

---

## Technologies

* Python
* Flask
* SQLAlchemy
* Jinja2
* Celery
* MySQL
* HTML
* CSS
* JavaScript

---

## Project Structure

```text
project/
│
├── apps/
├── upload/
├── requirements.txt
├── run.py
├── calc_result.py
├── celery_worker.py
├── config.py
├── .env
└── README.md
```

---

## Installation

Follow these steps to run azmoon_gir locally.

---

### Requirements

* Python
* MySQL
* Redis
* Celery

the project should be ran on linux/macOS opearing systems.

### Clone

```bash
git clone https://github.com/aryan7384/azmoon_gir.git
cd azmoon_gir
```

### Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file in the project root.

the information needed for this section is in .env.example near this file.

### Database setup

Create a MySQL database named azmoon_db.
then set DATABASE_URI inside .env to match your database settings.
after it's created, run this command:

```bash
flask --app run db init && flask --app run db migrate && flask --app run db upgrade
```

after that, there should be a new directory in project's root directory named migrations.

### Start Redis

```bash
redis-server
```

### Start Celery

```bash
celery -A celery_worker.celery worker --loglevel=info
```

### Run the application

```bash
flask --app run run
```

---

## Screenshots

### Login page

![Login](screenshots/Screenshot%202026-06-29%20010932.png)

### Student dashboard

![Student](screenshots/Screenshot%202026-06-29%20011058.png)

### Teacher dashboard

![Teacher](screenshots/Screenshot%202026-06-29%20011255.png)

### Exam page

![Exam](screenshots/Screenshot%202026-06-29%20011504.png)

### Result page

![Result](screenshots/Screenshot%202026-06-29%20011858.png)

---

## Roadmap

* [x] Negative marking
* [ ] Time-limited exams
* [x] Randomized question order
* [x] Randomized option order
* [ ] Export results to Excel
* [ ] Export results to PDF
* [ ] Question bank
* [ ] Multi-language support
* [ ] Mobile-friendly UI improvements

---

## Author

Developed by **Aryan Amraei**.
