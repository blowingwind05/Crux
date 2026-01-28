"""
节点基类

定义所有节点的通用接口和基础功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from src.crux.config import CruxConfig
from src.crux.core.state import AgentState


class BaseNode(ABC):
    """
    节点抽象基类
    
    所有节点都需要继承此类并实现 process 方法。
    """
    
    # 节点名称，子类应覆盖
    name: str = "base"
    
    # 节点描述
    description: str = "Base node"
    
    def __init__(self, config: Optional[CruxConfig] = None):
        """
        初始化节点
        
        Args:
            config: 框架配置对象
        """
        self.config = config or CruxConfig()
    
    @abstractmethod
    def process(self, state: AgentState) -> Dict[str, Any]:
        """
        处理状态并返回更新
        
        Args:
            state: 当前 Agent 状态
            
        Returns:
            状态更新字典，将被合并到 state 中
        """
        pass
    
    def log(self, message: str, level: str = "INFO"):
        """
        日志输出
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        prefix = f"[{self.name.upper()}]"
        if self.config.debug:
            print(f"{prefix} [{level}] {message}")
        else:
            print(f"{prefix} {message}")
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"
