# TrisSEAS

Smart Entry & Attendance System built with Django. The project ships with polished operational consoles, analytics, and a live-notifications experience so you can demo or deploy quickly.

## Quick start
1. Install dependencies (Python 3.11+):
   ```bash
   pip install -r requirements.txt
   ```
2. Apply migrations:
   ```bash
   python manage.py migrate
   ```
3. Seed demo data, including an admin user (`admin` / `admin`) plus students, attendance, and gate events:
   ```bash
   python manage.py seed_demo
   ```
4. Run the server:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
5. Explore the experience:
   - Home: [http://localhost:8000/](http://localhost:8000/)
   - Gate console: [http://localhost:8000/console/](http://localhost:8000/console/)
   - Ops dashboard: [http://localhost:8000/ops/](http://localhost:8000/ops/)
   - Analytics: [http://localhost:8000/analytics/](http://localhost:8000/analytics/)
   - Notifications: [http://localhost:8000/notifications/](http://localhost:8000/notifications/)
   - Django admin: [http://localhost:8000/admin/](http://localhost:8000/admin/)

The landing page and dashboards read from `/api/live-stats/`, which is populated by the demo data seeder. Rerun `seed_demo` anytime to reset the experience without recreating existing records for the current day.
