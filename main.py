"""
程序入口。

职责被压缩到只剩：
1. 跑加载菜单拿到用户配置
2. 初始化 pygame
3. 创建 AppLoop 并注册场景
4. 启动主循环
"""
import data
from core.app_loop import AppLoop
from core.state import AppState
from scenes.game_scene import GameScene
from scenes.main_menu_scene import MainMenuScene
from source.main_loading_menu import show_loading_menu
from scenes.replay_select_scene import ReplaySelectScene
from scenes.replay_scene import ReplayScene
from scenes.settings_scene import SettingsScene

DEFAULT_MAIN_CONFIG = {"button_style": "COD"}


def main():
    
    user_config = show_loading_menu() or DEFAULT_MAIN_CONFIG
    if "button_style" not in user_config:
        user_config["button_style"] = DEFAULT_MAIN_CONFIG["button_style"]

    screen = data.init_pygame()

    app = AppLoop(screen)
    app.register(AppState.MAIN_MENU, MainMenuScene(app, user_config))
    app.register(AppState.IN_GAME, GameScene(app))
    app.register(AppState.REPLAY_FILE_SELECT, ReplaySelectScene(app))
    app.register(AppState.REPLAY_PLAYING, ReplayScene(app))
    app.register(AppState.SETTINGS, SettingsScene(app, user_config))
    app.run(AppState.MAIN_MENU)


if __name__ == "__main__":
    main()