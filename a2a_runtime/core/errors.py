"""Runtime exception hierarchy."""


class A2ARuntimeError(Exception):
    """Base class for all A2A runtime errors."""


class FrontmatterError(A2ARuntimeError):
    """Raised when Markdown frontmatter cannot be parsed or serialized."""


class SchemaError(A2ARuntimeError):
    """Raised when a file violates an A2A schema rule."""


class ValidationError(SchemaError):
    """Raised when validation fails and an exception is preferred."""


class WorkspaceError(A2ARuntimeError):
    """Raised when the workspace layout is invalid."""


class RepositoryError(A2ARuntimeError):
    """Raised when a repository cannot read or write its file."""


class StateMachineError(A2ARuntimeError):
    """Raised when a state transition is not allowed."""


class TaskIdentityError(A2ARuntimeError):
    """Raised when a task cannot be identified safely."""


class TaskIdentityAmbiguousError(TaskIdentityError):
    """Raised when more than one task exists and no active task is selected."""


class GateError(A2ARuntimeError):
    """Raised when a runtime gate rejects an operation."""


class BlockerError(A2ARuntimeError):
    """Raised when blocker handling fails."""


class RiskGateError(A2ARuntimeError):
    """Raised when a risk decision gate is required or invalid."""


class RiskDecisionError(RiskGateError):
    """Raised when a risk decision is invalid or cannot be applied."""


class ReviewError(A2ARuntimeError):
    """Raised when review record creation or review state flow fails."""


class FinalDeliveryError(A2ARuntimeError):
    """Raised when final delivery gates fail."""
