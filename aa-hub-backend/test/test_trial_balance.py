from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login():
    response = client.post(
        "/api/auth/login",
        json={
            "username": "test1",
            "password": "123"
        }
    )

    assert response.status_code == 200


def test_trial_balance_is_balanced():
    """
    Verify Trial Balance satisfies accounting equation:

        Total Debit == Total Credit

    Including:
    - Opening balances
    - Period movements
    """

    login()

    response = client.get(
        "/api/reports/trial-balance"
    )

    assert response.status_code == 200

    rows = response.json()["rows"]

    total_opening_debit = 0
    total_opening_credit = 0

    total_period_debit = 0
    total_period_credit = 0

    total_closing_debit = 0
    total_closing_credit = 0

    for row in rows:

        total_opening_debit += row["opening_debit"]
        total_opening_credit += row["opening_credit"]

        total_period_debit += row["period_debit"]
        total_period_credit += row["period_credit"]

        total_closing_debit += row["closing_debit"]
        total_closing_credit += row["closing_credit"]

    # Opening balances must balance
    assert (
        total_opening_debit
        ==
        total_opening_credit
    )

    # Period movements must balance
    assert (
        total_period_debit
        ==
        total_period_credit
    )

    # Closing balances must balance
    assert (
        total_closing_debit
        ==
        total_closing_credit
    )

    # Full equation
    assert (
        total_opening_debit
        +
        total_period_debit
        ==
        total_opening_credit
        +
        total_period_credit
    )