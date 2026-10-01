"""
场景基类。

约定：
- 场景不拥有主循环 → AppLoop 是唯一主循环
- 场景不调用 pygame.event.get() → 事件由 AppLoop 分发
- 场景不调用 pygame.display.flip() → AppLoop 统一 flip
- 场景切换 → self.app.switch_to(AppState.XXX)
- 场景退出 → self.app.quit()
"""


class Scene:
    def __init__(self, app):
        self.app = app

    def escape_is_busy(self) -> bool:
        """
        覆盖层（控制台、模态框）打开时返回 True。
        KeyRouter 会跳过 ESC 处理，把事件让给场景的 handle_event。
        """
        return False
    
    def on_enter(self, **kwargs):
        """场景被激活时调用一次。"""
        pass

    def on_exit(self):
        """场景被切换走时调用一次。"""
        pass

    def handle_event(self, event):
        """处理单个 pygame 事件。"""
        pass

    def update(self, dt):
        """每帧调用，dt 为秒。"""
        pass

    def render(self, screen):
        """每帧调用，负责绘制。AppLoop 会在其后画全局 HUD。"""
        pass