from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


# Enums for status and type fields
class FileStatus(str, Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class ChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SearchStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class VideoEditType(str, Enum):
    TRIM = "trim"
    MERGE = "merge"
    FILTER = "filter"
    ENHANCE = "enhance"
    CUSTOM = "custom"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True)
    email: str = Field(max_length=255, unique=True, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    full_name: str = Field(max_length=200)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Storage quota in bytes
    storage_quota: int = Field(default=5368709120)  # 5GB default
    storage_used: int = Field(default=0)

    # Relationships
    uploaded_files: List["UploadedFile"] = Relationship(back_populates="user")
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")
    search_queries: List["SearchQuery"] = Relationship(back_populates="user")
    video_projects: List["VideoProject"] = Relationship(back_populates="user")


class UploadedFile(SQLModel, table=True):
    __tablename__ = "uploaded_files"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int = Field(ge=0)  # Size in bytes
    mime_type: str = Field(max_length=100)
    file_hash: str = Field(max_length=64)  # SHA-256 hash for deduplication
    status: FileStatus = Field(default=FileStatus.UPLOADING)
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata for different file types
    file_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # File processing results
    processed_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Relationships
    user: User = Relationship(back_populates="uploaded_files")
    chat_file_attachments: List["ChatFileAttachment"] = Relationship(back_populates="file")


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200, default="New Chat")
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    # AI model configuration
    ai_model: str = Field(max_length=100, default="gpt-3.5-turbo")
    system_prompt: str = Field(default="", max_length=2000)
    temperature: Decimal = Field(default=Decimal("0.7"))
    max_tokens: int = Field(default=2048)

    # Session settings
    settings: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Relationships
    user: User = Relationship(back_populates="chat_sessions")
    messages: List["ChatMessage"] = Relationship(back_populates="session")


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chat_sessions.id")
    role: ChatMessageRole = Field()
    content: str = Field(max_length=10000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Token usage tracking
    input_tokens: Optional[int] = Field(default=None, ge=0)
    output_tokens: Optional[int] = Field(default=None, ge=0)

    # Message metadata
    message_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Relationships
    session: ChatSession = Relationship(back_populates="messages")
    file_attachments: List["ChatFileAttachment"] = Relationship(back_populates="message")


class ChatFileAttachment(SQLModel, table=True):
    __tablename__ = "chat_file_attachments"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: int = Field(foreign_key="chat_messages.id")
    file_id: int = Field(foreign_key="uploaded_files.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    message: ChatMessage = Relationship(back_populates="file_attachments")
    file: UploadedFile = Relationship(back_populates="chat_file_attachments")


class SearchQuery(SQLModel, table=True):
    __tablename__ = "search_queries"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    query: str = Field(max_length=1000)
    status: SearchStatus = Field(default=SearchStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Search parameters
    search_engines: List[str] = Field(default=["google"], sa_column=Column(JSON))
    max_results: int = Field(default=10)
    language: str = Field(default="en", max_length=10)
    region: str = Field(default="us", max_length=10)

    # Search results
    results: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    results_count: int = Field(default=0, ge=0)

    # Error information
    error_message: Optional[str] = Field(default=None, max_length=1000)

    # Relationships
    user: User = Relationship(back_populates="search_queries")


class VideoProject(SQLModel, table=True):
    __tablename__ = "video_projects"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: str = Field(max_length=200)
    description: str = Field(default="", max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Project settings
    settings: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Relationships
    user: User = Relationship(back_populates="video_projects")
    video_files: List["VideoFile"] = Relationship(back_populates="project")
    edit_tasks: List["VideoEditTask"] = Relationship(back_populates="project")


class VideoFile(SQLModel, table=True):
    __tablename__ = "video_files"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="video_projects.id")
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int = Field(ge=0)
    duration: Optional[Decimal] = Field(default=None)  # Duration in seconds
    resolution: Optional[str] = Field(default=None, max_length=20)  # e.g., "1920x1080"
    fps: Optional[Decimal] = Field(default=None)
    codec: Optional[str] = Field(default=None, max_length=50)
    status: VideoStatus = Field(default=VideoStatus.UPLOADED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Video metadata
    video_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Relationships
    project: VideoProject = Relationship(back_populates="video_files")


class VideoEditTask(SQLModel, table=True):
    __tablename__ = "video_edit_tasks"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="video_projects.id")
    edit_type: VideoEditType = Field()
    status: VideoStatus = Field(default=VideoStatus.UPLOADED)
    user_prompt: str = Field(max_length=2000)  # User's natural language instruction
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Edit parameters (generated from user prompt)
    edit_parameters: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Processing results
    output_file_path: Optional[str] = Field(default=None, max_length=500)
    processing_log: str = Field(default="", max_length=5000)
    error_message: Optional[str] = Field(default=None, max_length=1000)

    # Progress tracking
    progress_percentage: Decimal = Field(default=Decimal("0"))

    # Relationships
    project: VideoProject = Relationship(back_populates="edit_tasks")


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    username: str = Field(max_length=50)
    email: str = Field(max_length=255)
    full_name: str = Field(max_length=200)
    storage_quota: Optional[int] = Field(default=5368709120)


class UserUpdate(SQLModel, table=False):
    username: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=200)
    is_active: Optional[bool] = Field(default=None)
    storage_quota: Optional[int] = Field(default=None)


class FileUploadRequest(SQLModel, table=False):
    filename: str = Field(max_length=255)
    file_size: int = Field(ge=0)
    mime_type: str = Field(max_length=100)


class ChatSessionCreate(SQLModel, table=False):
    title: Optional[str] = Field(default="New Chat", max_length=200)
    ai_model: Optional[str] = Field(default="gpt-3.5-turbo", max_length=100)
    system_prompt: Optional[str] = Field(default="", max_length=2000)
    temperature: Optional[Decimal] = Field(default=Decimal("0.7"))
    max_tokens: Optional[int] = Field(default=2048)


class ChatSessionUpdate(SQLModel, table=False):
    title: Optional[str] = Field(default=None, max_length=200)
    ai_model: Optional[str] = Field(default=None, max_length=100)
    system_prompt: Optional[str] = Field(default=None, max_length=2000)
    temperature: Optional[Decimal] = Field(default=None)
    max_tokens: Optional[int] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class ChatMessageCreate(SQLModel, table=False):
    role: ChatMessageRole = Field()
    content: str = Field(max_length=10000)
    file_ids: Optional[List[int]] = Field(default=[])


class SearchQueryCreate(SQLModel, table=False):
    query: str = Field(max_length=1000)
    search_engines: Optional[List[str]] = Field(default=["google"])
    max_results: Optional[int] = Field(default=10)
    language: Optional[str] = Field(default="en", max_length=10)
    region: Optional[str] = Field(default="us", max_length=10)


class VideoProjectCreate(SQLModel, table=False):
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default="", max_length=1000)


class VideoProjectUpdate(SQLModel, table=False):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class VideoEditTaskCreate(SQLModel, table=False):
    edit_type: VideoEditType = Field()
    user_prompt: str = Field(max_length=2000)


class VideoEditTaskUpdate(SQLModel, table=False):
    status: Optional[VideoStatus] = Field(default=None)
    edit_parameters: Optional[Dict[str, Any]] = Field(default=None)
    output_file_path: Optional[str] = Field(default=None, max_length=500)
    processing_log: Optional[str] = Field(default=None, max_length=5000)
    error_message: Optional[str] = Field(default=None, max_length=1000)
    progress_percentage: Optional[Decimal] = Field(default=None)
