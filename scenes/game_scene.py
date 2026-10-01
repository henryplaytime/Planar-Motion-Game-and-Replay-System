"""
游戏内场景。

包含：
- 正常游戏（子状态 NORMAL）
- ESC 呼出的暂停覆盖层（子状态 PAUSED）

关键设计：
- 暂停层不是独立场景，是 GameScene 的一个子状态
- 暂停时 render 依然画游戏，再叠半透明遮罩
- 暂停时 update 不调用 Game.update，所以游戏不动
"""
import pygame

import data
from core.state import AppState, GameSubState
from game import Game
from scenes.base_scene import Scene
from console import ConsoleState


class GameScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.game = None
        self.sub_state = GameSubState.NORMAL

    # ---------- 生命周期 ----------
    def on_enter(self, **kwargs):
        pygame.display.set_caption(getattr(data, "GAME_WINDOW_TITLE", "游戏"))
        self.game = Game(self.app.screen)
        self.sub_state = GameSubState.NORMAL

    def on_exit(self):
        if self.game is not None:
            self.game.stop_recording()
            self.game = None

    # ---------- 事件 ----------
    def handle_event(self, event):
        if self.game is None:
            return

        if self.sub_state == GameSubState.PAUSED:
            self._handle_pause_event(event)
        else:
            signal = self.game.handle_event(event)
            if signal == "quit":
                self.app.quit()
            elif signal == "pause":
                self.sub_state = GameSubState.PAUSED

    def _handle_pause_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                self.app.switch_to(AppState.MAIN_MENU)

    def escape_is_busy(self):
        if self.game is None:
            return False
        return (self.game.console is not None
                and self.game.console.state != ConsoleState.CLOSED)

    # ---------- 更新 ----------
    def update(self, dt):
        if self.game is None:
            return
        if self.sub_state == GameSubState.NORMAL:
            self.game.update(dt)

    # ---------- 渲染 ----------
    def render(self, screen):
        if self.game is None:
            return

        # 1. 正常游戏渲染
        self.game.render()

        # 2. 暂停覆盖层
        if self.sub_state == GameSubState.PAUSED:
            self._render_pause_overlay(screen)

    def _render_pause_overlay(self, screen):
        # 半透明遮罩
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        font_size = data.get_scaled_font(data.GAME_TITLE_FONT_SIZE, screen)
        font = data.get_font(font_size)

        lines = [
            ("已暂停", (240, 240, 240)),
            ("按 ESC 继续游戏", (200, 200, 200)),
            ("按 M 返回主菜单", (200, 200, 200)),
        ]
        y = screen.get_height() // 2 - 40
        for text, color in lines:
            surf = font.render(text, True, color)
            screen.blit(surf, (
                screen.get_width() // 2 - surf.get_width() // 2,
                y,
            ))
            y += font.get_height() + 12