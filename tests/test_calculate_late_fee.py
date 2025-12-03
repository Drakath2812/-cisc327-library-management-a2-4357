import pytest
import os
from datetime import datetime, timedelta

import database
from services.library_service import (
    calculate_late_fee_for_book
)

@pytest.fixture(autouse=True)
def temporary_db(monkeypatch):
    # Assign a temporary value to DATABASE so we don't affect the live database
    monkeypatch.setenv("LIBRARY_DB_PATH", "unit_test.db")

    database.init_database()
    database.add_sample_data()

    # Yield control to the test
    yield

    # Teardown
    os.remove("unit_test.db")

def test_calculate_late_fee_on_time():
    """Test the calculation of late fee when the book is returned on time (no fee)."""
    borrow_date = datetime.now()
    due_date = borrow_date  # Returned on time
    
    database.insert_borrow_record("123456", 1, borrow_date, due_date)

    response = calculate_late_fee_for_book("123456", 1)

    assert response['fee_amount'] == 0.00
    assert response['days_overdue'] == 0
    assert "no fee" in response['status'].lower()

def test_calculate_late_fee_small_lateness():
    """Test the calculation of late fee when the book is 6 days late (before price hike)"""
    borrow_date = datetime.now() - timedelta(days=20)  # Borrowed 20 days ago
    due_date = datetime.now() - timedelta(days=6)  # Due 6 days ago
    
    database.insert_borrow_record("123456", 1, borrow_date, due_date)

    response = calculate_late_fee_for_book("123456", 1)

    assert response['fee_amount'] == 3.00  # 6 * $0.50
    assert response['days_overdue'] == 6
    assert "late fee" in response['status'].lower()

def test_calculate_late_fee_medium_lateness():
    """Test the calculation of late fee when the book is 11 days late (includes the higher rate)"""
    borrow_date = datetime.now() - timedelta(days=25)  # Borrowed 18 days ago
    due_date = datetime.now() - timedelta(days=11)

    database.insert_borrow_record("123456", 1, borrow_date, due_date)

    response = calculate_late_fee_for_book("123456", 1)  # Book ID 1, 11 days late

    assert response['fee_amount'] == 7.50  # (7 * $0.50) + (4 * $1.00)
    assert response['days_overdue'] == 11
    assert "late fee" in response['status'].lower()

def test_calculate_late_fee_max_fee():
    """Test the calculation of late fee when the book is overdue for more than 15 days"""
    borrow_date = datetime.now() - timedelta(days=100) # Borrowed 100 days ago
    due_date = datetime.now() - timedelta(days=86)
    
    database.insert_borrow_record("123456", 1, borrow_date, due_date)

    response = calculate_late_fee_for_book("123456", 1)  # Book ID 1, 20 days overdue

    assert response['fee_amount'] == 15.00  # Maximum fee reached
    assert response['days_overdue'] == 86
    assert "successful" in response['status'].lower()

def test_calculate_late_fee_no_borrow_record():
    """Test the return when no record exists"""

    response = calculate_late_fee_for_book("123456", 999)

    assert response['fee_amount'] == 0.00
    assert response['days_overdue'] == 0
    assert "no borrow record" in response['status'].lower()

def test_return_on_due_date():
    """Test when the borrowed book is returned on the exact right date"""

    borrow_date = datetime.now() - timedelta(days=14)
    due_date = borrow_date + timedelta(days=14)

    database.insert_borrow_record("123456", 1, borrow_date, due_date)

    response = calculate_late_fee_for_book("123456", 1)