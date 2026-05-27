from __future__ import annotations

from enum import Enum


class ErrorCode(Enum):
    """错误码枚举"""
    
    # 业务错误 (1000-1999)
    VALIDATION_ERROR = 1001
    RESOURCE_NOT_FOUND = 1002
    DUPLICATE_RESOURCE = 1003
    INVALID_OPERATION = 1004
    FORCE_UPDATE_REQUIRED = 1005
    
    # 系统错误 (2000-2999)
    FILE_IO_ERROR = 2001
    DATABASE_ERROR = 2002
    EXTERNAL_SERVICE_ERROR = 2003
    
    # 未知错误
    UNKNOWN_ERROR = 9999


class DomainError(Exception):
    """领域错误基类"""
    
    def __init__(self, code: ErrorCode, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> dict:
        """转换为字典格式，用于 RPC 响应"""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details
        }


class ValidationError(DomainError):
    """验证错误"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(ErrorCode.VALIDATION_ERROR, message, details)


class ResourceNotFoundError(DomainError):
    """资源不存在错误"""
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} 不存在: {resource_id}"
        details = {"resource_type": resource_type, "resource_id": resource_id}
        super().__init__(ErrorCode.RESOURCE_NOT_FOUND, message, details)


class FileIOError(DomainError):
    """文件 I/O 错误"""
    
    def __init__(self, message: str, file_path: str = None):
        details = {"file_path": file_path} if file_path else {}
        super().__init__(ErrorCode.FILE_IO_ERROR, message, details)
