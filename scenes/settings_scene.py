"""
设置场景。

从 settings.settings_menu() 的 while 循环抽出。
控件/渲染/保存逻辑仍由 settings.py 提供，本文件只做：
- 事件分发
- 场景状态（当前分类、悬停索引）
- 通过 AppLoop 切换场景

语义保持与原 settings_menu 一致：
- 点"应用" → save_settings + user_config 更新 + 回主菜单
- 点"返回" → 只回主菜单，不保存
- ESC      → 等价"返回"
- ~ 键     → 开关控制台
"""
import pygame

import data
import settings
from console import Console, ConsoleState
from core.state import AppState, SettingsSubState
from scenes.base_scene import Scene



_CATEGORY_TO_SUBSTATE = [
    SettingsSubState.INTERFACE,
    SettingsSubState.AUDIO,
    SettingsSubState.GAMEPLAY,
    SettingsSubState.CONTROLS,
]


class SettingsScene(Scene):
    def __init__(self, app, user_config):
        super().__init__(app)
        self.user_config = user_config

        # 预览中的样式（点"应用"才提交到 user_config）
        self.preview_style = user_config.get("button_style", "COD")

        self.buttons = []
        self.controls = {}
        self.console = None

        self.current_category = 0
        self.current_selected = -1
        self.last_hover_index = -1
        self.click_sound = None
        self.hover_sound = None
        self.mouse_pos = (0, 0)

        self.sub_state = SettingsSubState.INTERFACE

    # ---------- 生命周期 ----------
    def on_enter(self, **kwargs):
        pygame.display.set_caption(data.SETTINGS_MENU_TITLE)

        if not pygame.mixer.get_init():
            pygame.mixer.init()
        try:
            self.click_sound = pygame.mixer.Sound(data.SOUND_MENU_CLICK)
            self.hover_sound = pygame.mixer.Sound(data.SOUND_MENU_HOVER)
        except Exception as e:
            print(f"无法加载音效: {e}")
            self.click_sound = None
            self.hover_sound = None

        self.console = Console()
        self.preview_style = self.user_config.get("button_style", "COD")
        self._rebuild_widgets()

        self.current_category = 0
        self.current_selected = -1
        self.last_hover_index = -1
        self.sub_state = _CATEGORY_TO_SUBSTATE[self.current_category]
        self.mouse_pos = pygame.mouse.get_pos()

    def on_exit(self):
        self.buttons = []
        self.controls = {}
        self.console = None

    def _rebuild_widgets(self):
        screen = self.app.screen
        self.buttons = settings.create_settings_buttons(screen, self.preview_style)
        self.controls = settings.create_settings_controls(screen, self.user_config)

    def _category_controls(self):
        name = settings.SETTINGS_CATEGORIES[self.current_category]["name"]
        return self.controls.get(name, [])

    # ---------- 事件 ----------
    def handle_event(self, event):
        # 控制台优先
        if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
            self.console.toggle()
            return
        if self.console and self.console.handle_event(event):
            return

        if event.type == pygame.QUIT:
            self.app.quit()
            return

        if event.type == pygame.VIDEORESIZE:
            self.app.screen = pygame.display.set_mode(
                (event.w, event.h), pygame.RESIZABLE)
            self._rebuild_widgets()
            return

        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            self._handle_motion(event.pos)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event)
            return

    def _handle_motion(self, pos):
        screen = self.app.screen

        # 1. 分类按钮
        category_width = screen.get_width() // len(settings.SETTINGS_CATEGORIES)
        for i in range(len(settings.SETTINGS_CATEGORIES)):
            rect = pygame.Rect(i * category_width, 100, category_width, 60)
            if rect.collidepoint(pos):
                if i != self.last_hover_index:
                    self.current_selected = i
                    if self.hover_sound:
                        self.hover_sound.play()
                    self.last_hover_index = i
                return

        # 2. 底部按钮
        for i, button in enumerate(self.buttons):
            if data.get_scaled_button_rect(button, screen).collidepoint(pos):
                idx = len(settings.SETTINGS_CATEGORIES) + i
                if idx != self.last_hover_index:
                    self.current_selected = idx
                    if self.hover_sound:
                        self.hover_sound.play()
                    self.last_hover_index = idx
                return

        # 3. 控件悬停
        for _, control in self._category_controls():
            if hasattr(control, "update_hover_state"):
                control.update_hover_state(pos)

        self.current_selected = -1
        self.last_hover_index = -1

    def escape_is_busy(self):
        return (self.console is not None
                and self.console.state != ConsoleState.CLOSED)

    def _handle_click(self, event):
        screen = self.app.screen

        # 1. 分类按钮
        category_width = screen.get_width() // len(settings.SETTINGS_CATEGORIES)
        for i in range(len(settings.SETTINGS_CATEGORIES)):
            rect = pygame.Rect(i * category_width, 100, category_width, 60)
            if rect.collidepoint(event.pos):
                if self.click_sound:
                    self.click_sound.play()
                self.current_category = i
                self.sub_state = _CATEGORY_TO_SUBSTATE[i]
                return

        # 2. 底部按钮
        for i, button in enumerate(self.buttons):
            if data.get_scaled_button_rect(button, screen).collidepoint(event.pos):
                if self.click_sound:
                    self.click_sound.play()
                button.state = "active"
                if i == 0:
                    self._back()
                elif i == 1:
                    self._apply()
                return

        # 3. 控件点击
        for setting_name, control in self._category_controls():
            if control.handle_event(event):
                if self.click_sound:
                    self.click_sound.play()
                if setting_name == "按钮样式":
                    self.preview_style = control.get_current_style()
                    # 重新创建设置底部按钮以套用新样式（原逻辑）
                    self.buttons = settings.create_settings_buttons(
                        screen, self.preview_style)
                break

    # ---------- 提交 / 返回 ----------
    def _apply(self):
        self.user_config["button_style"] = self.preview_style
        settings.save_settings(self.user_config, self.preview_style, self.controls)
        print("设置已保存")
        self.app.switch_to(AppState.MAIN_MENU)

    def _back(self):
        # 不写 user_config，直接返回
        self.app.switch_to(AppState.MAIN_MENU)

    # ---------- 更新 ----------
    def update(self, dt):
        # 底部按钮：重置 → 悬停
        for button in self.buttons:
            button.state = "idle"

        n_cat = len(settings.SETTINGS_CATEGORIES)
        if n_cat <= self.current_selected < n_cat + len(self.buttons):
            self.buttons[self.current_selected - n_cat].state = "hover"

        for button in self.buttons:
            button.update(self.mouse_pos, False)

        # 每帧刷新当前分类控件的悬停（原代码在循环开头也这么做）
        for _, control in self._category_controls():
            if hasattr(control, "update_hover_state"):
                control.update_hover_state(self.mouse_pos)

    # ---------- 渲染 ----------
    def render(self, screen):
        settings.draw_settings_ui(
            screen,
            self.console,
            settings.SETTINGS_CATEGORIES,
            self.current_category,
            self.buttons,
            self.controls,
        )
        # AppLoop 会统一 flip