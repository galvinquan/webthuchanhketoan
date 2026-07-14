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


def test_accounting_reconciliation():
    login()

    # -------- General Ledger --------

    ledger = client.get(
        "/api/reports/general-ledger/1111"
    )

    assert ledger.status_code == 200

    ledger_data = ledger.json()

    assert ledger_data["closing_balance"] == 700

    # -------- Trial Balance --------

    trial = client.get(
        "/api/reports/trial-balance"
    )

    assert trial.status_code == 200

    rows = trial.json()["rows"]

    cash = next(
        r for r in rows
        if r["account_number"] == "1111"
    )

    revenue = next(
        r for r in rows
        if r["account_number"] == "511"
    )

    expense = next(
        r for r in rows
        if r["account_number"] == "811"
    )

    assert cash["closing_debit"] == 700

    assert revenue["period_credit"] == 1000

    assert expense["period_debit"] == 300

    # -------- Income Statement --------

    report = client.get(
        "/api/reports/income-statement"
    )

    assert report.status_code == 200

    income = report.json()

    assert income["dt_ban_hang"] == 1000

    assert income["cp_khac"] == 300

    assert income["ln_truoc_thue"] == 700

    # -------- Reconciliation --------

    assert (
        ledger_data["closing_balance"]
        ==
        cash["closing_debit"]
    )

    assert (
        income["dt_ban_hang"]
        ==
        revenue["period_credit"]
    )

    assert (
        income["cp_khac"]
        ==
        expense["period_debit"]
    )

    assert (
        income["dt_ban_hang"]
        -
        income["cp_khac"]
        ==
        income["ln_truoc_thue"]
    )