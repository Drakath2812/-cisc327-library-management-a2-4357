import pytest
import os

import database
from services.library_service import (
    add_book_to_catalog, borrow_book_by_patron
)

from unittest.mock import patch

@pytest.fixture(autouse=True)
def temporary_db(monkeypatch):
    # Assign a temporary value to DATABASE so we don't affect the live database
    monkeypatch.setenv("LIBRARY_DB_PATH", "unit_test.db")

    database.init_database()
    database.add_sample_data()

    add_book_to_catalog("Test", "Author Test", "9999999999999", 10)
    # Setting up a patron who has borrowed the maxmimum amount of books
    borrow_book_by_patron("987654", 4)
    borrow_book_by_patron("987654", 4)
    borrow_book_by_patron("987654", 4)
    borrow_book_by_patron("987654", 4)
    borrow_book_by_patron("987654", 4)

    # Yield control to the test
    yield

    # Teardown
    os.remove("unit_test.db")

def test_borrow_book_by_patron_valid():
    """Testing the valid borrowing of a book, with a valid patron"""
    success, message = borrow_book_by_patron("123456", 1) #The Great Gatsby

    assert success == True
    assert "successfully borrowed" in message.lower()

def test_borrow_book_by_patron_invalid_patron_id():
    """Testing the valid borrowing of a book, with an invalid patron id"""
    success, message = borrow_book_by_patron("123456789", 1) #The Great Gatsby

    assert success == False
    assert "invalid patron id" in message.lower()

def test_borrow_book_by_patron_invalid_book_id():
    """Testing the valid borrowing of a book, with an invalid id and valid patron"""
    success, message = borrow_book_by_patron("222222", -1)

    assert success == False
    assert "book not found" in message.lower()

def test_borrow_book_no_copies_available():
    """Testing the borrowing of a book, with a valid id, and valid patron, but no copies available"""
    success, message = borrow_book_by_patron("123456", 3) #1984

    assert success == False
    assert "not available" in message.lower()

def test_borrow_with_max_already_borrowed_patron():
    """Testing a patron with already max borrowed books trying to borrow more (that do exist)"""
    success, message = borrow_book_by_patron("987654", 4)

    assert success == False
    assert "maximum borrowing limit" in message.lower()

def test_borrow_with_max_already_borrowed_patron_and_out_of_stock_book():
    """Testing a patron with already max borrowed books trying to borrow more (that do exist)"""
    success, message = borrow_book_by_patron("987654", 0)

    assert success == False
    assert "book not found" in message.lower()

# Uses mocking to cover the DB error case
def test_borrow_with_insert_borrow_record_failure():
    """Testing a valid insert but with a database error"""
    with patch("services.library_service.insert_borrow_record", return_value = False):
        success, message = borrow_book_by_patron("123456", 1)

    assert success == False
    assert "Database error occurred while creating borrow record" in message

def test_updating_availability_with_database_failure():
    """Testing a valid borrow but with a database error when updating record."""
    with patch("services.library_service.update_book_availability", return_value = False):
        success, message = borrow_book_by_patron("123456", 1)

    assert success == False
    assert "Database error occurred while updating book availability" in message
