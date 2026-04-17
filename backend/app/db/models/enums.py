from __future__ import annotations

from enum import StrEnum


class ResumeSourceType(StrEnum):
    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    LINKEDIN_TEXT = "linkedin_text"
    IMPORTED = "imported"


class ParseStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_MANUAL_INPUT = "needs_manual_input"


class JobStatus(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class WorkMode(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class Seniority(StrEnum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    UNKNOWN = "unknown"


class MatchType(StrEnum):
    EXACT = "exact"
    ALIAS = "alias"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    MISSING = "missing"


class MatchStatus(StrEnum):
    STRONG = "strong"
    PARTIAL = "partial"
    WEAK = "weak"
    MISSING = "missing"


class AITaskType(StrEnum):
    RESUME_PARSE = "resume_parse"
    JOB_PARSE = "job_parse"
    EMBEDDING = "embedding"
    MATCH_EXPLAIN = "match_explain"
    RESUME_OPTIMIZE = "resume_optimize"
    TRUTH_GUARD = "truth_guard"
    JSON_REPAIR = "json_repair"
    EVAL = "eval"


class AIProvider(StrEnum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    OTHER = "other"


class AIRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    REPAIRED = "repaired"
    CANCELLED = "cancelled"


class ValidationStatus(StrEnum):
    NOT_VALIDATED = "not_validated"
    VALID = "valid"
    INVALID = "invalid"
    REPAIRED = "repaired"
