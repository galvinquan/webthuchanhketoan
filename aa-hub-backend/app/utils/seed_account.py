from app.db.database import SessionLocal
from app.models.account import Account

ACCOUNTS = [
    {
        "number": "1111",
        "name": "Tiền mặt",
        "level": 2,
        "parent_number": None,
        "acct_class": 1,
        "balance_nature": "DEBIT",
    },
    {
        "number": "1121",
        "name": "Tiền gửi ngân hàng",
        "level": 2,
        "parent_number": None,
        "acct_class": 1,
        "balance_nature": "DEBIT",
    },
    {
        "number": "131",
        "name": "Phải thu khách hàng",
        "level": 1,
        "parent_number": None,
        "acct_class": 1,
        "balance_nature": "DEBIT",
    },
    {
        "number": "331",
        "name": "Phải trả nhà cung cấp",
        "level": 1,
        "parent_number": None,
        "acct_class": 3,
        "balance_nature": "CREDIT",
    },
    {
        "number": "333",
        "name": "Thuế và các khoản phải nộp",
        "level": 1,
        "parent_number": None,
        "acct_class": 3,
        "balance_nature": "CREDIT",
    },
    {
        "number": "411",
        "name": "Vốn chủ sở hữu",
        "level": 1,
        "parent_number": None,
        "acct_class": 4,
        "balance_nature": "CREDIT",
    },
    {
        "number": "421",
        "name": "Lợi nhuận chưa phân phối",
        "level": 1,
        "parent_number": None,
        "acct_class": 4,
        "balance_nature": "CREDIT",
    },
    {
        "number": "511",
        "name": "Doanh thu bán hàng",
        "level": 1,
        "parent_number": None,
        "acct_class": 5,
        "balance_nature": "CREDIT",
    },
    {
        "number": "515",
        "name": "Doanh thu tài chính",
        "level": 1,
        "parent_number": None,
        "acct_class": 5,
        "balance_nature": "CREDIT",
    },
    {
        "number": "521",
        "name": "Giảm trừ doanh thu",
        "level": 1,
        "parent_number": None,
        "acct_class": 5,
        "balance_nature": "DEBIT",
    },
    {
        "number": "632",
        "name": "Giá vốn hàng bán",
        "level": 1,
        "parent_number": None,
        "acct_class": 6,
        "balance_nature": "DEBIT",
    },
    {
        "number": "635",
        "name": "Chi phí tài chính",
        "level": 1,
        "parent_number": None,
        "acct_class": 6,
        "balance_nature": "DEBIT",
    },
    {
        "number": "641",
        "name": "Chi phí bán hàng",
        "level": 1,
        "parent_number": None,
        "acct_class": 6,
        "balance_nature": "DEBIT",
    },
    {
        "number": "642",
        "name": "Chi phí quản lý doanh nghiệp",
        "level": 1,
        "parent_number": None,
        "acct_class": 6,
        "balance_nature": "DEBIT",
    },
    {
        "number": "711",
        "name": "Thu nhập khác",
        "level": 1,
        "parent_number": None,
        "acct_class": 7,
        "balance_nature": "CREDIT",
    },
    {
        "number": "811",
        "name": "Chi phí khác",
        "level": 1,
        "parent_number": None,
        "acct_class": 8,
        "balance_nature": "DEBIT",
    },
    {
        "number": "821",
        "name": "Chi phí thuế TNDN",
        "level": 1,
        "parent_number": None,
        "acct_class": 8,
        "balance_nature": "DEBIT",
    },
]


def seed_accounts():
    db = SessionLocal()

    try:
        created = 0

        for acc in ACCOUNTS:
            existing = db.get(Account, acc["number"])

            if existing:
                continue

            db.add(Account(**acc))
            created += 1

        db.commit()

        print(f"Seed thành công {created} tài khoản")

    finally:
        db.close()


if __name__ == "__main__":
    seed_accounts()