from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, selectinload
from datetime import datetime, timezone

from app.db.database import get_db
from app.models import (
    User, ClassRoom, ClassTeacher, Enrollment, Assignment, Company,
)
from app.models.classroom import generate_join_code
from app.schemas.classroom import (
    ClassCreate, ClassOut, ClassDetailOut, JoinClassRequest,
    AddCoTeacherRequest, CoTeacherOut, StudentInClassOut, StudentSubmissionOut,
)
from app.schemas.assignment import AssignmentCreate, AssignmentOut
from app.schemas.company import CompanyOut, GradeRequest

router = APIRouter(prefix="/api/classes", tags=["classes"])


# ---------- auth dependencies ----------

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(401, "Chưa đăng nhập")
    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(401, "User không tồn tại")
    return user


def require_teacher(user: User = Depends(get_current_user)) -> User:
    if user.role != "teacher":
        raise HTTPException(403, "Chỉ giáo viên mới có quyền thực hiện thao tác này")
    return user


def require_student(user: User = Depends(get_current_user)) -> User:
    if user.role != "student":
        raise HTTPException(403, "Chỉ sinh viên mới có quyền thực hiện thao tác này")
    return user


# ---------- helpers ----------

def _generate_unique_join_code(db: Session) -> str:
    for _ in range(20):
        code = generate_join_code()
        if not db.query(ClassRoom).filter(ClassRoom.join_code == code).first():
            return code
    raise HTTPException(500, "Không thể sinh mã lớp, thử lại sau")


def _get_class_teacher_link(db: Session, class_id: int, teacher_id: int):
    return (
        db.query(ClassTeacher)
        .filter(ClassTeacher.class_id == class_id, ClassTeacher.teacher_id == teacher_id)
        .first()
    )


def _require_class_teacher(db: Session, class_id: int, teacher: User) -> ClassTeacher:
    """Owner hoặc co_teacher đều được xem/tạo bài tập/chấm điểm."""
    link = _get_class_teacher_link(db, class_id, teacher.id)
    if not link:
        raise HTTPException(403, "Bạn không phụ trách lớp này")
    return link


def _require_class_owner(db: Session, class_id: int, teacher: User) -> ClassTeacher:
    """Chỉ owner mới được xóa lớp / assign đồng giáo viên."""
    link = _require_class_teacher(db, class_id, teacher)
    if link.role != "owner":
        raise HTTPException(403, "Chỉ giáo viên chủ lớp mới có quyền thực hiện thao tác này")
    return link


def _get_class_or_404(db: Session, class_id: int) -> ClassRoom:
    classroom = db.query(ClassRoom).filter(ClassRoom.id == class_id).first()
    if not classroom:
        raise HTTPException(404, "Không tìm thấy lớp")
    return classroom


def _get_assignment_or_404(db: Session, assignment_id: int) -> Assignment:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(404, "Không tìm thấy bài tập")
    return assignment


# ---------- Giáo viên: tạo / xem / xóa lớp ----------

