"""
节点基类

定义所有节点的通用接口和基础功能。
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.crux.config import CruxConfig
    from src.crux.state import AgentState

from src.crux.utils.logger import StageLogger, StageLog
from src.crux.utils.callback import get_global_callback


class BaseNode(ABC):
    """
    节点抽象基类
    
    所有节点都需要继承此类并实现 process 方法。
    支持结构化日志收集，便于前端展示执行过程。
    支持回调机制实现实时日志流式推送。
    """
    
    # 节点名称，子类应覆盖
    name: str = "base"
    
    # 节点中文名称
    name_cn: str = "基础节点"
    
    # 节点描述
    description: str = "Base node"
    
    def __init__(self, config: Optional["CruxConfig"] = None):
        """
        初始化节点
        
        Args:
            config: 框架配置对象
        """
        if config is None:
            from src.crux.config import CruxConfig
            config = CruxConfig()
        self.config = config
        self._logger: Optional[StageLogger] = None
        self._start_time: float = 0
    
    @property
    def logger(self) -> StageLogger:
        """获取日志收集器"""
        if self._logger is None:
            self._logger = StageLogger(self.name)
        return self._logger
    
    def reset_logger(self):
        """重置日志收集器"""
        self._logger = StageLogger(self.name)
        self._start_time = time.time()
        
        # 通知全局回调当前阶段
        callback = get_global_callback()
        if callback:
            callback.set_stage(self.name)
    
    @abstractmethod
    def process(self, state: "AgentState") -> Dict[str, Any]:
        """
        处理状态并返回更新
        
        Args:
            state: 当前 Agent 状态
            
        Returns:
            状态更新字典，将被合并到 state 中
        """
        pass
    
    def log(self, message: str, level: str = "INFO", details: Optional[Dict[str, Any]] = None):
        """
        日志输出 - 同时推送到回调和本地收集器
        
        Args:
            message: 日志消息
            level: 日志级别 (INFO, WARN, ERROR, DEBUG)
            details: 额外详情信息
        """
        # 1. 推送到实时回调（如果存在）
        callback = get_global_callback()
        if callback:
            callback.on_log(level, message, details)
        
        # 2. 收集到结构化日志
        if level == "INFO":
            self.logger.info(message, details)
        elif level == "WARN":
            self.logger.warn(message, details)
        elif level == "ERROR":
            self.logger.error(message, details)
        else:
            self.logger.debug(message, details)
        
        # 3. 同时输出到控制台
        prefix = f"[{self.name.upper()}]"
        if self.config.debug:
            print(f"{prefix} [{level}] {message}")
        else:
            print(f"{prefix} {message}")
    
    def get_stage_logs(self) -> List[Dict[str, Any]]:
        """获取当前阶段收集的所有日志"""
        return self.logger.get_logs()
    
    def get_duration_ms(self) -> float:
        """获取执行时长（毫秒）"""
        return self.logger.get_duration_ms()
    
    def build_result(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建带日志的结果
        
        子类可以调用此方法将日志附加到返回结果中
        
        Args:
            updates: 状态更新字典
            
        Returns:
            带日志信息的完整结果
        """
        result = updates.copy()
        result["_stage_logs"] = self.get_stage_logs()
        result["_stage_duration_ms"] = self.get_duration_ms()
        return result
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"

