"""
主菜单场景。

从 main.py 的 main_menu 函数抽出：
- while 循环 → 拆成 handle_event / update / render
- 按钮点击 → 通过 self.app.switch_to 切状态，不再直接调用 start_game
"""
import pygame

import data
from console import Console, ConsoleState
from core.state import AppState
from scenes.base_scene import Scene
from source.menu_btn_style import create_button



def _create_menu_buttons(screen, button_style):
    """按当前屏幕尺寸创建主菜单按钮。"""
    button_width = data.MENU_BUTTON_WIDTH
    button_height = data.MENU_BUTTON_HEIGHT
    start_y = screen.get_height() * data.MENU_BUTTON_START_Y_RATIO

    specs = [
        data.BUTTON_TEXT_START,
        data.BUTTON_TEXT_REPLAY,
        data.BUTTON_TEXT_SETTINGS,
        data.BUTTON_TEXT_EXIT,
    ]

    buttons = []
    for i, text in enumerate(specs):
        buttons.append(create_button(
            button_style,
            screen.get_width() // 2 - button_width // 2,
            start_y + data.MENU_BUTTON_SPACING * i,
            button_width,
            button_height,
            text,
            screen,
        ))
    return buttons


def _scaled_button_rect(button):
    """按钮在屏幕上实际占据的矩形（考虑缩放）。"""
    x = data.scale_value(button.rect.x, button.screen, True)
    y = data.scale_value(button.rect.y, button.screen, False)
    w = data.scale_value(button.rect.width, button.screen, True)
    h = data.scale_value(button.rect.height, button.screen, False)
    return pygame.Rect(x, y, w, h)


class MainMenuScene(Scene):
    def __init__(self, app, user_config):
        super().__init__(app)
        self.user_config = user_config
        self.button_style = user_config.get("button_style", "COD")

        self.buttons = []
        self.console = None
        self.click_sound = None
        self.hover_sound = None

        self.current_selected = -1
        self.last_hover_index = -1
        self.mouse_pos = (0, 0)

    # ---------- 生命周期 ----------
    def on_enter(self, **kwargs):
        pygame.display.set_caption(data.MAIN_MENU_TITLE)

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
        self.buttons = _create_menu_buttons(self.app.screen, self.button_style)
        self.current_selected = -1
        self.last_hover_index = -1
        self.mouse_pos = pygame.mouse.get_pos()

    def on_exit(self):
        # 保留控制台状态无所谓，每次进来重新创建
        self.buttons = []
        self.console = None

    # ---------- 事件 ----------
    def handle_event(self, event):
    # 1. 控制台优先
        if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
            self.console.toggle()
            return
        if self.console and self.console.handle_event(event):
            return

        # 2. 窗口
        if event.type == pygame.VIDEORESIZE:
            self.app.screen = pygame.display.set_mode(
                (event.w, event.h), pygame.RESIZABLE)
            self.buttons = _create_menu_buttons(self.app.screen, self.button_style)

        # 3. 鼠标
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            self._refresh_hover()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    def _refresh_hover(self):
        found = False
        for i, button in enumerate(self.buttons):
            if _scaled_button_rect(button).collidepoint(self.mouse_pos):
                self.current_selected = i
                if i != self.last_hover_index and self.hover_sound:
                    self.hover_sound.play()
                self.last_hover_index = i
                found = True
                break
        if not found:
            self.current_selected = -1
            self.last_hover_index = -1

    def _handle_click(self, pos):
        for button in self.buttons:
            if _scaled_button_rect(button).collidepoint(pos):
                if self.click_sound:
                    self.click_sound.play()
                button.state = "active"
                self._dispatch(button.text)
                return

    def _dispatch(self, text):
        if text == data.BUTTON_TEXT_START:
            self.app.switch_to(AppState.IN_GAME)

        elif text == data.BUTTON_TEXT_REPLAY:
            self.app.switch_to(AppState.REPLAY_FILE_SELECT)
            # print("[MainMenu] 回放模式：下一版接入 ReplayFileSelectScene")


        elif text == data.BUTTON_TEXT_SETTINGS:
            self.app.switch_to(AppState.SETTINGS)
            # print("[MainMenu] 设置菜单：下一版接入 SettingsScene")

        elif text == data.BUTTON_TEXT_EXIT:
            self.app.quit()

    def escape_is_busy(self):
        return (self.console is not None
                and self.console.state != ConsoleState.CLOSED)

    # ---------- 更新 ----------
    def update(self, dt):
        for button in self.buttons:
            button.state = "idle"
        if 0 <= self.current_selected < len(self.buttons):
            self.buttons[self.current_selected].state = "hover"
        for button in self.buttons:
            button.update(self.mouse_pos, False)

        if self.console:
            self.console.update()

    # ---------- 渲染 ----------
    def render(self, screen):
        screen.fill(data.BACKGROUND)

        # 标题
        title_font_size = data.get_scaled_font(data.MENU_TITLE_FONT_SIZE, screen)
        font_title = data.get_font(title_font_size)
        title = font_title.render(data.MAIN_MENU_TITLE, True, data.TEXT_COLOR)
        title_pos = (
            screen.get_width() // 2 - title.get_width() // 2,
            data.scale_value(screen.get_height() * data.MENU_TITLE_Y_RATIO, screen, False),
        )
        screen.blit(title, title_pos)

        # 装饰线
        line_y = data.scale_value(screen.get_height() * data.MENU_TITLE_LINE_Y_RATIO, screen, False)
        line_width = 180 * (screen.get_width() / data.BASE_WIDTH)
        pygame.draw.line(
            screen, data.ACCENT_COLOR,
            (screen.get_width() // 2 - line_width, line_y),
            (screen.get_width() // 2 + line_width, line_y),
            3,
        )

        # 按钮
        for button in self.buttons:
            button.draw(screen)

        # 底部信息
        info_font_size = data.get_scaled_font(data.INFO_FONT_SIZE, screen)
        font_info = data.get_font(info_font_size)
        info_text = font_info.render(data.MAIN_MENU_INFO, True, (150, 150, 150))
        screen.blit(info_text, (
            screen.get_width() // 2 - info_text.get_width() // 2,
            screen.get_height() - data.MENU_INFO_BOTTOM_MARGIN,
        ))

        # 控制台
        if self.console:
            self.console.render(screen)