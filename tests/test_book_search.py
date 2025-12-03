import pytest
import os

import database
from services.library_service import (
    search_books_in_catalog
)

# Test data to make the search more complex
    
books = [
        {"title": "The Anthropocene Reviewed", "author": "John Green", "isbn": "000000000001"},
        {"title": "What If?", "author": "Randall Munroe", "isbn": "000000000002"},
        {"title": "The Lord of the Rings", "author": "J.R.R. Tolkien", "isbn": "000000000003"},
        {"title": "It", "author": "Stephen King", "isbn": "000000000004"},
        {"title": "Everything is Tuberculosis", "author": "John Green", "isbn": "000000000005"},
        {"title": "Hitchhiker's Guide to the Galaxy", "author": "Douglas Adams", "isbn": "000000000006"},
        {"title": "The Martian", "author": "Andy Weir", "isbn": "000000000007"}
    ]

@pytest.fixture(autouse=True)
def temporary_db(monkeypatch):
    # Assign a temporary value to DATABASE so we don't affect the live database
    monkeypatch.setenv("LIBRARY_DB_PATH", "unit_test.db")

    database.init_database()

    for book in books:
        database.insert_book(book["title"], book["author"], book["isbn"], 3, 3)

    # Yield control to the test
    yield

    # Teardown
    os.remove("unit_test.db")

def test_search_books_by_title():
    """Test searching for books by title"""
    
    search_term = "ThE" # Odd case to ensure the case insensitivity is working
    search_type = "title"
    
    results = search_books_in_catalog(search_term, search_type)
    
    # Check if results contain books with "The" in the title
    assert 4 == len(results)
    assert all(search_term.lower() in book["title"].lower() for book in results)

def test_search_books_by_author():
    """Tests searching for books by author"""

    search_term = "Green"
    search_type = "author"
    
    results = search_books_in_catalog(search_term, search_type)
    
    assert len(results) == 2
    assert all(search_term.lower() in book["author"].lower() for book in results)

def test_search_books_by_isbn():
    """Tests searching for books by author"""

    search_term = "000000000007"
    search_type = "isbn"
    
    results = search_books_in_catalog(search_term, search_type)
    
    # Check if results contain books with "The" in the title
    assert len(results) == 1
    assert results[0]["title"] == "The Martian"

def test_search_books_isbn_with_spaces():
    """Test searching with leading/trailing spaces"""
    
    # Search for an ISBN with spaces
    search_term = " 000000000006  "  # ISBN for "Hitchhiker's Guide to the Galaxy"
    search_type = "isbn"
    
    results = search_books_in_catalog(search_term, search_type)
    
    # Check if the result contains the book with the exact ISBN
    assert len(results) == 1
    assert results[0]["title"] == "Hitchhiker's Guide to the Galaxy"

def test_blank_search():
    """Test searching blankly"""
    search_term = ""
    search_type = "title"

    results = search_books_in_catalog(search_term, search_type)

    assert len(results) == len(books)