@router.post("", response_model=ClassOut)
def create_class(
    payload: ClassCreate,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    classroom = ClassRoom(
        name=payload.name,
        teacher_id=teacher.id,
        join_code=_generate_unique_join_code(db),
    )
    db.add(classroom)
    db.flush()  # để có classroom.id trước khi tạo ClassTeacher

    db.add(ClassTeacher(class_id=classroom.id, teacher_id=teacher.id, role="owner"))
    db.commit()
    db.refresh(classroom)
    return classroom


@router.get("/mine", response_model=list[ClassOut])
def list_my_classes(
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    return (
        db.query(ClassRoom)
        .join(ClassTeacher, ClassTeacher.class_id == ClassRoom.id)
        .filter(ClassTeacher.teacher_id == teacher.id)
        .all()
    )


@router.get("/{class_id}", response_model=ClassDetailOut)
def get_class_detail(
    class_id: int,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    _require_class_teacher(db, class_id, teacher)
    classroom = (
        db.query(ClassRoom)
        .options(
            selectinload(ClassRoom.enrollments).selectinload(Enrollment.user),
            selectinload(ClassRoom.assignments),
            selectinload(ClassRoom.class_teachers).selectinload(ClassTeacher.teacher),
        )
        .filter(ClassRoom.id == class_id)
        .first()
    )
    if not classroom:
        raise HTTPException(404, "Không tìm thấy lớp")

    assignment_ids = [a.id for a in classroom.assignments]
    companies = (
        db.query(Company).filter(Company.assignment_id.in_(assignment_ids)).all()
        if assignment_ids else []
    )
    subs_by_user: dict[int, dict[int, Company]] = {}
    for c in companies:
        subs_by_user.setdefault(c.user_id, {})[c.assignment_id] = c

    students = []
    for e in classroom.enrollments:
        if e.status != "active":
            continue
        user_subs = subs_by_user.get(e.user_id, {})
        submissions = [
            StudentSubmissionOut(
                assignment_id=a.id,
                company_id=user_subs[a.id].id if a.id in user_subs else None,
                status=user_subs[a.id].status if a.id in user_subs else None,
                score=float(user_subs[a.id].score) if a.id in user_subs and user_subs[a.id].score is not None else None,
            )
            for a in classroom.assignments
        ]
        students.append(StudentInClassOut(
            user_id=e.user_id,
            username=e.user.username,
            joined_at=e.joined_at,
            status=e.status,
            submissions=submissions,
        ))

    co_teachers = [
        CoTeacherOut(
            teacher_id=ct.teacher_id,
            username=ct.teacher.username,
            role=ct.role,
            added_at=ct.added_at,
        )
        for ct in classroom.class_teachers
    ]

    detail = ClassDetailOut.model_validate(classroom)
    detail.students = students
    detail.assignments = [AssignmentOut.model_validate(a) for a in classroom.assignments]
    detail.co_teachers = co_teachers
    return detail


@router.delete("/{class_id}")
def delete_class(
    class_id: int,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    _require_class_owner(db, class_id, teacher)
    classroom = _get_class_or_404(db, class_id)
    db.delete(classroom)
    db.commit()
    return {"message": "Đã xóa lớp"}


# ---------- Giáo viên: assign đồng giáo viên ----------

@router.post("/{class_id}/teachers", response_model=CoTeacherOut)
def add_co_teacher(
    class_id: int,
    payload: AddCoTeacherRequest,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    _require_class_owner(db, class_id, teacher)
    _get_class_or_404(db, class_id)

    target = db.query(User).filter(User.username == payload.username).first()
    if not target:
        raise HTTPException(404, "Không tìm thấy tài khoản với username này")
    if target.role != "teacher":
        raise HTTPException(400, "Tài khoản này không có role giáo viên")

    existing = _get_class_teacher_link(db, class_id, target.id)
    if existing:
        raise HTTPException(400, "Giáo viên này đã phụ trách lớp")

    link = ClassTeacher(class_id=class_id, teacher_id=target.id, role="co_teacher")
    db.add(link)
    db.commit()
    db.refresh(link)
    return CoTeacherOut(
        teacher_id=target.id, username=target.username,
        role=link.role, added_at=link.added_at,
    )


@router.delete("/{class_id}/teachers/{teacher_id}")
def remove_co_teacher(
    class_id: int,
    teacher_id: int,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    _require_class_owner(db, class_id, teacher)
    link = _get_class_teacher_link(db, class_id, teacher_id)
    if not link or link.role == "owner":
        raise HTTPException(404, "Không tìm thấy đồng giáo viên này")
    db.delete(link)
    db.commit()
    return {"message": "Đã gỡ đồng giáo viên"}


# ---------- Giáo viên: quản lý bài tập ----------

@router.post("/{class_id}/assignments", response_model=AssignmentOut)
def create_assignment(
    class_id: int,
    payload: AssignmentCreate,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    _require_class_teacher(db, class_id, teacher)
    _get_class_or_404(db, class_id)

    assignment = Assignment(
        class_id=class_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        created_by=teacher.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/{class_id}/assignments", response_model=list[AssignmentOut])
def list_assignments(
    class_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == "teacher":
        _require_class_teacher(db, class_id, user)
    else:
        enrolled = (
            db.query(Enrollment)
            .filter(Enrollment.class_id == class_id, Enrollment.user_id == user.id,
                     Enrollment.status == "active")
            .first()
        )
        if not enrolled:
            raise HTTPException(403, "Bạn chưa tham gia lớp này")

    return db.query(Assignment).filter(Assignment.class_id == class_id).all()


@router.delete("/{class_id}/assignments/{assignment_id}")
def delete_assignment(
    class_id: int,
    assignment_id: int,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    _require_class_teacher(db, class_id, teacher)
    assignment = _get_assignment_or_404(db, assignment_id)
    if assignment.class_id != class_id:
        raise HTTPException(404, "Bài tập không thuộc lớp này")
    db.delete(assignment)
    db.commit()
    return {"message": "Đã xóa bài tập"}


# ---------- Giáo viên: xem & chấm bài nộp ----------

@router.get("/assignments/{assignment_id}/submissions", response_model=list[CompanyOut])
def list_submissions(
    assignment_id: int,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    assignment = _get_assignment_or_404(db, assignment_id)
    _require_class_teacher(db, assignment.class_id, teacher)
    return db.query(Company).filter(Company.assignment_id == assignment_id).all()


@router.post("/submissions/{company_id}/grade", response_model=CompanyOut)
def grade_submission(
    company_id: int,
    payload: GradeRequest,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company or not company.assignment_id:
        raise HTTPException(404, "Không tìm thấy bài nộp")

    assignment = _get_assignment_or_404(db, company.assignment_id)
    _require_class_teacher(db, assignment.class_id, teacher)

    company.score = payload.score
    company.feedback = payload.feedback
    company.graded_by = teacher.id
    company.graded_at = datetime.now(timezone.utc)
    company.status = "graded"

    db.commit()
    db.refresh(company)
    return company


# ---------- Sinh viên: tham gia lớp bằng mã, xem lớp đã tham gia ----------

@router.post("/join", response_model=ClassOut)
def join_class(
    payload: JoinClassRequest,
    student: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    classroom = (
        db.query(ClassRoom)
        .filter(ClassRoom.join_code == payload.join_code.strip().upper())
        .first()
    )
    if not classroom:
        raise HTTPException(404, "Mã lớp không hợp lệ")

    existing = (
        db.query(Enrollment)
        .filter(Enrollment.class_id == classroom.id, Enrollment.user_id == student.id)
        .first()
    )
    if existing:
        if existing.status == "active":
            raise HTTPException(400, "Bạn đã tham gia lớp này rồi")
        existing.status = "active"
        db.commit()
        return classroom

    db.add(Enrollment(class_id=classroom.id, user_id=student.id, status="active"))
    db.commit()
    return classroom


@router.get("/joined/list", response_model=list[ClassOut])
def list_joined_classes(
    student: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    return (
        db.query(ClassRoom)
        .join(Enrollment, Enrollment.class_id == ClassRoom.id)
        .filter(Enrollment.user_id == student.id, Enrollment.status == "active")
        .all()
    )


@router.delete("/{class_id}/leave")
def leave_class(
    class_id: int,
    student: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.class_id == class_id, Enrollment.user_id == student.id)
        .first()
    )
    if not enrollment or enrollment.status != "active":
        raise HTTPException(404, "Bạn chưa tham gia lớp này")

    enrollment.status = "removed"
    db.commit()
    return {"message": "Đã rời lớp"}
