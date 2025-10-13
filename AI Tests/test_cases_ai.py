import pytest
from datetime import datetime, timedelta
import os
import sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
import database
from library_service import (
    add_book_to_catalog,
    borrow_book_by_patron,
    return_book_by_patron,
    calculate_late_fee_for_book,
    search_books_in_catalog,
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

class TestAddBookToCatalog:

    def test_add_valid_book(self):
        success, msg = add_book_to_catalog("The Odyssey", "Homer", "1234567890123", 3)
        assert success
        assert "successfully added" in msg.lower()

    def test_add_duplicate_isbn(self):
        # First insert
        add_book_to_catalog("Book A", "Author A", "9999999999999", 2)
        # Second with same ISBN
        success, msg = add_book_to_catalog("Book B", "Author B", "9999999999999", 5)
        assert not success
        assert "already exists" in msg.lower()

    def test_invalid_title(self):
        success, msg = add_book_to_catalog("", "Author", "1234567890123", 3)
        assert not success
        assert "title is required" in msg.lower()

    def test_title_too_long(self):
        title = "A" * 201
        success, msg = add_book_to_catalog(title, "Author", "1234567890123", 3)
        assert not success
        assert "less than 200" in msg.lower()

    def test_invalid_author(self):
        success, msg = add_book_to_catalog("Book", "", "1234567890123", 3)
        assert not success
        assert "author is required" in msg.lower()

    def test_author_too_long(self):
        author = "B" * 101
        success, msg = add_book_to_catalog("Book", author, "1234567890123", 3)
        assert not success
        assert "less than 100" in msg.lower()

    def test_invalid_isbn(self):
        success, msg = add_book_to_catalog("Book", "Author", "123", 3)
        assert not success
        assert "isbn must be exactly 13" in msg.lower()

    def test_invalid_total_copies(self):
        success, msg = add_book_to_catalog("Book", "Author", "1234567890123", 0)
        assert not success
        assert "positive integer" in msg.lower()
        
class TestBorrowBookByPatron:

    def test_valid_borrow(self):
        # Assuming sample data includes a book with ID 1
        success, msg = borrow_book_by_patron("123456", 1)
        assert success
        assert "successfully borrowed" in msg.lower()
        assert "due date" in msg.lower()

    def test_invalid_patron_id(self):
        success, msg = borrow_book_by_patron("abc", 1)
        assert not success
        assert "invalid patron id" in msg.lower()

    def test_book_not_found(self):
        success, msg = borrow_book_by_patron("123456", 999)
        assert not success
        assert "book not found" in msg.lower()

    def test_book_not_available(self):
        # Borrow same book until it’s unavailable
        for _ in range(5):
            borrow_book_by_patron("111111", 2)
        success, msg = borrow_book_by_patron("222222", 2)
        assert not success
        assert "not available" in msg.lower()

    def test_patron_reached_limit(self):
        # Patron has already borrowed 5 books
        borrow_date = datetime.now() - timedelta(days=2)
        due_date = datetime.now() + timedelta(days=12)

        for i in range(0, 6):
            database.insert_borrow_record("123456", i, borrow_date, due_date)

        # Now trying to borrow another should fail
        success, msg = borrow_book_by_patron("123456", 6)
        assert not success
        assert "maximum borrowing limit" in msg.lower()


class TestReturnBookByPatron:

    def test_return_successful(self):
        borrow_book_by_patron("123456", 1)
        success, msg = return_book_by_patron("123456", 1)
        assert success
        assert "book returned successfully" in msg.lower()

    def test_invalid_patron_id(self):
        success, msg = return_book_by_patron("12", 1)
        assert not success
        assert "invalid patron id" in msg.lower()

    def test_book_not_borrowed(self):
        success, msg = return_book_by_patron("123456", 999)
        assert not success
        assert "not borrowed by patron" in msg.lower()


class TestCalculateLateFee:

    def test_no_fee_not_overdue(self):
        # Borrow a book normally
        borrow_book_by_patron("123456", 1)
        result = calculate_late_fee_for_book("123456", 1)
        assert result["fee_amount"] == 0.0
        assert "not overdue" in result["status"].lower()

    def test_fee_first_week_overdue(self):
        # Manually insert a borrow record 20 days ago with due date 6 days ago (6 days late)
        borrow_date = datetime.now() - timedelta(days=20)
        due_date = datetime.now() - timedelta(days=6)
        database.insert_borrow_record("123456", 1, borrow_date, due_date)
        # Calculate
        result = calculate_late_fee_for_book("123456", 1)
        # 6 days * $0.50 = $3.00
        assert result["fee_amount"] == 3.0
        assert result["days_overdue"] == 6
        assert "successful" in result["status"].lower()

    def test_fee_after_first_week_overdue(self):
        # Borrowed 25 days ago, due 11 days ago (11 days late)
        borrow_date = datetime.now() - timedelta(days=25)
        due_date = datetime.now() - timedelta(days=11)
        database.insert_borrow_record("123456", 1, borrow_date, due_date)
        # Calculate
        result = calculate_late_fee_for_book("123456", 1)
        # 7 days * $0.50 + 4 days * $1.00 = $7.5
        assert result["fee_amount"] == 7.5
        assert result["days_overdue"] == 11

    def test_fee_capped_at_maximum(self):
        # Borrowed 60 days ago, due 46 days ago (46 days late)
        borrow_date = datetime.now() - timedelta(days=60)
        due_date = datetime.now() - timedelta(days=46)
        database.insert_borrow_record("123456", 1, borrow_date, due_date)
        # Calculate
        result = calculate_late_fee_for_book("123456", 1)
        # Fee capped at $15.00
        assert result["fee_amount"] == 15.0
        assert result["days_overdue"] == 46
        assert "successful" in result["status"].lower()

class TestSearchBooksInCatalog:

    def test_search_by_title_partial(self):
        results = search_books_in_catalog("adventure", "title")
        assert isinstance(results, list)
        for book in results:
            assert "adventure" in book["title"].lower()

    def test_search_by_author_partial(self):
        results = search_books_in_catalog("doe", "author")
        assert all("doe" in b["author"].lower() for b in results)

    def test_search_by_isbn_exact(self):
        book = add_book_to_catalog("Exact Match", "Tester", "5555555555555", 1)
        results = search_books_in_catalog("5555555555555", "isbn")
        assert all(b["isbn"] == "5555555555555" for b in results)

    def test_invalid_search_type(self):
        results = search_books_in_catalog("anything", "genre")
        assert results == []


class TestPatronStatusReport:

    def test_valid_patron_report(self):
        borrow_book_by_patron("123456", 1)
        report = get_patron_status_report("123456")
        assert report["status"] == "success"
        assert "currently_borrowed" in report
        assert "borrowing_history" in report
        assert isinstance(report["total_late"], float)

    def test_invalid_patron_id(self):
        success, msg = get_patron_status_report("abc")
        assert not success
        assert "invalid patron id" in msg.lower()
