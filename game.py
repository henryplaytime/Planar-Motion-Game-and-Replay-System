"""
游戏主模块
包含游戏主循环、事件处理、状态更新和渲染逻辑
实现玩家控制、录制系统、UI界面等核心功能
"""

import pygame
import data
import os
import sys
import time
import json
import console
from data import create_background_grid
from player import Player
from enum import Enum

class GameState(Enum):
    """游戏状态枚举"""
    NORMAL = 0  # 正常游戏状态
    REPLAY = 1  # 回放状态

class Game:
    """
    游戏主类
    
    功能概述:
    1. 管理游戏主循环
    2. 处理用户输入事件
    3. 更新游戏状态
    4. 渲染游戏画面
    5. 管理录制系统
    """
    
    def __init__(self, screen):
        """初始化游戏对象"""
        self.screen = screen  # Pygame屏幕对象
        self.clock = pygame.time.Clock()  # 游戏时钟
        self.console = console.Console(self)  # 控制台对象

        self.record_interval = 1.0 / data.RECORD_FPS  # 录制间隔时间
        
        # 初始化游戏状态
        self.running = True
        self.show_detection = False
        self.recording = False
        self.game_state = GameState.NORMAL  # 添加游戏状态
        
        # 初始化游戏对象
        self.player = Player()
        self._init_time_variables()
        self._init_recording()
        
        # 初始化UI元素
        self.ground_y = data.SCREEN_HEIGHT - data.GROUND_OFFSET
        self.background_grid = create_background_grid(screen)
        self.create_ui_elements()
        
        # 加载肾上腺素配置
        self.adrenaline_config = self.load_adrenaline_config()
        self.last_q_pressed = False
    
    def _init_time_variables(self):
        """初始化时间相关变量"""
        self.last_time = pygame.time.get_ticks() / 1000.0
        self.record_start_time = 0
        self.last_record_time = 0
        self.last_snapshot_time = 0
    
    def _init_recording(self):
        """初始化录制状态"""
        self.record_file = None
        self.last_key_states = {  # 按键状态缓存
            'w': False, 'a': False, 's': False, 'd': False, 'shift': False
        }
    
    def load_adrenaline_config(self):
        """
        从item.json加载肾上腺素配置
        
        返回:
        - dict: 包含速度倍率、持续时间和冷却时间的字典
        """
        try:
            # 构建配置文件路径 - 指向config文件夹
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "config", 
                "item.json"
            )
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 获取肾上腺素配置
            item_config = config_data["items"].get("adrenaline", {})
            effects = item_config.get("effects", {})
            
            # 添加默认值以防配置缺失
            return {
                "speed_multiplier": effects.get("speed_multiplier", 1.5),
                "duration": effects.get("duration", 5.0),
                "cooldown": effects.get("cooldown", 15.0)
            }
        except Exception as e:
            print(f"加载肾上腺素配置失败: {str(e)}")
            # 返回默认配置
            return {
                "speed_multiplier": 1.5,
                "duration": 5.0,
                "cooldown": 15.0
            }
    
    def create_ui_elements(self):
        """创建UI元素文本"""
        self.control_info_texts = data.CONTROL_INFO_TEXTS
        self.move_info_texts = data.MOVE_INFO_TEXTS
    
    def run(self):
        """运行游戏主循环"""
        while self.running:
            self.handle_events()  # 处理事件
            pressed_keys, delta_time = self.update()  # 更新状态
            self.update_console()  # 更新控制台
            self.render(pressed_keys, delta_time)  # 渲染画面
            self.clock.tick(60)  # 限制帧率
    
    def update_console(self):
        """更新控制台状态"""
        if self.console:
            self.console.update()
    
    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            # 如果控制台打开，优先处理控制台事件
            if self.console and self.console.state != console.ConsoleState.CLOSED:
                if self.console.handle_event(event):
                    continue
                    
            # 处理退出事件
            if event.type == pygame.QUIT:
                self.stop_recording()
                pygame.quit()
                sys.exit()
                
            # 处理按键事件
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKQUOTE:  # 反引号键
                    self.console.toggle()  # 切换控制台
                elif event.key == pygame.K_ESCAPE:  # ESC键
                    self.stop_recording()
                    self.running = False  # 退出游戏
                elif event.key == pygame.K_F1:  # F1键
                    self.show_detection = not self.show_detection  # 切换检测面板
                elif event.key == pygame.K_F2:  # F2键
                    if self.recording:
                        self.stop_recording()  # 停止录制
                    else:
                        self.start_recording()  # 开始录制
                        
            # 处理窗口大小变化事件
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
    
    def start_recording(self):
        """开始游戏录制"""
        if self.recording: return  # 如果已经在录制则返回
        timestamp = data.get_timestamp()  # 生成时间戳
        filename = f"game_recording_{timestamp}.dem"  # 生成文件名
        try:
            self.record_file = open(filename, 'w')  # 打开录制文件
            self.record_start_time = time.time()  # 记录开始时间
            self.last_record_time = 0  # 重置上次记录时间
            self.last_snapshot_time = 0  # 重置上次快照时间
            self.recording = True  # 设置录制状态
            # 重置按键状态缓存
            self.last_key_states = {
                'w': False, 'a': False, 's': False, 'd': False, 'shift': False
            }
            # 写入录制文件头信息
            self.record_file.write(f"VERSION: {data.RECORD_VERSION}\n")
            self.record_file.write(f"SCREEN_WIDTH: {data.SCREEN_WIDTH}\n")
            self.record_file.write(f"SCREEN_HEIGHT: {data.SCREEN_HEIGHT}\n")
            self.record_file.write(f"RECORD_FPS: {data.RECORD_FPS}\n")
            self.record_file.write(f"START_TIME: {self.record_start_time}\n")
            print(f"开始录制: {filename}")
        except Exception as e:
            print(f"开始录制失败: {str(e)}")
            self.recording = False
    
    def stop_recording(self):
        """停止游戏录制"""
        if not self.recording: return  # 如果不在录制则返回
        try:
            if self.record_file:
                self.record_file.close()  # 关闭录制文件
                print("录制已停止")
        except Exception as e:
            print(f"停止录制时出错: {str(e)}")
        finally:
            self.recording = False
            self.record_file = None
    
    def record_high_level_command(self, pressed_keys):
        """序列化高阶命令"""
        return data.serialize_high_level_command(pressed_keys)
    
    def record_frame(self, player, pressed_keys):
        """
        记录当前帧数据
        
        参数:
        - player: 玩家对象
        - pressed_keys: 按键状态列表
        """
        if not self.recording or self.record_file is None: return
        current_time = time.time() - self.record_start_time  # 当前录制时间
        
        # 记录高阶命令
        if current_time - self.last_record_time >= self.record_interval:
            command = self.record_high_level_command(pressed_keys)
            self.record_file.write(f"C:{current_time:.3f},{command}\n")
            self.last_record_time = current_time
        
        # 记录输入变化
        input_changes = []
        for key, key_code in [('w', pygame.K_w), 
                              ('a', pygame.K_a), 
                              ('s', pygame.K_s), 
                              ('d', pygame.K_d), 
                             ('shift', pygame.K_LSHIFT)]:
            key_state = pressed_keys[key_code]  # 当前按键状态
            # 检查状态是否变化
            if key_state != self.last_key_states[key]:
                input_changes.append(f"{key.upper()}:{int(key_state)}")  # 记录变化
                self.last_key_states[key] = key_state  # 更新状态缓存
        
        # 如果有变化则写入文件
        if input_changes:
            self.record_file.write(f"I:{current_time:.3f},{';'.join(input_changes)}\n")
        
        # 记录状态快照
        snapshot_interval = 0.2
        if current_time - self.last_snapshot_time >= snapshot_interval:
            self.record_file.write(
                f"S:{current_time:.3f},"
                f"{player.position[0]:.3f},{player.position[1]:.3f},"
                f"{player.velocity[0]:.3f},{player.velocity[1]:.3f},"
                f"{int(player.sprinting)}\n"
            )
            self.last_snapshot_time = current_time

    def update(self):
        """
        更新游戏状态
        
        返回:
        - pressed_keys: 当前按键状态
        - delta_time: 距离上一帧的时间
        """
        current_time = pygame.time.get_ticks() / 1000.0  # 当前时间
        delta_time = current_time - self.last_time  # 时间增量
        self.last_time = current_time
        delta_time = min(delta_time, 0.033)  # 限制最大增量(约30FPS)
        
        pressed_keys = pygame.key.get_pressed()  # 获取按键状态
        
        # 处理肾上腺素激活
        self._handle_adrenaline_activation(pressed_keys, current_time)
        
        # 更新玩家状态
        self.player.update(pressed_keys, delta_time)
        self.player.check_ground(self.ground_y)
        
        # 记录当前帧
        self.record_frame(self.player, pressed_keys)
        
        return pressed_keys, delta_time
    
    def _handle_adrenaline_activation(self, pressed_keys, current_time):
        """处理肾上腺素激活逻辑"""
        if pressed_keys[pygame.K_q] and not self.last_q_pressed:
            # 检查是否在冷却时间内
            if current_time >= self.player.adrenaline_cooldown_end:
                # 激活肾上腺素效果
                success = self.player.activate_adrenaline(
                    self.adrenaline_config["duration"],
                    self.adrenaline_config["cooldown"],
                    self.adrenaline_config["speed_multiplier"]
                )
                if success:
                    print("肾上腺素激活!")
        
        self.last_q_pressed = pressed_keys[pygame.K_q]
    
    def render(self, pressed_keys, delta_time):
        """渲染游戏画面"""
        # 渲染背景
        self.screen.blit(self.background_grid, (0, 0))
        
        # 渲染玩家
        self.player.draw(self.screen)
        
        # 渲染玩家状态
        self.draw_player_status()
        
        # 如果正在录制，显示录制状态
        if self.recording:
            self.draw_recording_indicator()
        
        # 根据设置渲染检测面板或控制信息
        if self.show_detection:
            self.draw_detection_panel(pressed_keys, delta_time)
        else:
            self.draw_control_info(pressed_keys)
        
        # 渲染控制台
        if self.console:
            self.console.render(self.screen)
        
        # 更新显示
        pygame.display.flip()
    
    def draw_recording_indicator(self):
        """渲染录制状态指示器"""
        rec_text = data.get_font(data.get_scaled_font(data.INFO_FONT_SIZE, self.screen)).render(
            data.RECORDING_TEXT, True, data.RECORDING_COLOR)
        rec_pos = data.scale_position(
            data.SCREEN_WIDTH - rec_text.get_width() - 20, 
            20, 
            self.screen
        )
        self.screen.blit(rec_text, rec_pos)
    
    def draw_player_status(self):
        """渲染玩家状态信息"""
        # 渲染状态文本(行走/奔跑)
        status = data.PLAYER_STATUS_RUNNING if self.player.sprinting else data.PLAYER_STATUS_WALKING
        status_font = data.get_scaled_font(data.INFO_FONT_SIZE, self.screen)
        status_text = data.get_font(status_font).render(
            status, True, 
            data.STATUS_RUNNING_COLOR if self.player.sprinting else data.STATUS_WALKING_COLOR)
        text_rect = status_text.get_rect(center=(
            int(self.player.position[0]), 
            int(self.player.position[1] - 60)
        ))
        
        # 渲染状态背景
        bg_rect = text_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, data.get_rgba_color(data.PANEL_COLOR), bg_rect, border_radius=5)
        pygame.draw.rect(self.screen, data.UI_HIGHLIGHT, bg_rect, 2, border_radius=5)
        self.screen.blit(status_text, text_rect)
        
        # 渲染速度信息
        speed = data.calculate_speed(self.player.velocity)
        speed_text = data.get_font(data.get_scaled_font(data.SMALL_FONT_SIZE, self.screen)).render(
            data.PLAYER_SPEED_FORMAT.format(speed), True, data.INFO_LIGHT_BLUE)
        speed_pos = data.scale_position(10, data.SCREEN_HEIGHT - 60, self.screen)
        self.screen.blit(speed_text, speed_pos)
        
        # 渲染位置信息
        pos_text = data.get_font(data.get_scaled_font(data.SMALL_FONT_SIZE, self.screen)).render(
            data.PLAYER_POSITION_FORMAT.format(
                int(self.player.position[0]), 
                int(self.player.position[1])), 
            True, data.INFO_LIGHT_BLUE)
        pos_pos = data.scale_position(10, data.SCREEN_HEIGHT - 30, self.screen)
        self.screen.blit(pos_text, pos_pos)
        
        # 渲染地面状态
        ground_status = data.PLAYER_STATUS_GROUND if self.player.grounded else data.PLAYER_STATUS_AIR
        ground_text = data.get_font(data.get_scaled_font(data.SMALL_FONT_SIZE, self.screen)).render(
            data.PLAYER_STATUS_FORMAT.format(ground_status), True, 
            data.STATUS_GROUND_COLOR if self.player.grounded else data.STATUS_AIR_COLOR)
        ground_pos = data.scale_position(10, data.SCREEN_HEIGHT - 90, self.screen)
        self.screen.blit(ground_text, ground_pos)
        
        # 渲染肾上腺素状态
        if self.player.adrenaline_active:
            adrenaline_text = data.get_font(data.get_scaled_font(data.SMALL_FONT_SIZE, self.screen)).render(
                data.PLAYER_ADRENALINE_ACTIVE, True, data.ADRENALINE_ACTIVE_COLOR)
            adrenaline_pos = data.scale_position(
                10, data.SCREEN_HEIGHT - 120, self.screen)
            self.screen.blit(adrenaline_text, adrenaline_pos)
    
    def draw_control_info(self, pressed_keys):
        """渲染控制信息面板"""
        # 获取字体
        default_font_size = data.get_scaled_font(data.GAME_DEFAULT_FONT_SIZE, self.screen)
        title_font_size = data.get_scaled_font(data.GAME_TITLE_FONT_SIZE, self.screen)
        font = data.get_font(default_font_size)
        title_font = data.get_font(title_font_size)
        
        # 创建信息项
        items = []
        for control in self.control_info_texts:
            items.append((control, data.TEXT_COLOR))
        
        # F1键状态
        f1_status = data.KEY_PRESSED_STATUS if pressed_keys[pygame.K_F1] else data.KEY_NOT_PRESSED_STATUS
        f1_color = data.KEY_PRESSED_COLOR if pressed_keys[pygame.K_F1] else data.TEXT_COLOR
        items.append((data.KEY_STATUS_FORMAT.format("F1键状态", f1_status), f1_color))
        
        # F2键状态
        f2_status = data.KEY_PRESSED_STATUS if pressed_keys[pygame.K_F2] else data.KEY_NOT_PRESSED_STATUS
        f2_color = data.RECORDING_COLOR if self.recording else data.TEXT_COLOR
        items.append((data.KEY_STATUS_FORMAT.format("F2键状态", f2_status), f2_color))
        
        # 录制状态
        rec_status = data.RECORDING_STATUS_ON if self.recording else data.RECORDING_STATUS_OFF
        rec_color = data.RECORDING_COLOR if self.recording else (100, 200, 100)
        items.append((data.RECORDING_STATUS_FORMAT.format(rec_status), rec_color))
        
        # 肾上腺素状态
        adrenaline_status = data.ADRENALINE_ACTIVE if self.player.adrenaline_active else data.ADRENALINE_AVAILABLE
        adrenaline_color = data.ADRENALINE_ACTIVE_COLOR if self.player.adrenaline_active else data.ADRENALINE_AVAILABLE_COLOR
        items.append((data.PLAYER_ADRENALINE_STATUS_FORMAT.format(adrenaline_status), adrenaline_color))
        
        # 计算面板尺寸
        max_width = 0
        for text, _ in items:
            text_width = font.size(text)[0]
            if text_width > max_width:
                max_width = text_width
        title_width = title_font.size(data.PANEL_TITLE_GAME)[0]
        max_width = max(max_width, title_width)
        panel_width = max_width + 2 * data.UI_PADDING
        panel_height = data.UI_PADDING * 2 + (len(items) + 2) * data.UI_LINE_SPACING
        
        # 创建面板
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill(data.get_rgba_color(data.PANEL_COLOR, data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, data.UI_HIGHLIGHT, panel.get_rect(), 2)
        
        # 渲染面板
        panel_pos = data.scale_position(
            (data.BASE_WIDTH - panel_width) // 2, 
            20, 
            self.screen
        )
        self.screen.blit(panel, panel_pos)
        
        # 渲染标题
        title = title_font.render(data.PANEL_TITLE_GAME, True, data.INFO_COLOR)
        title_pos = (
            panel_pos[0] + (panel_width - title.get_width()) // 2,
            panel_pos[1] + 10
        )
        self.screen.blit(title, title_pos)
        
        # 渲染信息项
        y_pos = title_pos[1] + 50
        for text, color in items:
            text_surface = font.render(text, True, color)
            text_pos = (
                panel_pos[0] + (panel_width - text_surface.get_width()) // 2,
                y_pos
            )
            self.screen.blit(text_surface, text_pos)
            y_pos += data.UI_LINE_SPACING

    def draw_detection_panel(self, pressed_keys, delta_time):
        """渲染检测面板"""
        # 获取字体
        default_font_size = data.get_scaled_font(data.GAME_DEFAULT_FONT_SIZE, self.screen)
        title_font_size = data.get_scaled_font(data.GAME_TITLE_FONT_SIZE, self.screen)
        font = data.get_font(default_font_size)
        title_font = data.get_font(title_font_size)
        
        # 创建按键状态项
        items = []
        for key, name in data.KEYS_TO_MONITOR.items():
            is_pressed = pressed_keys[key]  # 按键状态
            status = data.KEY_PRESSED_STATUS if is_pressed else data.KEY_NOT_PRESSED_STATUS
            color = data.KEY_PRESSED_COLOR if is_pressed else data.TEXT_COLOR
            items.append((data.KEY_STATUS_FORMAT.format(name, status), color))
        
        # 录制状态
        rec_status = data.RECORDING_STATUS_ON if self.recording else data.RECORDING_STATUS_OFF
        rec_color = data.RECORDING_COLOR if self.recording else (200, 200, 200)
        items.append((data.RECORDING_STATUS_FORMAT.format(rec_status), rec_color))
        
        # 添加肾上腺素状态项
        adrenaline_status = data.ADRENALINE_ACTIVE if self.player.adrenaline_active else data.ADRENALINE_AVAILABLE
        adrenaline_color = data.ADRENALINE_ACTIVE_COLOR if self.player.adrenaline_active else data.ADRENALINE_AVAILABLE_COLOR
        items.append((data.PLAYER_ADRENALINE_STATUS_FORMAT.format(adrenaline_status), adrenaline_color))
        
        # 如果激活中，显示剩余时间
        if self.player.adrenaline_active:
            remaining = self.player.adrenaline_active_end - (pygame.time.get_ticks() / 1000.0)
            items.append((data.PLAYER_ADRENALINE_REMAINING_FORMAT.format(remaining), data.ADRENALINE_REMAINING_COLOR))
        
        # 如果在冷却中，显示冷却时间
        elif (pygame.time.get_ticks() / 1000.0) < self.player.adrenaline_cooldown_end:
            cooldown = self.player.adrenaline_cooldown_end - (pygame.time.get_ticks() / 1000.0)
            items.append((data.PLAYER_ADRENALINE_COOLDOWN_FORMAT.format(cooldown), data.ADRENALINE_COOLDOWN_COLOR))
        
        # 添加游戏信息项
        info_texts = [
            data.GAME_INFO_SPEED_FORMAT.format(data.calculate_speed(self.player.velocity)),
            data.GAME_INFO_ACCELERATION_FORMAT.format(data.ACCELERATION),
            data.GAME_INFO_DECELERATION_FORMAT.format(data.DECELERATION),
            data.GAME_INFO_FRICTION_FORMAT.format(data.FRICTION),
            data.GAME_INFO_FRAME_TIME_FORMAT.format(delta_time*1000)
        ]
        for text in info_texts:
            items.append((text, data.INFO_LIGHT_BLUE))
        
        # 计算面板尺寸
        max_width = 0
        for text, _ in items:
            text_width = font.size(text)[0]
            if text_width > max_width:
                max_width = text_width
        title_width = title_font.size(data.PANEL_TITLE_DETECTION)[0]
        max_width = max(max_width, title_width)
        panel_width = max_width + 2 * data.UI_PADDING
        panel_height = data.UI_PADDING * 2 + (len(items) + 2) * data.UI_LINE_SPACING
        
        # 创建面板
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill(data.get_rgba_color(data.PANEL_COLOR, data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, data.UI_HIGHLIGHT, panel.get_rect(), 2)
        
        # 渲染面板
        panel_pos = data.scale_position(20, 20, self.screen)
        self.screen.blit(panel, panel_pos)
        
        # 渲染标题
        title = title_font.render(data.PANEL_TITLE_DETECTION, True, data.INFO_COLOR)
        title_pos = (panel_pos[0] + data.UI_PADDING, panel_pos[1] + data.UI_PADDING)
        self.screen.blit(title, title_pos)
        
        # 渲染信息项
        y_pos = title_pos[1] + data.UI_LINE_SPACING * 1.5
        for text, color in items:
            text_surface = font.render(text, True, color)
            self.screen.blit(text_surface, (panel_pos[0] + data.UI_PADDING, y_pos))
            y_pos += data.UI_LINE_SPACING
    
    def force_replay(self, filename):
        """强制启动回放模式"""
        self.replay_file = filename
        self.game_state = GameState.REPLAY  # 使用枚举值