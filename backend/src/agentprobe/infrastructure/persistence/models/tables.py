"""SQLAlchemy ORM table definitions for AgentProbe persistence."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Declarative base for all AgentProbe ORM models."""


class UserModel(Base):
    """ORM model for the ``users`` table."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    api_keys: Mapped[list["ApiKeyModel"]] = relationship(
        "ApiKeyModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"<UserModel id={self.id!r} email={self.email!r}>"


class ApiKeyModel(Base):
    """ORM model for the ``api_keys`` table."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="api_keys")

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"<ApiKeyModel id={self.id} user_id={self.user_id!r}>"


class RunModel(Base):
    """ORM model for the ``runs`` table.

    Stores the top-level metadata of each agent execution including
    query, model, status, performance metrics, and outcome.
    """

    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    model_id: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="running")
    final_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    succeeded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    steps: Mapped[list["StepModel"]] = relationship(
        "StepModel",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="StepModel.step_index",
    )
    failures: Mapped[list["FailureModel"]] = relationship(
        "FailureModel",
        back_populates="run",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"<RunModel id={self.id!r} status={self.status!r}>"


class StepModel(Base):
    """ORM model for the ``steps`` table.

    Represents a single step in the ReAct agent loop, linked
    to its parent run.
    """

    __tablename__ = "steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_args: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_type: Mapped[str] = mapped_column(String, nullable=False, default="none")
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)

    run: Mapped["RunModel"] = relationship("RunModel", back_populates="steps")

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return (
            f"<StepModel id={self.id} run_id={self.run_id!r} "
            f"index={self.step_index}>"
        )


class FailureModel(Base):
    """ORM model for the ``failures`` table.

    Records discrete failure events with optional links to the
    specific step where the failure was detected.
    """

    __tablename__ = "failures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    step_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("steps.id", ondelete="SET NULL"), nullable=True
    )
    failure_type: Mapped[str] = mapped_column(String, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped["RunModel"] = relationship("RunModel", back_populates="failures")

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return (
            f"<FailureModel id={self.id} type={self.failure_type!r} "
            f"run_id={self.run_id!r}>"
        )


class CustomToolModel(Base):
    """ORM model for the ``custom_tools`` table."""

    __tablename__ = "custom_tools"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    args_schema: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tool_type: Mapped[str] = mapped_column(String, nullable=False, default="static")
    config: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"<CustomToolModel id={self.id!r} name={self.name!r}>"


class PromptTemplateModel(Base):
    """ORM model for the ``prompt_templates`` table."""

    __tablename__ = "prompt_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"<PromptTemplateModel id={self.id!r} name={self.name!r}>"


class MemoryEntryModel(Base):
    """ORM model for the ``memory_entries`` table."""

    __tablename__ = "memory_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    source_run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"<MemoryEntryModel id={self.id!r} key={self.key!r}>"


class BenchmarkCaseModel(Base):
    """ORM model for the ``benchmark_cases`` table.

    Stores test-case definitions used by the benchmarking system.
    """

    __tablename__ = "benchmark_cases"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    difficulty: Mapped[str] = mapped_column(String, nullable=False)
    expected_answer: Mapped[str] = mapped_column(Text, nullable=False)
    expected_tools: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    results: Mapped[list["BenchmarkResultModel"]] = relationship(
        "BenchmarkResultModel",
        back_populates="case",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"<BenchmarkCaseModel id={self.id!r} category={self.category!r}>"


class BenchmarkSuiteModel(Base):
    """ORM model for the ``benchmark_suites`` table.

    Groups benchmark results for a specific model and provider run.
    """

    __tablename__ = "benchmark_suites"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    model_id: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_steps: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    failure_summary: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    results: Mapped[list["BenchmarkResultModel"]] = relationship(
        "BenchmarkResultModel",
        back_populates="suite",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return (
            f"<BenchmarkSuiteModel id={self.id!r} model={self.model_id!r} "
            f"status={self.status!r}>"
        )


class BenchmarkResultModel(Base):
    """ORM model for the ``benchmark_results`` table.

    Stores the outcome of running a single benchmark case within a suite.
    """

    __tablename__ = "benchmark_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    suite_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("benchmark_suites.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("benchmark_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    answer_correct: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    tools_correct: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    failures: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    suite: Mapped["BenchmarkSuiteModel"] = relationship(
        "BenchmarkSuiteModel", back_populates="results"
    )
    case: Mapped["BenchmarkCaseModel"] = relationship(
        "BenchmarkCaseModel", back_populates="results"
    )

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return (
            f"<BenchmarkResultModel id={self.id} suite={self.suite_id!r} "
            f"passed={self.passed}>"
        )
