from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.models import Company, LedgerEntry, OpeningBalance, Account, Voucher
from datetime import date
from typing import Optional

router = APIRouter(prefix="/api/reports", tags=["reports"])


def get_company_id(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(401, "Chưa đăng nhập")
    company = db.query(Company).filter(Company.user_id == int(user_id)).first()
    if not company:
        raise HTTPException(404, "Chưa có thông tin doanh nghiệp")
    return company.id


# ── 1. Nhật ký chung ──────────────────────────────────────────────────────────

@router.get("/journal")
def general_journal(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    q = db.query(LedgerEntry).filter(LedgerEntry.company_id == company_id)
    if from_date:
        q = q.filter(LedgerEntry.posting_date >= from_date)
    if to_date:
        q = q.filter(LedgerEntry.posting_date <= to_date)
    entries = q.order_by(LedgerEntry.posting_date).all()

    lines = []
    total_debit = 0
    total_credit = 0
    for e in entries:
        voucher = db.get(Voucher, e.voucher_id)
        lines.append({
            "posting_date": str(e.posting_date),
            "voucher_no": voucher.voucher_no if voucher else "",
            "voucher_type": voucher.voucher_type if voucher else "",
            "narration": e.narration,
            "debit_acct": e.debit_acct,
            "credit_acct": e.credit_acct,
            "amount": float(e.amount),
        })
        total_debit += float(e.amount)
        total_credit += float(e.amount)

    return {
        "lines": lines,
        "total_debit": total_debit,
        "total_credit": total_credit,
    }


# ── 2. Bảng cân đối số phát sinh ─────────────────────────────────────────────

@router.get("/trial-balance")
def trial_balance(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    accounts = db.query(Account).order_by(Account.number).all()
    opening_rows = db.query(OpeningBalance).filter(
        OpeningBalance.company_id == company_id
    ).all()
    opening_map = {r.account_number: (float(r.debit), float(r.credit)) for r in opening_rows}

    entries = db.query(LedgerEntry).filter(LedgerEntry.company_id == company_id)
    if from_date:
        entries = entries.filter(LedgerEntry.posting_date >= from_date)
    if to_date:
        entries = entries.filter(LedgerEntry.posting_date <= to_date)
    entries = entries.all()

    debit_map = {}
    credit_map = {}
    for e in entries:
        debit_map[e.debit_acct] = debit_map.get(e.debit_acct, 0) + float(e.amount)
        credit_map[e.credit_acct] = credit_map.get(e.credit_acct, 0) + float(e.amount)

    rows = []
    for acct in accounts:
        od, oc = opening_map.get(acct.number, (0, 0))
        pd = debit_map.get(acct.number, 0)
        pc = credit_map.get(acct.number, 0)
        if od == 0 and oc == 0 and pd == 0 and pc == 0:
            continue
        net = (od - oc) + (pd - pc)
        cd = max(net, 0)
        cc = max(-net, 0)
        rows.append({
            "account_number": acct.number,
            "account_name": acct.name,
            "opening_debit": od,
            "opening_credit": oc,
            "period_debit": pd,
            "period_credit": pc,
            "closing_debit": cd,
            "closing_credit": cc,
        })

    return {"rows": rows}


# ── 3. Kết quả kinh doanh ─────────────────────────────────────────────────────

@router.get("/income-statement")
def income_statement(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    entries = db.query(LedgerEntry).filter(LedgerEntry.company_id == company_id)
    if from_date:
        entries = entries.filter(LedgerEntry.posting_date >= from_date)
    if to_date:
        entries = entries.filter(LedgerEntry.posting_date <= to_date)
    entries = entries.all()

    debit_map = {}
    credit_map = {}
    for e in entries:
        debit_map[e.debit_acct] = debit_map.get(e.debit_acct, 0) + float(e.amount)
        credit_map[e.credit_acct] = credit_map.get(e.credit_acct, 0) + float(e.amount)

    def c(acct): return credit_map.get(acct, 0)
    def d(acct): return debit_map.get(acct, 0)

    dt_ban_hang = c("511")
    giam_tru = d("521")
    dt_thuan = dt_ban_hang - giam_tru
    gia_von = d("632")
    ln_gop = dt_thuan - gia_von
    dt_tai_chinh = c("515")
    cp_tai_chinh = d("635")
    cp_ban_hang = d("641")
    cp_quan_ly = d("642")
    ln_thuan = ln_gop + dt_tai_chinh - cp_tai_chinh - cp_ban_hang - cp_quan_ly
    thu_nhap_khac = c("711")
    cp_khac = d("811")
    ln_khac = thu_nhap_khac - cp_khac
    ln_truoc_thue = ln_thuan + ln_khac
    thue_tndn = d("821")
    ln_sau_thue = ln_truoc_thue - thue_tndn

    return {
        "dt_ban_hang": dt_ban_hang,
        "giam_tru": giam_tru,
        "dt_thuan": dt_thuan,
        "gia_von": gia_von,
        "ln_gop": ln_gop,
        "dt_tai_chinh": dt_tai_chinh,
        "cp_tai_chinh": cp_tai_chinh,
        "cp_ban_hang": cp_ban_hang,
        "cp_quan_ly": cp_quan_ly,
        "ln_thuan": ln_thuan,
        "thu_nhap_khac": thu_nhap_khac,
        "cp_khac": cp_khac,
        "ln_khac": ln_khac,
        "ln_truoc_thue": ln_truoc_thue,
        "thue_tndn": thue_tndn,
        "ln_sau_thue": ln_sau_thue,
    }


# ── 4. Bảng cân đối kế toán ──────────────────────────────────────────────────

@router.get("/balance-sheet")
def balance_sheet(
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    opening_rows = db.query(OpeningBalance).filter(
        OpeningBalance.company_id == company_id
    ).all()
    opening_map = {r.account_number: (float(r.debit), float(r.credit)) for r in opening_rows}

    entries = db.query(LedgerEntry).filter(
        LedgerEntry.company_id == company_id
    ).all()

    debit_map = {}
    credit_map = {}
    for e in entries:
        debit_map[e.debit_acct] = debit_map.get(e.debit_acct, 0) + float(e.amount)
        credit_map[e.credit_acct] = credit_map.get(e.credit_acct, 0) + float(e.amount)

    def closing(acct):
        od, oc = opening_map.get(acct, (0, 0))
        return (od + debit_map.get(acct, 0)) - (oc + credit_map.get(acct, 0))

    tien_mat = closing("1111")
    tien_gui = closing("1121")
    phai_thu_kh = closing("131")
    hang_ton_kho = closing("156")
    tscd = closing("211")
    hao_mon = closing("214")
    tong_tai_san = tien_mat + tien_gui + phai_thu_kh + hang_ton_kho + tscd - abs(hao_mon)

    phai_tra_ncc = abs(closing("331"))
    thue_phai_nop = abs(closing("333"))
    phai_tra_ldong = abs(closing("334"))
    tong_no_phai_tra = phai_tra_ncc + thue_phai_nop + phai_tra_ldong

    von_csh = abs(closing("411"))
    loi_nhuan = abs(closing("421"))
    tong_vcsh = von_csh + loi_nhuan

    tong_nguon_von = tong_no_phai_tra + tong_vcsh

    return {
        "tai_san": {
            "tien_mat": tien_mat,
            "tien_gui": tien_gui,
            "phai_thu_kh": phai_thu_kh,
            "hang_ton_kho": hang_ton_kho,
            "tscd": tscd,
            "hao_mon": hao_mon,
            "tong": tong_tai_san,
        },
        "nguon_von": {
            "phai_tra_ncc": phai_tra_ncc,
            "thue_phai_nop": thue_phai_nop,
            "phai_tra_ldong": phai_tra_ldong,
            "tong_no_phai_tra": tong_no_phai_tra,
            "von_csh": von_csh,
            "loi_nhuan": loi_nhuan,
            "tong_vcsh": tong_vcsh,
            "tong": tong_nguon_von,
        },
        "can_doi": abs(tong_tai_san - tong_nguon_von) < 1,
    }