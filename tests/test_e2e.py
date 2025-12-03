import pytest
from playwright.sync_api import sync_playwright, Page, expect
import subprocess
import time
import os

@pytest.fixture(scope="session", autouse=True)
def test_server():

    # Start Flask in test mode
    proc = subprocess.Popen(
        ["python", "app.py", "--test"]
    )

    # Give the server time to start
    time.sleep(2)

    yield

    # Shutdown server
    proc.terminate()
    proc.wait()

@pytest.fixture(scope="session")
def browser():
    # Launch browser session
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # set to True for headless
        yield browser
        browser.close()

@pytest.fixture(scope="session")
def page(browser):
    # Create a page within the browser
    context = browser.new_context()
    page = context.new_page()
    yield page
    page.close()

def test_page_basic(page):
    page.goto('http://localhost:2812')

    expect(page.get_by_text("Library Management System")).to_have_role("heading")

# Testing adding a book to the library, and then borrowing a copy of it.
def test_workflow(page):
    page.goto('http://localhost:2812/catalog')

    page.get_by_role("link", name="➕ Add New Book").click()

    page.get_by_role("textbox", name="Title *").click()
    page.get_by_role("textbox", name="Title *").fill("Test Book")
    page.get_by_role("textbox", name="Author *").click()
    page.get_by_role("textbox", name="Author *").fill("Test Author")
    page.get_by_role("textbox", name="ISBN *").click()
    page.get_by_role("textbox", name="ISBN *").fill("0000000000013")
    
    page.get_by_role("spinbutton", name="Total Copies *").click()
    page.get_by_role("spinbutton", name="Total Copies *").fill("5")
    page.get_by_role("button", name="Add Book to Catalog").click()
    
    expect(page.get_by_text("Book \"Test Book\" has been")).to_be_visible()
    
    page.get_by_role("cell", name="Test Book").click()
    page.get_by_role("cell", name="/5 Available").click()
    page.get_by_role("row", name="4 Test Book Test Author").get_by_placeholder("Patron ID (6 digits)").click()
    page.get_by_role("row", name="4 Test Book Test Author").get_by_placeholder("Patron ID (6 digits)").fill("123456")
    page.get_by_role("cell", name="123456 Borrow").get_by_role("button").click()
    
    expect(page.get_by_text("Successfully borrowed \"Test Book\"")).to_be_visible()
    expect(page.get_by_text("4/5 Available")).to_be_visible()

# Testing borrowing and returning a book.
def test_workflow_2(page):
    page.goto('http://localhost:2812/catalog')

    expect(page.get_by_role("cell", name="The Great Gatsby")).to_be_visible()

    page.get_by_role("row", name="1 The Great Gatsby F. Scott").get_by_placeholder("Patron ID (6 digits)").click()
    page.get_by_role("row", name="1 The Great Gatsby F. Scott").get_by_placeholder("Patron ID (6 digits)").fill("123456")
    page.get_by_role("cell", name="123456 Borrow").get_by_role("button").click()
    
    page.get_by_role("link", name="↩️ Return Book").click()
    page.get_by_role("textbox", name="Patron ID *").click()
    page.get_by_role("textbox", name="Patron ID *").fill("123456")
    page.get_by_role("spinbutton", name="Book ID *").click()
    page.get_by_role("spinbutton", name="Book ID *").fill("1")
    page.get_by_role("button", name="Process Return").click()
    
    expect(page.get_by_text("Book returned successfully.")).to_be_visible()