import pytest
import os
import sys
from datetime import datetime, timedelta

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import database
from services.library_service import (
    get_patron_status_report
)

@pytest.fixture(autouse=True)
def temporary_db(monkeypatch):
    # Assign a temporary value to DATABASE so we don't affect the live database
    monkeypatch.setattr(database, 'DATABASE', 'test_database.db')

    database.init_database()
    database.add_sample_data()

    yield

    # Remove the temp database file as it is no longer needed
    os.remove("test_database.db")

def test_report_has_all_properties():
    report =  get_patron_status_report("123456")

    assert report.get("currently_borrowed") != None
    assert report.get("total_late") != None
    assert report.get("number_borrowed") != None
    assert report.get("borrowing_history") != None

def test_report_properties_types():
    report = get_patron_status_report("123456")

    assert isinstance(report.get("currently_borrowed"), list)
    assert isinstance(report.get("total_late"), float)
    assert isinstance(report.get("number_borrowed"), int)
    assert isinstance(report.get("borrowing_history"), list)

def test_report_with_overdue_book():
    borrow_date = datetime.now() - timedelta(days=20)  # Borrowed 20 days ago
    due_date = datetime.now() - timedelta(days=6)  # Due 6 days ago
    
    database.insert_borrow_record("123456", 1, borrow_date, due_date)

    report = get_patron_status_report("123456")

    assert report.get("total_late") > 0
    assert any(book['book_id'] == 3 for book in report.get("currently_borrowed"))

def test_report_with_no_books():
    report = get_patron_status_report("000000")

    assert report.get("currently_borrowed") == []
    assert report.get("total_late") == 0.0
    assert report.get("number_borrowed") == 0
    assert report.get("borrowing_history") == []