import pytest
from unittest.mock import Mock
from services.library_service import pay_late_fees, refund_late_fee_payment
from services.payment_service import PaymentGateway

def test_pay_late_fees_success(mocker):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 10.00})
    mocker.patch('services.library_service.get_book_by_id', return_value={'id': 1, 'title': 'A Brief History of Time'})
    
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (True, "txn_123456_", "Success")
    
    success, message, txn_id = pay_late_fees("123456", 1, mock_gateway)
    
    assert success is True
    assert "txn_123456" in txn_id
    assert "Payment successful" in message
    
    mock_gateway.process_payment.assert_called_once_with(
        patron_id="123456",
        amount=10.00,
        description="Late fees for 'A Brief History of Time'"
    )

def test_pay_late_fees_payment_declined(mocker):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 10.00})
    mocker.patch('services.library_service.get_book_by_id', return_value={'id': 1, 'title': 'A Brief History of Time'})

    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (False, "", "Card declined")

    success, message, txn_id = pay_late_fees("123456", 1, mock_gateway)

    assert success is False
    assert txn_id is None
    assert "Payment failed" in message
    assert "Card declined" in message

    mock_gateway.process_payment.assert_called_once_with(
        patron_id="123456",
        amount=10.00,
        description="Late fees for 'A Brief History of Time'"
    )

def test_pay_late_fees_invalid_patron_id(mocker):
    mock_gateway = Mock(spec=PaymentGateway)

    success, message, txn_id = pay_late_fees("12abc", 1, mock_gateway)

    assert success is False
    assert txn_id is None
    assert "Invalid patron ID" in message

    mock_gateway.process_payment.assert_not_called()

def test_pay_late_fees_zero_late_fees(mocker):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 0.00})
    mocker.patch('services.library_service.get_book_by_id', return_value={'id': 1, 'title': 'A Brief History of Time'})
    mock_gateway = Mock(spec=PaymentGateway)

    success, message, txn_id = pay_late_fees("123456", 1, mock_gateway)

    assert success is False
    assert txn_id is None
    assert "No late fees" in message

    mock_gateway.process_payment.assert_not_called()

def test_pay_late_fees_network_error(mocker):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 10.00})
    mocker.patch('services.library_service.get_book_by_id', return_value={'id': 1, 'title': 'A Brief History of Time'})

    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.side_effect = Exception("Network timeout")

    success, message, txn_id = pay_late_fees("123456", 1, mock_gateway)

    assert success is False
    assert txn_id is None
    assert "Payment processing error" in message
    assert "Network timeout" in message

    mock_gateway.process_payment.assert_called_once_with(
        patron_id="123456",
        amount=10.00,
        description="Late fees for 'A Brief History of Time'"
    )

def test_pay_late_fees_malformed_late_fee_return(mocker):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={})
    mocker.patch('services.library_service.get_book_by_id', return_value={'id': 1, 'title': 'A Brief History of Time'})

    mock_gateway = Mock(spec=PaymentGateway)

    success, message, txn_id = pay_late_fees("123456", 1, mock_gateway)

    assert success == False
    assert "Unable to calculate late fees" in message
    assert not txn_id

def test_pay_late_fees_book_not_found(mocker):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 10.00})
    mocker.patch('services.library_service.get_book_by_id', return_value={})

    mock_gateway = Mock(spec=PaymentGateway)

    success, message, txn_id = pay_late_fees("123456", 1, mock_gateway)

    assert success == False
    assert "Book not found" in message
    assert not txn_id

    mock_gateway.assert_not_called()

def test_refund_late_fee_payment_success():
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (True, "Refund successful")

    success, message = refund_late_fee_payment("txn_123", 10.00, mock_gateway)

    assert success is True
    assert "Refund successful" in message

    mock_gateway.refund_payment.assert_called_once_with("txn_123", 10.00)

def test_refund_late_fee_payment_invalid_transaction_id():
    """Test that invalid transaction IDs are rejected before reaching the gateway."""
    mock_gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("bad_txn", 10.00, mock_gateway)

    assert success is False
    assert "Invalid transaction ID" in message

    mock_gateway.refund_payment.assert_not_called()

# This format allows three different tests in one format, for the three different values ranges.
@pytest.mark.parametrize("amount, expected_msg", [
    (-5.00, "greater than 0"),
    (0.00, "greater than 0"),
    (20.00, "exceeds maximum"),
])
def test_refund_late_fee_payment_invalid_amounts(amount, expected_msg):
    mock_gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("txn_123", amount, mock_gateway)

    assert success is False
    assert expected_msg in message

    mock_gateway.refund_payment.assert_not_called()

def test_refund_payment_failure():
    mock_gateway = Mock(spec=PaymentGateway)

    mock_gateway.refund_payment.return_value = {False, "Insufficient funds"}

    success, message = refund_late_fee_payment("txn_123", 10, mock_gateway)

    assert success == False
    assert "Refund failed: Insufficient funds" in message

    mock_gateway.assert_not_called()

def test_refund_payment_exception():
    mock_gateway = Mock(spec=PaymentGateway)

    mock_gateway.refund_payment.side_effect = Exception("Network error")

    success, message = refund_late_fee_payment("txn_123", 10, mock_gateway)

    mock_gateway.refund_payment.assert_called_once_with("txn_123", 10)

    assert success == False
    assert "Refund processing error: Network error" in message