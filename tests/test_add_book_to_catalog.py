import pytest
import os
import sys

import database
from services.library_service import (
    add_book_to_catalog
)

from unittest.mock import patch

@pytest.fixture(autouse=True)
def temporary_db(monkeypatch):
    # Assign a temporary value to DATABASE so we don't affect the live database
    monkeypatch.setattr(database, 'DATABASE', 'test_database.db')
    print(f"db: {database.DATABASE}")
    database.init_database()
    database.add_sample_data()

    # Yield control to the test
    yield

    # Teardown
    os.remove("test_database.db")


def test_add_book_valid_input():
    """Test adding a book with valid input."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "2345678901234", 4)
    
    assert success == True
    assert "successfully added" in message.lower()

def test_add_book_invalid_isbn_too_short():
    """Test adding a book with ISBN too short."""
    success, message = add_book_to_catalog("Test Book!", "Test Author!", "123456789", 5)
    
    assert success == False
    assert "13 digits" in message

def test_add_book_invalid_isbn_too_long():
    """Test adding a book with ISBN too long."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "12345678901234567890", 5)
    
    assert success == False
    assert "13 digits" in message

def test_add_book_title_too_long():
    """Test adding a book with too many characters in it's name"""
    long_name = "A" * 250
    success, message = add_book_to_catalog(long_name, "Test Author", "1234567890123", 5)

    assert success == False
    assert "less than 200 characters." in message

def test_add_book_no_title():
    """Test adding a book with no title"""
    success, message = add_book_to_catalog("", "Test Author", "1234567890123", 5)

    assert success == False
    assert "Title is required" in message

def test_add_book_no_author():
    """Test adding a book with no author"""
    success, message = add_book_to_catalog("Test Book", "", "1234567890123", 5)

    assert success == False
    assert "Author is required" in message

def test_add_book_author_too_long():
    """Test adding a book with an author name that is too long"""
    success, message = add_book_to_catalog("Test Book", "a long long time ago, I can still remember, how that music used to make me smile. And I knew if I had my chance, that I could make those people dance and then, maybe they'd be happy for a while. But february made me shiver, with every paper I delievered, bad news on the door step, I couldn't take one more step. I can't remember if I cried when I read about his widowed bride. But something touched me deep inside, the day the music died. So bye bye Miss American Pie- Drove my chevy to the levy but the levy was dry.", "1234567890123", 5)

    assert success == False
    assert "Author must be less than 100 characters" in message

def test_add_book_negative_copies():
    """Test adding a book with a negative copy number"""
    success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", -42)

    assert success == False
    assert "must be a positive integer" in message

def test_add_book_duplicate_isbn():
    """Test adding a book with a duplicate isbn"""
    add_book_to_catalog("Test Book 1", "Test Author 1", "1234567890123", 3)
    success, message = add_book_to_catalog("Test Book 2", "Test Author 2", "1234567890123", 6)

    assert success == False
    assert "ISBN already exists" in message

# Uses mocking to fake a DB error.
def test_add_book_database_error():
    """Test adding a book but there is a database error"""
    with patch("services.library_service.insert_book", return_value = False):
        success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)

    assert success == False
    assert "Database error occurred while adding the book" in message