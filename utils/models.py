from app import db,app
import uuid
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import types, Integer, String, ForeignKey, Boolean
from datetime import datetime
from dataclasses import dataclass


@dataclass
class User(db.Model):
    __tablename__ = "Users"
    id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(types.DateTime, default=datetime.now())

    # --- RELATIONSHIPS ---
    Resumes: Mapped[list["Resume"]] = relationship(back_populates="User")
    job_applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="User"
    )


@dataclass
class Resume(db.Model):
    __tablename__ = "Resumes"
    resume_id: Mapped[uuid.UUID] = mapped_column(
        types.UUID,  # Note: types.Uuid and types.UUID are interchangeable
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        types.UUID,
        ForeignKey("Users.id"),  # <-- FIX: Added target "Users.id"
    )
    resume_text: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        types.DateTime, default=datetime.now()
    )

    # --- RELATIONSHIPS ---
    User: Mapped["User"] = relationship(
        back_populates="Resumes"
    )  # <-- FIX: Renamed from 'Users'
    job_applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="Resume"
    )


@dataclass
class JobDescription(db.Model):
    __tablename__ = "JobDescriptions"
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid, primary_key=True, default=uuid.uuid4
    )
    job_title: Mapped[str] = mapped_column(String, nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=True)
    job_desc: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(types.DateTime, default=datetime.now())

    # --- RELATIONSHIPS ---
    job_applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="JobDescription"
    )


@dataclass
class JobApplication(db.Model):
    __tablename__ = "JobApplications"
    application_id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid,
        default=uuid.uuid4,
        primary_key=True,  # <-- FIX: Added missing primary key
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid,
        ForeignKey("Users.id"),  # <-- FIX: Added target
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        types.UUID,
        ForeignKey("Resumes.resume_id"),  # <-- FIX: Added target
    )
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        types.UUID,
        ForeignKey("JobDescriptions.job_description_id"),  # <-- FIX: Added target
    )
    ats_score: Mapped[int] = mapped_column(Integer, nullable=False)
    certifications_count: Mapped[int] = mapped_column(Integer, nullable=False)
    keyword_analysis: Mapped[str] = mapped_column(
        String, nullable=True
    )  # Added nullable=True
    analysis_summary: Mapped[str] = mapped_column(
        String, nullable=True
    )  # Added nullable=True
    created_at: Mapped[datetime] = mapped_column(types.DateTime, default=datetime.now())

    # --- RELATIONSHIPS ---
    User: Mapped["User"] = relationship(
        back_populates="job_applications"
    )  # <-- FIX: Changed from 'Users'
    Resume: Mapped["Resume"] = relationship(back_populates="job_applications")
    JobDescription: Mapped["JobDescription"] = relationship(
        back_populates="job_applications"
    )
    mock_interviews: Mapped[list["MockInterview"]] = relationship(
        back_populates="JobApplication"
    )


@dataclass
class MockInterview(db.Model):
    __tablename__ = "MockInterviews"
    interview_id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid, default=uuid.uuid4, primary_key=True
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid,
        ForeignKey("JobApplications.application_id"),  # <-- FIX: Added target
    )
    status: Mapped[str] = mapped_column(String, default="Pending")
    overall_feedback: Mapped[str] = mapped_column(
        String, nullable=True
    )  # Added nullable=True
    completed_at: Mapped[datetime] = mapped_column(
        types.DateTime, default=datetime.now()
    )

    # --- RELATIONSHIPS ---
    JobApplication: Mapped["JobApplication"] = relationship(
        back_populates="mock_interviews"
    )
    questions: Mapped[list["InterviewQuestion"]] = relationship(
        back_populates="MockInterview"
    )


@dataclass
class InterviewQuestion(db.Model):
    __tablename__ = "InterviewQuestions"
    question_id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid, primary_key=True, default=uuid.uuid4
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid,
        ForeignKey("MockInterviews.interview_id"),  # <-- FIX: Added target
    )
    question_text: Mapped[str] = mapped_column(String)

    # --- RELATIONSHIPS ---
    MockInterview: Mapped["MockInterview"] = relationship(back_populates="questions")
    answers: Mapped[list["InterviewAnswer"]] = relationship(
        back_populates="InterviewQuestion"
    )


@dataclass
class InterviewAnswer(db.Model):
    __tablename__ = "InterviewAnswers"
    answer_id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid, primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid,
        ForeignKey("InterviewQuestions.question_id"),  # <-- FIX: Added target
    )
    transcription: Mapped[str] = mapped_column(String, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    vocal_analysis: Mapped[str] = mapped_column(String, default="")

    # --- RELATIONSHIPS ---
    InterviewQuestion: Mapped["InterviewQuestion"] = relationship(
        back_populates="answers"
    )


# --- DATABASE CREATION ---


def create_tables():
    print("Creating tables...")
    with app.app_context():
        db.create_all()
        db.session.commit()
    print("Tables created successfully.")
