"""
集中式 ESC 语义分发。

设计:
- KeyRouter 维护 (AppState, sub_state) → handler(scene) 的表
- AppLoop 在把事件交给场景之前先调用 router.dispatch(event, scene)
- 若场景声明 escape_is_busy() → True（控制台等覆盖层打开），
  KeyRouter 跳过，让场景的 handle_event 处理

场景只需要:
- 不再自己写 if event.key == K_ESCAPE
- 持有控制台等覆盖层时，覆写 escape_is_busy() 返回 True
- 新增状态时只在本文件的 build_default_router() 里加一行
"""
import pygame

from core.state import AppState, GameSubState


class KeyRouter:
    def __init__(self):
        self._handlers = {}    # (state, sub_state) -> handler(scene)
        self._fallbacks = {}   # state -> handler(scene)

    def register(self, state, sub_state, handler):
        self._handlers[(state, sub_state)] = handler

    def register_fallback(self, state, handler):
        """无子状态时使用的处理函数。"""
        self._fallbacks[state] = handler

    def dispatch(self, event, scene) -> bool:
        """处理成功返回 True，否则 False。"""
        if event.type != pygame.KEYDOWN or event.key != pygame.K_ESCAPE:
            return False

        # 覆盖层优先（控制台等）
        if scene.escape_is_busy():
            return False

        state = scene.app.state
        sub = getattr(scene, "sub_state", None)
        handler = self._handlers.get((state, sub)) or self._fallbacks.get(state)
        if handler is None:
            return False

        handler(scene)
        return True


# ============ 默认处理函数 ============
def _escape_main_menu(scene):
    scene.app.quit()


def _escape_game_normal(scene):
    scene.sub_state = GameSubState.PAUSED


def _escape_game_paused(scene):
    scene.sub_state = GameSubState.NORMAL


def _escape_replay_select(scene):
    scene.app.switch_to(AppState.MAIN_MENU)


def _escape_replay_playing(scene):
    scene.app.switch_to(AppState.REPLAY_FILE_SELECT)


def _escape_settings(scene):
    scene.app.switch_to(AppState.MAIN_MENU)


def build_default_router() -> KeyRouter:
    router = KeyRouter()

    router.register_fallback(AppState.MAIN_MENU, _escape_main_menu)

    router.register(AppState.IN_GAME, GameSubState.NORMAL, _escape_game_normal)
    router.register(AppState.IN_GAME, GameSubState.PAUSED, _escape_game_paused)

    router.register_fallback(AppState.REPLAY_FILE_SELECT, _escape_replay_select)
    router.register_fallback(AppState.REPLAY_PLAYING, _escape_replay_playing)

    router.register_fallback(AppState.SETTINGS, _escape_settings)

    return router