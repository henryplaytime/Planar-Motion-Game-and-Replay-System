"""
游戏主模块

此文件现在只负责"游戏内逻辑"：
- 玩家控制 / 物理
- 录制系统调用
- 游戏内 HUD 渲染（检测面板、控制信息、玩家状态）

不再负责：
- 主循环（归 core/app_loop.py）
- 全局状态（归 core/state.py）
- ESC 的语义（归 scenes/game_scene.py）
"""

import json
import os
import pygame
import time
import console
import data
from shared.player_view import draw_player_state_label, draw_player_stats
from data import create_background_grid
from player import Player
from shared.record_format import (
    ETYPE_PLAYER, EntityFrameData, EntitySpec, RecordWriter,
)


class Game:
    """游戏内逻辑（不含主循环）。"""

    def __init__(self, screen):
        self.screen = screen
        self.console = console.Console(self)

        # 状态标记
        self.show_detection = False
        self.recording = False

        # 玩家
        self.player = Player()

        # 录制状态
        self.record_writer = None

        # UI
        self.ground_y = data.SCREEN_HEIGHT - data.GROUND_OFFSET
        self.background_grid = create_background_grid(screen)
        self.control_info_texts = data.CONTROL_INFO_TEXTS
        self.move_info_texts = data.MOVE_INFO_TEXTS

        # 肾上腺素
        self.adrenaline_config = self.load_adrenaline_config()
        self.last_q_pressed = False

        # 由 update() 缓存，供 render() 使用
        self.last_pressed_keys = None
        self.last_delta_time = 0.0

    # ---------- 配置 ----------
    def load_adrenaline_config(self):
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "item.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            effects = config_data["items"].get("adrenaline", {}).get("effects", {})
            return {
                "speed_multiplier": effects.get("speed_multiplier", 1.5),
                "duration": effects.get("duration", 5.0),
                "cooldown": effects.get("cooldown", 15.0),
            }
        except Exception as e:
            print(f"加载肾上腺素配置失败: {str(e)}")
            return {"speed_multiplier": 1.5, "duration": 5.0, "cooldown": 15.0}

    # ---------- 事件（单个） ----------
    def handle_event(self, event):
        """
        处理单个事件。

        返回：
            'quit'  → 请求退出整个程序
            'pause' → 请求进入暂停（由 GameScene 决定如何处理）
            None    → 无特殊请求
        """
        # 控制台优先
        if self.console and self.console.state != console.ConsoleState.CLOSED:
            if self.console.handle_event(event):
                return None

        if event.type == pygame.QUIT:
            self.stop_recording()
            return 'quit'

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKQUOTE:
                self.console.toggle()
            elif event.key == pygame.K_ESCAPE:
                self.stop_recording()
                return 'pause'
            elif event.key == pygame.K_F1:
                self.show_detection = not self.show_detection
            elif event.key == pygame.K_F2:
                if self.recording:
                    self.stop_recording()
                else:
                    self.start_recording()

        elif event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode(
                (event.w, event.h), pygame.RESIZABLE)

        return None

    # ---------- 录制 ----------
    def start_recording(self):
        if self.recording:
            return
        timestamp = data.get_timestamp()
        filename = f"game_recording_{timestamp}.dem"
        try:
            self.record_writer = RecordWriter(filename)
            # 录制开始时就把所有实体注册好，写 E: 行
            self.record_writer.open(entities=self._collect_entity_specs())
            self.recording = True
            print(f"开始录制: {filename}")
        except Exception as e:
            print(f"开始录制失败: {e}")
            self.recording = False
            self.record_writer = None

    def stop_recording(self):
        if not self.recording:
            return
        try:
            if self.record_writer:
                self.record_writer.close()
                print("录制已停止")
        finally:
            self.recording = False
            self.record_writer = None

    def _collect_entity_specs(self):
        """目前只有玩家。NPC 接入后在这里展开。"""
        return [EntitySpec(0, ETYPE_PLAYER, "player")]

    def _collect_frame_data(self, player, pressed_keys):
        """目前只有玩家。NPC 接入后在这里展开。"""
        command = data.serialize_high_level_command(pressed_keys)
        return [
            EntityFrameData(
                eid=0,
                position=player.position,
                velocity=player.velocity,
                flags={
                    "sprint": int(player.sprinting),
                    "adr": int(player.adrenaline_active),
                    "gnd": int(player.grounded),
                },
                command=command,
        )
    ]

    def record_frame(self, player, pressed_keys):
        if self.recording and self.record_writer:
            self.record_writer.write_frame(
                self._collect_frame_data(player, pressed_keys),
                pressed_keys,
            )

    # ---------- 更新 ----------
    def update(self, dt):
        """dt 由 AppLoop 提供（秒）。"""
        dt = min(dt, 0.033)

        pressed_keys = pygame.key.get_pressed()
        self.last_pressed_keys = pressed_keys
        self.last_delta_time = dt

        current_time = pygame.time.get_ticks() / 1000.0
        self._handle_adrenaline_activation(pressed_keys, current_time)

        self.player.update(pressed_keys, dt)
        self.player.check_ground(self.ground_y)
        self.record_frame(self.player, pressed_keys)

        if self.console:
            self.console.update()

    def _handle_adrenaline_activation(self, pressed_keys, current_time):
        if pressed_keys[pygame.K_q] and not self.last_q_pressed:
            if current_time >= self.player.adrenaline_cooldown_end:
                success = self.player.activate_adrenaline(
                    self.adrenaline_config["duration"],
                    self.adrenaline_config["cooldown"],
                    self.adrenaline_config["speed_multiplier"],
                )
                if success:
                    print("肾上腺素激活!")
        self.last_q_pressed = pressed_keys[pygame.K_q]

    # ---------- 渲染 ----------
    def render(self):
        screen = self.screen

        screen.blit(self.background_grid, (0, 0))
        self.player.draw(screen)
        self.draw_player_status()

        if self.recording:
            self.draw_recording_indicator()

        if self.show_detection:
            self.draw_detection_panel(self.last_pressed_keys, self.last_delta_time)
        else:
            self.draw_control_info(self.last_pressed_keys)

        if self.console:
            self.console.render(screen)
        # 注意：不在这里 flip —— AppLoop 统一 flip

    # ---------- 下面的渲染函数基本原样保留 ----------
    def draw_recording_indicator(self):
        rec_text = data.get_font(data.get_scaled_font(data.INFO_FONT_SIZE, self.screen)).render(
            data.RECORDING_TEXT, True, data.RECORDING_COLOR)
        rec_pos = data.scale_position(
            data.SCREEN_WIDTH - rec_text.get_width() - 20, 20, self.screen)
        self.screen.blit(rec_text, rec_pos)

    def draw_player_status(self):
        draw_player_state_label(self.screen, self.player)
        draw_player_stats(self.screen, self.player)
    def draw_control_info(self, pressed_keys):
        if pressed_keys is None:
            return
        default_font_size = data.get_scaled_font(data.GAME_DEFAULT_FONT_SIZE, self.screen)
        title_font_size = data.get_scaled_font(data.GAME_TITLE_FONT_SIZE, self.screen)
        font = data.get_font(default_font_size)
        title_font = data.get_font(title_font_size)

        items = [(c, data.TEXT_COLOR) for c in self.control_info_texts]

        f1_status = data.KEY_PRESSED_STATUS if pressed_keys[pygame.K_F1] else data.KEY_NOT_PRESSED_STATUS
        f1_color = data.KEY_PRESSED_COLOR if pressed_keys[pygame.K_F1] else data.TEXT_COLOR
        items.append((data.KEY_STATUS_FORMAT.format("F1键状态", f1_status), f1_color))

        f2_status = data.KEY_PRESSED_STATUS if pressed_keys[pygame.K_F2] else data.KEY_NOT_PRESSED_STATUS
        f2_color = data.RECORDING_COLOR if self.recording else data.TEXT_COLOR
        items.append((data.KEY_STATUS_FORMAT.format("F2键状态", f2_status), f2_color))

        rec_status = data.RECORDING_STATUS_ON if self.recording else data.RECORDING_STATUS_OFF
        rec_color = data.RECORDING_COLOR if self.recording else (100, 200, 100)
        items.append((data.RECORDING_STATUS_FORMAT.format(rec_status), rec_color))

        adrenaline_status = data.ADRENALINE_ACTIVE if self.player.adrenaline_active else data.ADRENALINE_AVAILABLE
        adrenaline_color = data.ADRENALINE_ACTIVE_COLOR if self.player.adrenaline_active else data.ADRENALINE_AVAILABLE_COLOR
        items.append((data.PLAYER_ADRENALINE_STATUS_FORMAT.format(adrenaline_status), adrenaline_color))

        max_width = max([font.size(t)[0] for t, _ in items] + [title_font.size(data.PANEL_TITLE_GAME)[0]])
        panel_width = max_width + 2 * data.UI_PADDING
        panel_height = data.UI_PADDING * 2 + (len(items) + 2) * data.UI_LINE_SPACING

        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill(data.get_rgba_color(data.PANEL_COLOR, data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, data.UI_HIGHLIGHT, panel.get_rect(), 2)

        panel_pos = data.scale_position((data.BASE_WIDTH - panel_width) // 2, 20, self.screen)
        self.screen.blit(panel, panel_pos)

        title = title_font.render(data.PANEL_TITLE_GAME, True, data.INFO_COLOR)
        title_pos = (panel_pos[0] + (panel_width - title.get_width()) // 2,
                     panel_pos[1] + 10)
        self.screen.blit(title, title_pos)

        y_pos = title_pos[1] + 50
        for text, color in items:
            text_surface = font.render(text, True, color)
            self.screen.blit(text_surface, (
                panel_pos[0] + (panel_width - text_surface.get_width()) // 2, y_pos))
            y_pos += data.UI_LINE_SPACING

    def draw_detection_panel(self, pressed_keys, delta_time):
        if pressed_keys is None:
            return
        default_font_size = data.get_scaled_font(data.GAME_DEFAULT_FONT_SIZE, self.screen)
        title_font_size = data.get_scaled_font(data.GAME_TITLE_FONT_SIZE, self.screen)
        font = data.get_font(default_font_size)
        title_font = data.get_font(title_font_size)

        items = []
        for key, name in data.KEYS_TO_MONITOR.items():
            is_pressed = pressed_keys[key]
            status = data.KEY_PRESSED_STATUS if is_pressed else data.KEY_NOT_PRESSED_STATUS
            color = data.KEY_PRESSED_COLOR if is_pressed else data.TEXT_COLOR
            items.append((data.KEY_STATUS_FORMAT.format(name, status), color))

        rec_status = data.RECORDING_STATUS_ON if self.recording else data.RECORDING_STATUS_OFF
        rec_color = data.RECORDING_COLOR if self.recording else (200, 200, 200)
        items.append((data.RECORDING_STATUS_FORMAT.format(rec_status), rec_color))

        adrenaline_status = data.ADRENALINE_ACTIVE if self.player.adrenaline_active else data.ADRENALINE_AVAILABLE
        adrenaline_color = data.ADRENALINE_ACTIVE_COLOR if self.player.adrenaline_active else data.ADRENALINE_AVAILABLE_COLOR
        items.append((data.PLAYER_ADRENALINE_STATUS_FORMAT.format(adrenaline_status), adrenaline_color))

        now = pygame.time.get_ticks() / 1000.0
        if self.player.adrenaline_active:
            remaining = self.player.adrenaline_active_end - now
            items.append((data.PLAYER_ADRENALINE_REMAINING_FORMAT.format(remaining),
                          data.ADRENALINE_REMAINING_COLOR))
        elif now < self.player.adrenaline_cooldown_end:
            cooldown = self.player.adrenaline_cooldown_end - now
            items.append((data.PLAYER_ADRENALINE_COOLDOWN_FORMAT.format(cooldown),
                          data.ADRENALINE_COOLDOWN_COLOR))

        info_texts = [
            data.GAME_INFO_SPEED_FORMAT.format(data.calculate_speed(self.player.velocity)),
            data.GAME_INFO_ACCELERATION_FORMAT.format(data.ACCELERATION),
            data.GAME_INFO_DECELERATION_FORMAT.format(data.DECELERATION),
            data.GAME_INFO_FRICTION_FORMAT.format(data.FRICTION),
            data.GAME_INFO_FRAME_TIME_FORMAT.format(delta_time * 1000),
        ]
        for text in info_texts:
            items.append((text, data.INFO_LIGHT_BLUE))

        max_width = max([font.size(t)[0] for t, _ in items] + [title_font.size(data.PANEL_TITLE_DETECTION)[0]])
        panel_width = max_width + 2 * data.UI_PADDING
        panel_height = data.UI_PADDING * 2 + (len(items) + 2) * data.UI_LINE_SPACING

        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill(data.get_rgba_color(data.PANEL_COLOR, data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, data.UI_HIGHLIGHT, panel.get_rect(), 2)

        panel_pos = data.scale_position(20, 20, self.screen)
        self.screen.blit(panel, panel_pos)

        title = title_font.render(data.PANEL_TITLE_DETECTION, True, data.INFO_COLOR)
        title_pos = (panel_pos[0] + data.UI_PADDING, panel_pos[1] + data.UI_PADDING)
        self.screen.blit(title, title_pos)

        y_pos = title_pos[1] + data.UI_LINE_SPACING * 1.5
        for text, color in items:
            text_surface = font.render(text, True, color)
            self.screen.blit(text_surface, (panel_pos[0] + data.UI_PADDING, y_pos))
            y_pos += data.UI_LINE_SPACING