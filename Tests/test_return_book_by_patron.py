import pytest
import os
import sys
from datetime import datetime, timedelta

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import database
from library_service import (
    add_book_to_catalog, borrow_book_by_patron, return_book_by_patron
)

@pytest.fixture(autouse=True)
def temporary_db(monkeypatch):
    # Assign a temporary value to DATABASE so we don't affect the live database
    monkeypatch.setattr(database, 'DATABASE', 'test_database.db')

    database.init_database()
    database.add_sample_data()

    add_book_to_catalog("Test", "Author Test", "9999999999999", 10)

    yield

    # Remove the temp database file as it is no longer needed
    os.remove("test_database.db")

def test_valid_return():
    # Borrow book
    borrow_book_by_patron("123456", 1)

    success, message = return_book_by_patron("123456", 1)

    assert success == True
    assert "book returned" in message.lower()

def test_return_book_invalid_patron_id():
    """Test returning a book with an invalid patron ID"""
    success, message = return_book_by_patron("9999999", 1)

    assert success == False
    assert "invalid patron id" in message.lower()

def test_return_book_invalid_book_id():
    """Test returning a book with valid patron id but invalid book ID"""
    success, message = return_book_by_patron("123456", -1)

    assert success == False
    assert "book not borrowed by patron" in message.lower()

def test_return_book_not_borrowed():
    """Test returning a book that was not borrowed by the patron"""
    success, message = return_book_by_patron("123456", 2)

    assert success == False
    assert "book not borrowed by patron" in message.lower()

def test_return_book_with_late_fee():
    """Test returning a book late, and returning a lateness message"""

    borrow_date = datetime.now() - timedelta(days=100) # Borrowed 100 days ago
    due_date = datetime.now() - timedelta(days=86)
    
    database.insert_borrow_record("123456", 1, borrow_date, due_date)

    success, message = return_book_by_patron("123456", 1)

    assert success == True
    assert "late fee" in message.lower()
    assert "days late" in message.lower()

def test_returning_book_increases_availability():
    """Returns 1984, and checks if it can be borrowed properly afterwards"""

    return_book_by_patron("123456", 3)

    success, message = borrow_book_by_patron("123456", 3)
    assert success == True
    assert "successfully borrowed" in message.lower()