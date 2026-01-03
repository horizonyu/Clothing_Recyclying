"""
通用Schema
"""
from pydantic import BaseModel
from typing import Any, Optional


class ResponseModel(BaseModel):
    """统一响应模型"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: list
    total: int
    page: int
    page_size: int
    pages: int

