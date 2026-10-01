"""
回放文件选择场景。

取代旧的 select_replay_file() / no_replay_message()，
不再自己 while + pygame.event.get()。
"""
import glob
import pygame

import data
from core.state import AppState
from scenes.base_scene import Scene


class ReplaySelectScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.files = []
        self.selected_index = 0
        self.empty = False

    def on_enter(self, **kwargs):
        pygame.display.set_caption("回放文件选择")
        self.files = sorted(glob.glob("*.dem"))
        self.selected_index = 0
        self.empty = not self.files

    def on_exit(self):
        self.files = []

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.empty:
            return

        n = len(self.files)
        if event.key == pygame.K_RETURN:
            self.app.switch_to(AppState.REPLAY_PLAYING,
                           path=self.files[self.selected_index])
            
        elif event.key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % n
            
        elif event.key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % n

    def update(self, dt):
        pass

    def render(self, screen):
        screen.fill(data.BACKGROUND)

        if self.empty:
            font = pygame.font.SysFont("simhei", 36)
            text = font.render("没有找到回放文件！按 ESC 返回主菜单", True, (255, 0, 0))
            screen.blit(text, text.get_rect(center=(
                screen.get_width() // 2, screen.get_height() // 2)))
            return

        title_font = data.get_font(data.get_scaled_font(36, screen))
        item_font = data.get_font(data.get_scaled_font(24, screen))

        max_w = max(item_font.size(f)[0] for f in self.files)
        panel_w = max_w + 100
        panel_h = 100 + len(self.files) * 40
        panel_x = (screen.get_width() - panel_w) // 2
        panel_y = (screen.get_height() - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((*data.PANEL_COLOR[:3], data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, (100, 150, 200), panel.get_rect(), 2)
        screen.blit(panel, (panel_x, panel_y))

        title = title_font.render("选择回放文件", True, data.TEXT_COLOR)
        screen.blit(title, (panel_x + (panel_w - title.get_width()) // 2,
                            panel_y + 20))

        y = panel_y + 70
        for i, name in enumerate(self.files):
            color = (255, 255, 255) if i == self.selected_index else (180, 180, 180)
            text = item_font.render(name, True, color)
            screen.blit(text, (panel_x + 30, y))
            y += 40

        help_font = data.get_font(data.get_scaled_font(18, screen))
        help_text = help_font.render(
            "↑/↓: 选择文件  ENTER: 确认  ESC: 取消", True, data.TEXT_COLOR)
        screen.blit(help_text, (
            panel_x + (panel_w - help_text.get_width()) // 2,
            panel_y + panel_h - 30,
        ))