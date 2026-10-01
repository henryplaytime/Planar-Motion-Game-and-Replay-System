"""
唯一的主循环。

职责：
- 从 pygame 拉事件，分发给当前场景
- 调用当前场景的 update / render
- 处理场景发起的 switch_to / quit 请求
- 在所有渲染之上画全局 HUD（状态徽章）
"""
import pygame

from core.state import AppState
from shared.hud import draw_state_badge
from core.key_router import build_default_router


class AppLoop:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.scenes = {}
        self.state = None
        self.current_scene = None
        self.running = False

        self.key_router = build_default_router()

        # 延迟切换：场景在 update/render 期间请求切换，帧末统一执行
        self._pending_switch = None
        self._pending_kwargs = {}
        self._pending_quit = False

    # ---------- 注册 / 请求 ----------
    def register(self, state: AppState, scene):
        self.scenes[state] = scene
        scene.app = self

    def switch_to(self, state: AppState, **kwargs):
        self._pending_switch = state
        self._pending_kwargs = kwargs

    def quit(self):
        self._pending_quit = True

    # ---------- 内部 ----------
    def _do_switch(self):
        if self.current_scene:
            self.current_scene.on_exit()

        self.state = self._pending_switch
        self.current_scene = self.scenes.get(self.state)

        if self.current_scene is None:
            print(f"[AppLoop] 警告: 状态 {self.state} 未注册场景")
        else:
            self.current_scene.on_enter(**self._pending_kwargs)

        self._pending_switch = None
        self._pending_kwargs = {}

    # ---------- 主循环 ----------
    def run(self, initial_state: AppState):
        self._pending_switch = initial_state
        self._do_switch()

        self.running = True
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            # 1. 事件分发
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                if self.current_scene is None:
                    continue
                # KeyRouter 优先：ESC 被集中处理
                if self.key_router.dispatch(event, self.current_scene):
                    continue
                self.current_scene.handle_event(event)
                
            if self._pending_quit:
                self.running = False
                break

            # 2. 更新 + 渲染
            if self.current_scene:
                self.current_scene.update(dt)
                self.current_scene.render(self.screen)

                # 3. 全局 HUD：状态徽章（左下角）
                sub = getattr(self.current_scene, "sub_state", None)
                draw_state_badge(self.screen, self.state, sub)

            pygame.display.flip()

            # 4. 应用场景请求的切换
            if self._pending_switch is not None:
                self._do_switch()

        pygame.quit()