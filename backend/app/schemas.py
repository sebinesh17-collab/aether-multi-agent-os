from pydantic import BaseModel, EmailStr, Field
class LoginIn(BaseModel): email: EmailStr; password: str = Field(min_length=8, max_length=200)
class ProjectIn(BaseModel): name: str = Field(min_length=2, max_length=240); brief: str = Field(min_length=10, max_length=50000); completion_email: EmailStr
class SecretIn(BaseModel): name: str = Field(min_length=3, max_length=100); value: str = Field(min_length=1, max_length=200000)
class DecisionIn(BaseModel): project_id: int; subject: str; proposals: list[dict]; critical: bool = False
class DebateIn(BaseModel): project_id: int; subject: str = Field(min_length=5, max_length=500); context: str = Field(min_length=10, max_length=20000); critical: bool = False
class TerminalIn(BaseModel): workspace_id: str; command: str
