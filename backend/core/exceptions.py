"""
Backend Core Exceptions

自定义异常类
"""


class CruxException(Exception):
    """Crux 基础异常"""
    
    def __init__(self, message: str, code: str = "CRUX_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class PipelineError(CruxException):
    """管线执行异常"""
    
    def __init__(self, message: str, stage: str = None):
        self.stage = stage
        super().__init__(message, code="PIPELINE_ERROR")


class ValidationError(CruxException):
    """数据验证异常"""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, code="VALIDATION_ERROR")


class LLMError(CruxException):
    """LLM 调用异常"""
    
    def __init__(self, message: str):
        super().__init__(message, code="LLM_ERROR")


class DataSourceError(CruxException):
    """数据源异常"""
    
    def __init__(self, message: str, source_type: str = None):
        self.source_type = source_type
        super().__init__(message, code="DATASOURCE_ERROR")
