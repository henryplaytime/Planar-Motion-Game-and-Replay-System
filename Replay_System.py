"""
游戏回放系统模块。

只负责"回放逻辑":
- 加载录制文件（通过 shared.record_format）
- 按时间插值恢复玩家状态
- 应用高阶命令 / 原始输入
- 渲染特效和回放 UI

不再负责:
- 主循环（→ core/app_loop.py）
- 文件选择界面（→ scenes/replay_select_scene.py）
- 事件分发（→ scenes/replay_scene.py）
"""

import bisect
import math
import random
import time
import traceback

import pygame

import data
from core.state import ReplaySubState
from player import Player
from shared import record_format
from shared.record_loader import load as load_recording
from core.state import ReplaySubState


class GameReplayer:
    """把 .dem 还原成玩家状态。"""

    def __init__(self, filename, screen):

        self.entities = []
        self.etype_by_eid = {}
        self.header = None

        self.filename = filename
        self.screen = screen

        self.commands = []
        self.inputs = []
        self.snapshots = []
        self.total_time = 0.0
        self.start_time = 0.0

        self.current_time = 0.0
        self.playback_speed = 1.0
        self.state = ReplaySubState.PLAYING
        self.last_frame_time = 0.0

        self.player = Player()
        self.current_command_index = 0
        self.current_input_index = 0
        self.current_snapshot_index = 0

        self.simulated_keys = {
            pygame.K_w: False, pygame.K_s: False,
            pygame.K_a: False, pygame.K_d: False,
            pygame.K_LSHIFT: False, pygame.K_RSHIFT: False,
            pygame.K_q: False,
        }
        self.last_snapshot = None
        self.next_snapshot = None

        self.adrenaline_active = False
        self.adrenaline_particles = []

        self.load_recording()

    # ---------- 加载 ----------
    def load_recording(self):
        try:
            rec = load_recording(self.filename)
            self.header = rec.header
            self.entities = rec.entities
            self.etype_by_eid = {e.eid: e.etype for e in rec.entities}

        # 3.0 第一版: 只处理 eid=0 的玩家
        # NPC 的 commands / inputs / snapshots 会在这里被过滤掉
            self.commands = [(t, c) for t, eid, c in rec.commands if eid == 0]
            self.inputs = [(t, c) for t, eid, c in rec.inputs if eid == 0]
            self.snapshots = rec.snapshots_by_eid.get(0, [])
            self.total_time = rec.total_time
            self.start_time = rec.header.start_time

            if self.snapshots:
                self.find_surrounding_snapshots(self.current_time)
            else:
                print("[GameReplayer] 警告: 没有玩家快照")
        except Exception as e:
            print(f"加载回放文件失败: {e}")
            traceback.print_exc()
            self.commands = []
            self.inputs = []
            self.snapshots = []
            self.entities = []
            self.etype_by_eid = {}
            self.total_time = 0.0
    def find_surrounding_snapshots(self, target_time):
        if not self.snapshots or len(self.snapshots) < 2:
            return None, None
        times = [s.time for s in self.snapshots]
        idx = bisect.bisect_left(times, target_time)
        if idx == 0:
            return self.snapshots[0], self.snapshots[1]
        if idx >= len(self.snapshots):
            return self.snapshots[-2], self.snapshots[-1]
        return self.snapshots[idx - 1], self.snapshots[idx]

    # ---------- 应用输入 ----------
    def apply_command(self, command_str):
        if not command_str:
            return
        cmds = command_str.split(",")
        self.simulated_keys[pygame.K_w] = 'W' in cmds
        self.simulated_keys[pygame.K_s] = 'S' in cmds
        self.simulated_keys[pygame.K_a] = 'A' in cmds
        self.simulated_keys[pygame.K_d] = 'D' in cmds
        self.simulated_keys[pygame.K_LSHIFT] = 'SHIFT' in cmds
        self.simulated_keys[pygame.K_RSHIFT] = 'SHIFT' in cmds
        self.player.update(self.simulated_keys, 1.0 / data.RECORD_FPS)

    def apply_input_changes(self, input_str):
        if not input_str:
            return
        for change in input_str.split(";"):
            if ":" not in change:
                continue
            key, state = change.split(":")
            if key.upper() == "SHIFT":
                v = bool(int(state))
                self.simulated_keys[pygame.K_LSHIFT] = v
                self.simulated_keys[pygame.K_RSHIFT] = v
            else:
                try:
                    code = getattr(pygame, f"K_{key.lower()}")
                    self.simulated_keys[code] = bool(int(state))
                except AttributeError:
                    print(f"警告: 未知按键 {key}")

    def apply_interpolated_snapshot(self):
        if not self.last_snapshot or not self.next_snapshot:
            return
        prev, nxt = self.last_snapshot, self.next_snapshot
        if prev.time > nxt.time:
            prev, nxt = nxt, prev

        total = nxt.time - prev.time
        blend = (self.current_time - prev.time) / total if total > 0 else 0.0

        target_x = prev.pos_x + (nxt.pos_x - prev.pos_x) * blend
        target_y = prev.pos_y + (nxt.pos_y - prev.pos_y) * blend
        target_vx = prev.vel_x + (nxt.vel_x - prev.vel_x) * blend
        target_vy = prev.vel_y + (nxt.vel_y - prev.vel_y) * blend

        sprinting = (prev.flags.get("sprint", False) if blend < 0.5
             else nxt.flags.get("sprint", False))
        adrenaline = (prev.flags.get("adr", False) if blend < 0.5
              else nxt.flags.get("adr", False))

        if adrenaline and not self.adrenaline_active:
            self._activate_adrenaline_effect()
        self.adrenaline_active = adrenaline

        self.player.position[0] += (target_x - self.player.position[0]) * 0.3
        self.player.position[1] += (target_y - self.player.position[1]) * 0.3
        self.player.velocity[0] += (target_vx - self.player.velocity[0]) * 0.5
        self.player.velocity[1] += (target_vy - self.player.velocity[1]) * 0.5
        self.player.sprinting = sprinting
        self.player.rect.center = (int(self.player.position[0]),
                                   int(self.player.position[1]))

    # ---------- 更新 ----------
    def update(self, delta_time):
        if self.state == ReplaySubState.PAUSED:
            return

        actual = delta_time * self.playback_speed
        now = time.time()

        if (self.state == ReplaySubState.REWIND
                and abs(now - self.last_frame_time) < 0.001
                and self.current_time > 0):
            print("检测到卡住，重置索引")
            self.reset_indices()
        self.last_frame_time = now

        if self.state == ReplaySubState.PLAYING:
            self.current_time += actual
        elif self.state == ReplaySubState.FAST_FORWARD:
            self.current_time += actual * 2.0
        elif self.state == ReplaySubState.REWIND:
            self.current_time -= actual * 2.0

        self.current_time = max(0.0, min(self.current_time, self.total_time))

        self.last_snapshot, self.next_snapshot = self.find_surrounding_snapshots(
            self.current_time)

        if self.state == ReplaySubState.REWIND:
            self.current_command_index = 0
            for i, (t, _) in enumerate(self.commands):
                if t <= self.current_time:
                    self.current_command_index = i
                else:
                    break
            self.current_input_index = 0
            for i, (t, _) in enumerate(self.inputs):
                if t <= self.current_time:
                    self.current_input_index = i
                else:
                    break

        while (self.current_command_index < len(self.commands)
               and self.commands[self.current_command_index][0] <= self.current_time):
            _, cmd = self.commands[self.current_command_index]
            self.apply_command(cmd)
            self.current_command_index += 1

        while (self.current_input_index < len(self.inputs)
               and self.inputs[self.current_input_index][0] <= self.current_time):
            _, ch = self.inputs[self.current_input_index]
            self.apply_input_changes(ch)
            self.current_input_index += 1

        if self.last_snapshot and self.next_snapshot:
            self.apply_interpolated_snapshot()

        self._update_adrenaline_particles(delta_time)

    def reset_indices(self):
        self.current_command_index = 0
        for i, (t, _) in enumerate(self.commands):
            if t <= self.current_time:
                self.current_command_index = i

        self.current_input_index = 0
        for i, (t, _) in enumerate(self.inputs):
            if t <= self.current_time:
                self.current_input_index = i

        self.current_snapshot_index = 0
        for i, s in enumerate(self.snapshots):
            if s.time <= self.current_time:
                self.current_snapshot_index = i

    # ---------- UI ----------
    def draw_ui(self, screen):
        default_font_size = data.get_scaled_font(data.REPLAY_DEFAULT_FONT_SIZE, screen)
        title_font_size = data.get_scaled_font(data.REPLAY_TITLE_FONT_SIZE, screen)
        font = data.get_font(default_font_size)
        title_font = data.get_font(title_font_size)

        controls = [
            "空格键: 播放/暂停",
            "→: 快进",
            "←: 后退",
            "↑: 增加速度",
            "↓: 减少速度",
            "J: 跳转到指定时间",
            "ESC: 退出回放",
        ]

        max_width = 0
        for text in controls:
            max_width = max(max_width, font.size(text)[0])

        time_text = f"时间: {self.current_time:.1f}/{self.total_time:.1f}秒"
        state_text = f"状态: {self.state.name} | 速度: x{self.playback_speed:.1f}"
        if self.adrenaline_active:
            state_text += " | 肾上腺素激活"
        max_width = max(max_width, font.size(time_text)[0], font.size(state_text)[0])

        panel_width = max_width + 2 * data.UI_PADDING
        panel_height = data.UI_PADDING * 2 + (len(controls) + 3) * data.UI_LINE_SPACING

        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((*data.PANEL_COLOR[:3], data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, (100, 150, 200), panel.get_rect(), 2)

        panel_pos = data.scale_position(
            data.BASE_WIDTH - panel_width - 20, 20, screen)
        screen.blit(panel, panel_pos)

        title = title_font.render("游戏回放系统", True, data.INFO_COLOR)
        screen.blit(title, (panel_pos[0] + (panel_width - title.get_width()) // 2,
                            panel_pos[1] + 10))

        time_surf = font.render(time_text, True, data.TEXT_COLOR)
        screen.blit(time_surf, (panel_pos[0] + (panel_width - time_surf.get_width()) // 2,
                                panel_pos[1] + 50))

        state_surf = font.render(state_text, True, data.TEXT_COLOR)
        screen.blit(state_surf, (panel_pos[0] + (panel_width - state_surf.get_width()) // 2,
                                 panel_pos[1] + 80))

        y = panel_pos[1] + 120
        for text in controls:
            line = font.render(text, True, data.TEXT_COLOR)
            screen.blit(line, (panel_pos[0] + data.UI_PADDING, y))
            y += data.UI_LINE_SPACING

    def draw_progress_bar(self, screen):
        if self.total_time <= 0:
            return
        font = data.get_font(data.get_scaled_font(data.REPLAY_INFO_FONT_SIZE, screen))

        bar_width = data.scale_value(600, screen)
        bar_height = data.scale_value(20, screen, False)
        bar_x = (screen.get_width() - bar_width) // 2
        bar_y = screen.get_height() - data.scale_value(50, screen, False)
        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)

        pygame.draw.rect(screen, (60, 60, 80), bar_rect)
        pygame.draw.rect(screen, (100, 100, 120), bar_rect, 2)

        progress = self.current_time / self.total_time
        fill_rect = pygame.Rect(bar_x, bar_y, int(bar_width * progress), bar_height)
        pygame.draw.rect(screen, (80, 180, 250), fill_rect)

        marker_x = bar_x + int(bar_width * progress)
        pygame.draw.line(screen, (255, 255, 255),
                         (marker_x, bar_y - 5),
                         (marker_x, bar_y + bar_height + 5), 3)

        time_text = font.render(
            f"{self.current_time:.1f}s / {self.total_time:.1f}s",
            True, data.TEXT_COLOR)
        screen.blit(time_text, (
            (screen.get_width() - time_text.get_width()) // 2,
            bar_y - data.UI_LINE_SPACING,
        ))

    def draw_effects(self, screen):
        for particle in self.adrenaline_particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            color = (*data.ADRENALINE_COLOR[:3], alpha)
            radius = int(particle['size'] * (particle['life'] / particle['max_life']))
            pygame.draw.circle(
                screen, color,
                (int(particle['pos'][0]), int(particle['pos'][1])),
                radius)

        if self.adrenaline_active:
            pulse = abs(math.sin(pygame.time.get_ticks() / 200.0))
            radius = 50 + 10 * pulse
            pygame.draw.circle(
                screen, data.ADRENALINE_COLOR,
                (int(self.player.position[0]), int(self.player.position[1])),
                int(radius), 3)

    # ---------- 粒子 ----------
    def _activate_adrenaline_effect(self):
        self.adrenaline_particles = []
        for _ in range(20):
            self._create_adrenaline_particle()

    def _create_adrenaline_particle(self):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 200)
        size = random.uniform(3, 10)
        self.adrenaline_particles.append({
            'pos': list(self.player.position),
            'vel': [math.cos(angle) * speed, math.sin(angle) * speed],
            'size': size,
            'life': 1.0,
            'max_life': random.uniform(0.3, 0.8),
        })

    def _update_adrenaline_particles(self, delta_time):
        for p in self.adrenaline_particles[:]:
            p['life'] -= delta_time
            if p['life'] <= 0:
                self.adrenaline_particles.remove(p)
                continue
            p['pos'][0] += p['vel'][0] * delta_time
            p['pos'][1] += p['vel'][1] * delta_time
            p['vel'][0] *= 0.9
            p['vel'][1] *= 0.9