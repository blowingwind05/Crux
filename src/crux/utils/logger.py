"""
阶段日志收集器

提供结构化日志收集功能，支持前端展示
"""

import time
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StageLog:
    """阶段日志条目"""
    level: Literal["INFO", "WARN", "ERROR", "DEBUG"] = "INFO"
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class StageLogger:
    """
    阶段日志收集器
    
    收集节点执行过程中的日志，便于返回给前端展示
    """
    
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.logs: List[StageLog] = []
        self.start_time: float = time.time()
    
    def info(self, message: str, details: Optional[Dict[str, Any]] = None):
        """记录 INFO 级别日志"""
        self._add_log("INFO", message, details)
    
    def warn(self, message: str, details: Optional[Dict[str, Any]] = None):
        """记录 WARN 级别日志"""
        self._add_log("WARN", message, details)
    
    def error(self, message: str, details: Optional[Dict[str, Any]] = None):
        """记录 ERROR 级别日志"""
        self._add_log("ERROR", message, details)
    
    def debug(self, message: str, details: Optional[Dict[str, Any]] = None):
        """记录 DEBUG 级别日志"""
        self._add_log("DEBUG", message, details)
    
    def _add_log(
        self, 
        level: Literal["INFO", "WARN", "ERROR", "DEBUG"], 
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """添加日志条目"""
        log = StageLog(
            level=level,
            message=message,
            timestamp=time.time(),
            details=details,
        )
        self.logs.append(log)
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """获取所有日志（字典格式）"""
        return [log.to_dict() for log in self.logs]
    
    def get_duration_ms(self) -> float:
        """获取执行时长（毫秒）"""
        return (time.time() - self.start_time) * 1000
    
    def clear(self):
        """清空日志"""
        self.logs.clear()
        self.start_time = time.time()


# 全局日志存储（按阶段）
_stage_loggers: Dict[str, StageLogger] = {}


def get_stage_logger(stage_name: str) -> StageLogger:
    """获取指定阶段的日志收集器"""
    if stage_name not in _stage_loggers:
        _stage_loggers[stage_name] = StageLogger(stage_name)
    return _stage_loggers[stage_name]


def clear_all_loggers():
    """清空所有日志收集器"""
    _stage_loggers.clear()


def collect_all_logs() -> Dict[str, List[Dict[str, Any]]]:
    """收集所有阶段的日志"""
    return {
        name: logger.get_logs()
        for name, logger in _stage_loggers.items()
    }
