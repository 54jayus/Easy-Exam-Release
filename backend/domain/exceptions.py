from __future__ import annotations


class DomainError(Exception):
    """业务规则违反，返回给用户的友好错误信息。"""


class ValidationError(DomainError):
    """输入数据验证失败。"""


class NotFoundError(DomainError):
    """请求的资源不存在。"""


class ConflictError(DomainError):
    """操作与当前状态冲突。"""
