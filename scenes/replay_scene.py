"""
回放播放场景。

取代旧的 run_replay_mode() / handle_replay_events() / render_replay_scene()。
回放器本身仍由 Replay_System.GameReplayer 提供，但主循环在这里。
"""
import pygame

import data
from core.state import AppState, ReplaySubState
from data import create_background_grid
from Replay_System import GameReplayer
from scenes.base_scene import Scene
from shared.player_view import draw_player_body


class ReplayScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.replayer = None
        self.background_grid = None
        self.sub_state = ReplaySubState.PLAYING

    def on_enter(self, **kwargs):
        path = kwargs.get("path")
        if not path:
            self.app.switch_to(AppState.REPLAY_FILE_SELECT)
            return

        pygame.display.set_caption("游戏回放模式")
        self.replayer = GameReplayer(path, self.app.screen)
        self.background_grid = create_background_grid(self.app.screen)
        self.sub_state = self.replayer.state

        if not self.replayer.snapshots:
            print(f"[ReplayScene] 文件无有效快照，返回选择界面: {path}")
            self.app.switch_to(AppState.REPLAY_FILE_SELECT)

    def on_exit(self):
        self.replayer = None
        self.background_grid = None

    # ---------- 事件 ----------
    def handle_event(self, event):
        if self.replayer is None:
            return
        if event.type != pygame.KEYDOWN:
            return

        r = self.replayer
        key = event.key

        if key == pygame.K_SPACE:
            r.state = (ReplaySubState.PLAYING
                    if r.state == ReplaySubState.PAUSED
                    else ReplaySubState.PAUSED)
        elif key == pygame.K_RIGHT:
            r.state = ReplaySubState.FAST_FORWARD
        elif key == pygame.K_LEFT:
            r.state = ReplaySubState.REWIND
        elif key == pygame.K_UP:
            r.playback_speed = min(4.0, r.playback_speed + 0.5)
        elif key == pygame.K_DOWN:
            r.playback_speed = max(0.5, r.playback_speed - 0.5)
        elif key == pygame.K_j:
            r.current_time = r.total_time / 2
            r.reset_indices()

        self.sub_state = r.state
    # ---------- 更新 ----------
    def update(self, dt):
        if self.replayer is None:
            return
        self.replayer.update(dt)
        self.sub_state = self.replayer.state

    # ---------- 渲染 ----------
    def render(self, screen):
        if self.replayer is None:
            return
        screen.blit(self.background_grid, (0, 0))
        draw_player_body(screen, self.replayer.player)
        self.replayer.draw_effects(screen)
        self.replayer.draw_ui(screen)
        self.replayer.draw_progress_bar(screen)