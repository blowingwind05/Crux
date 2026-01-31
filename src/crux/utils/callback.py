"""
流式回调模块

提供实时日志回调机制，支持异步日志收集和推送
"""

import asyncio
import time
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass, field
from queue import Queue
from threading import Lock


@dataclass
class LogEvent:
    """日志事件"""
    stage: str
    level: str  # INFO, WARN, ERROR, DEBUG
    message: str
    timestamp: float = field(default_factory=time.time)
    details: Optional[Dict[str, Any]] = None
    iteration: int = 0


class StreamCallback:
    """
    流式回调处理器
    
    用于在节点执行过程中实时收集日志，
    通过队列机制实现线程安全的异步日志推送。
    """
    
    def __init__(self):
        self._queue: Queue[LogEvent] = Queue()
        self._lock = Lock()
        self._current_stage: str = ""
        self._current_iteration: int = 0
        self._is_active: bool = True
    
    def set_stage(self, stage: str):
        """设置当前阶段"""
        with self._lock:
            self._current_stage = stage
    
    def set_iteration(self, iteration: int):
        """设置当前迭代"""
        with self._lock:
            self._current_iteration = iteration
    
    @property
    def current_stage(self) -> str:
        return self._current_stage
    
    @property
    def current_iteration(self) -> int:
        return self._current_iteration
    
    def on_log(
        self, 
        level: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        日志回调 - 由节点调用
        
        线程安全，可在任何线程中调用
        """
        if not self._is_active:
            return
            
        event = LogEvent(
            stage=self._current_stage,
            level=level,
            message=message,
            timestamp=time.time(),
            details=details,
            iteration=self._current_iteration,
        )
        self._queue.put(event)
    
    def get_pending_logs(self) -> List[LogEvent]:
        """
        获取所有待处理的日志（非阻塞）
        """
        logs = []
        while not self._queue.empty():
            try:
                logs.append(self._queue.get_nowait())
            except:
                break
        return logs
    
    def has_pending_logs(self) -> bool:
        """检查是否有待处理的日志"""
        return not self._queue.empty()
    
    def close(self):
        """关闭回调"""
        self._is_active = False
    
    def clear(self):
        """清空日志队列"""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except:
                break


# 全局回调实例（单次执行使用）
_global_callback: Optional[StreamCallback] = None


def get_global_callback() -> Optional[StreamCallback]:
    """获取全局回调"""
    return _global_callback


def set_global_callback(callback: Optional[StreamCallback]):
    """设置全局回调"""
    global _global_callback
    _global_callback = callback
