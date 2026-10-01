"""
全局状态定义。

两层状态：
- AppState    全局互斥，决定"谁在跑 update/render"
- SubState    场景内子状态，决定"同一场景里的模式切换"
"""
from enum import Enum, auto


class AppState(Enum):
    """全局状态。同一时刻只有一个激活。"""
    LOADING = auto()
    MAIN_MENU = auto()
    IN_GAME = auto()
    REPLAY_FILE_SELECT = auto()
    REPLAY_PLAYING = auto()
    SETTINGS = auto()


class GameSubState(Enum):
    """IN_GAME 场景的子状态。"""
    NORMAL = auto()
    PAUSED = auto()


class ReplaySubState(Enum):
    """REPLAY 场景的子状态。"""
    PLAYING = auto()
    PAUSED = auto()
    FAST_FORWARD = auto()
    REWIND = auto()

class SettingsSubState(Enum):
    """SETTINGS 场景的子状态，对应 4 个分类。"""
    INTERFACE = auto()   # 界面
    AUDIO = auto()       # 音频
    GAMEPLAY = auto()    # 游戏性
    CONTROLS = auto()    # 控制