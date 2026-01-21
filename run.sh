#!/bin/bash

echo "=========================================="
echo "  TrisSEAS - Smart Entry & Attendance"
echo "=========================================="
echo ""
echo "Starting development server..."
echo ""
echo "Access points:"
echo "  - Home: http://localhost:8000/"
echo "  - Gate Console: http://localhost:8000/console/"
echo "  - Ops Dashboard: http://localhost:8000/ops/"
echo "  - Analytics: http://localhost:8000/analytics/"
echo "  - Django Admin: http://localhost:8000/admin/"
echo ""
echo "Demo accounts:"
echo "  - Admin: admin@example.com / AdminPass123"
echo "  - Teacher: teacher@example.com / TeacherPass123"
echo "  - Student: student@example.com / StudentPass123"
echo ""
echo "=========================================="
echo ""

python3 manage.py runserver 0.0.0.0:8000
