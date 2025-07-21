# -*- coding: utf-8 -*-
"""
主游戏模块
包含游戏主循环、UI渲染和录制功能
"""

import pygame
import sys
import data
import os
import time
import console
from player import Player

class Game:
    """
    游戏主类
    管理游戏状态、输入处理和渲染
    
    属性:
        running (bool): 游戏运行状态标志
        screen (pygame.Surface): 游戏窗口表面
        player (Player): 玩家角色对象
        clock (pygame.time.Clock): 游戏时钟
        show_detection (bool): 是否显示键盘检测面板
        last_time (float): 上一帧的时间戳
        ground_y (int): 地面Y坐标
        console (Console): 游戏控制台对象
        recording (bool): 是否正在录制
        record_file (file): 录制文件对象
        record_start_time (float): 录制开始时间
    """
    
    def __init__(self, screen):
        """初始化游戏"""
        self.running = True
        self.screen = screen
        self.player = Player()
        self.clock = pygame.time.Clock()
        self.show_detection = False
        self.last_time = pygame.time.get_ticks() / 1000.0
        self.ground_y = data.SCREEN_HEIGHT - 100
        
        # 创建控制台实例
        self.console = console.Console(self)
        
        # 创建游戏背景和UI元素
        self.create_background_grid()
        self.create_ui_elements()
        
        # 录制状态初始化
        self.recording = False
        self.record_file = None
        self.record_start_time = 0
        self.last_record_time = 0
        self.snapshot_interval = 0.2
        self.last_snapshot_time = 0
        self.record_interval = 1.0 / data.RECORD_FPS
        self.last_key_states = {
            'w': False, 'a': False, 's': False, 'd': False, 'shift': False
        }
    
    def create_background_grid(self):
        """创建静态网格背景缓存"""
        self.background_grid = pygame.Surface((data.SCREEN_WIDTH, data.SCREEN_HEIGHT))
        self.background_grid.fill(data.BACKGROUND)
        
        # 绘制垂直网格线
        for x in range(0, data.SCREEN_WIDTH, 40):
            pygame.draw.line(self.background_grid, (50, 50, 70), 
                            (x, 0), (x, data.SCREEN_HEIGHT), 1)
        
        # 绘制水平网格线
        for y in range(0, data.SCREEN_HEIGHT, 40):
            pygame.draw.line(self.background_grid, (50, 50, 70), 
                            (0, y), (data.SCREEN_WIDTH, y), 1)
        
        # 绘制地面线
        pygame.draw.line(self.background_grid, (100, 150, 100), 
                        (0, self.ground_y), 
                        (data.SCREEN_WIDTH, self.ground_y), 3)
    
    def create_ui_elements(self):
        """预创建UI文本内容"""
        self.control_info_texts = [
            "WASD键: 移动玩家",
            "Shift键: 奔跑加速",
            "F1键: 显示/隐藏键盘状态",
            "F2键: 开启/关闭录制",
            "ESC键: 退出游戏"
        ]
        
        self.move_info_texts = [
            "移动系统: 平滑加速物理",
            "按下方向键加速",
            "松开方向键逐渐减速",
            "Shift键增加最大速度"
        ]
    
    def handle_events(self):
        """处理所有游戏事件"""
        for event in pygame.event.get():
            # 优先让控制台处理事件
            if self.console and self.console.state != console.ConsoleState.CLOSED:
                if self.console.handle_event(event):
                    continue
            
            # 退出事件
            if event.type == pygame.QUIT:
                self.stop_recording()
                pygame.quit()
                sys.exit()
            
            # 键盘按下事件
            elif event.type == pygame.KEYDOWN:
                # 控制台切换键
                if event.key == pygame.K_BACKQUOTE:
                    self.console.toggle()
                
                # 退出游戏
                elif event.key == pygame.K_ESCAPE:
                    self.stop_recording()
                    self.running = False
                
                # 显示/隐藏检测面板
                elif event.key == pygame.K_F1:
                    self.show_detection = not self.show_detection
                
                # 开始/停止录制
                elif event.key == pygame.K_F2:
                    if self.recording:
                        self.stop_recording()
                    else:
                        self.start_recording()
            
            # 窗口大小调整事件
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
    
    def start_recording(self):
        """开始游戏录制"""
        if self.recording:
            return
        
        # 创建录制文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"game_recording_{timestamp}.dem"
        
        try:
            # 打开录制文件
            self.record_file = open(filename, 'w')
            self.record_start_time = time.time()
            self.last_record_time = 0
            self.last_snapshot_time = 0
            self.recording = True
            
            # 重置按键状态记录
            self.last_key_states = {
                'w': False, 'a': False, 's': False, 'd': False, 'shift': False
            }
            
            # 写入文件头
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
        if not self.recording:
            return
        
        try:
            if self.record_file:
                self.record_file.close()
                print("录制已停止")
        except Exception as e:
            print(f"停止录制时出错: {str(e)}")
        finally:
            self.recording = False
            self.record_file = None
    
    def record_high_level_command(self, pressed_keys):
        """
        记录高阶指令（按键组合）
        
        参数:
            pressed_keys (dict): 当前按下的按键状态
            
        返回:
            str: 序列化的高阶指令字符串
        """
        command = []
        if pressed_keys[pygame.K_w]: command.append('W')  # 上
        if pressed_keys[pygame.K_s]: command.append('S')  # 下
        if pressed_keys[pygame.K_a]: command.append('A')  # 左
        if pressed_keys[pygame.K_d]: command.append('D')  # 右
        if pressed_keys[pygame.K_LSHIFT] or pressed_keys[pygame.K_RSHIFT]: 
            command.append('SHIFT')  # 冲刺
        
        return ",".join(command)
    
    def record_frame(self, player, pressed_keys):
        """
        记录当前帧数据
        
        格式:
        - 高阶指令 (C:时间,指令)
        - 原始输入变化 (I:时间,变化)
        - 状态快照 (S:时间,位置X,位置Y,速度X,速度Y,冲刺状态)
        """
        if not self.recording or self.record_file is None:
            return
    
        current_time = time.time() - self.record_start_time
    
        # 记录高阶指令 (按固定频率)
        if current_time - self.last_record_time >= self.record_interval:
            command = self.record_high_level_command(pressed_keys)
            self.record_file.write(f"C:{current_time:.3f},{command}\n")
            self.last_record_time = current_time
    
        # 记录原始输入变化 (当按键状态改变时)
        input_changes = []
        for key, key_code in [('w', pygame.K_w), 
                              ('a', pygame.K_a), 
                              ('s', pygame.K_s), 
                              ('d', pygame.K_d), 
                             ('shift', pygame.K_LSHIFT)]:
            key_state = pressed_keys[key_code]
            
            # 检查状态是否有变化
            if key_state != self.last_key_states[key]:
                input_changes.append(f"{key.upper()}:{int(key_state)}")
                self.last_key_states[key] = key_state
    
        # 如果有变化，记录原始输入
        if input_changes:
            self.record_file.write(f"I:{current_time:.3f},{';'.join(input_changes)}\n")
    
        # 记录状态快照 (按固定频率)
        snapshot_interval = 0.2  # 每秒5次
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
        
        步骤:
        1. 计算时间差
        2. 处理玩家输入
        3. 更新玩家状态
        4. 录制当前帧
        
        返回:
            tuple: (按下的按键, 时间差)
        """
        current_time = pygame.time.get_ticks() / 1000.0
        delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # 限制最大时间差，防止卡顿导致异常
        delta_time = min(delta_time, 0.033)
        
        # 获取当前按键状态
        pressed_keys = pygame.key.get_pressed()
        
        # 更新玩家状态
        self.player.update(pressed_keys, delta_time)
        self.player.check_ground(self.ground_y)
        self.player.check_bounds()
        
        # 录制当前帧
        self.record_frame(self.player, pressed_keys)
        
        return pressed_keys, delta_time
    
    def render(self, pressed_keys, delta_time):
        """
        渲染游戏画面
        
        步骤:
        1. 绘制背景
        2. 绘制玩家
        3. 绘制玩家状态信息
        4. 绘制录制状态
        5. 绘制控制台或检测面板
        """
        # 绘制背景
        self.screen.blit(self.background_grid, (0, 0))
        
        # 绘制玩家
        self.player.draw(self.screen)
        
        # 绘制玩家状态信息
        self.draw_player_status()
        
        # 绘制录制状态
        if self.recording:
            rec_text = data.get_font(data.get_scaled_font(24, self.screen)).render(
                "录制中...", True, (255, 50, 50))
            rec_pos = data.scale_position(
                data.SCREEN_WIDTH - rec_text.get_width() - 20, 
                20, 
                self.screen
            )
            self.screen.blit(rec_text, rec_pos)
        
        # 绘制检测面板或控制信息
        if self.show_detection:
            self.draw_detection_panel(pressed_keys, delta_time)
        else:
            self.draw_control_info(pressed_keys)
        
        # 渲染控制台（如果打开）
        if self.console:
            self.console.render(self.screen)
        
        # 更新显示
        pygame.display.flip()
    
    def draw_player_status(self):
        """绘制玩家状态信息"""
        # 移动状态（行走/奔跑）
        status = "奔跑中" if self.player.sprinting else "行走中"
        status_font = data.get_scaled_font(24, self.screen)
        status_text = data.get_font(status_font).render(
            status, True, 
            (255, 200, 0) if self.player.sprinting else (200, 200, 255))
        
        # 创建状态文本背景
        text_rect = status_text.get_rect(center=(
            int(self.player.position[0]), 
            int(self.player.position[1] - 60)
        ))
        bg_rect = text_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, (30, 30, 50, 180), bg_rect, border_radius=5)
        pygame.draw.rect(self.screen, (100, 150, 200), bg_rect, 2, border_radius=5)
        self.screen.blit(status_text, text_rect)
        
        # 速度信息
        speed = data.calculate_speed(self.player.velocity)
        speed_text = data.get_font(data.get_scaled_font(20, self.screen)).render(
            f"速度: {speed:.1f} 像素/秒", True, (180, 230, 255))
        speed_pos = data.scale_position(10, data.SCREEN_HEIGHT - 60, self.screen)
        self.screen.blit(speed_text, speed_pos)
        
        # 位置信息
        pos_text = data.get_font(data.get_scaled_font(20, self.screen)).render(
            f"位置: ({int(self.player.position[0])}, {int(self.player.position[1])})", 
            True, (180, 230, 255))
        pos_pos = data.scale_position(10, data.SCREEN_HEIGHT - 30, self.screen)
        self.screen.blit(pos_text, pos_pos)
        
        # 地面状态
        ground_status = "地面" if self.player.grounded else "空中"
        ground_text = data.get_font(data.get_scaled_font(20, self.screen)).render(
            f"状态: {ground_status}", True, 
            (150, 255, 150) if self.player.grounded else (255, 150, 150))
        ground_pos = data.scale_position(10, data.SCREEN_HEIGHT - 90, self.screen)
        self.screen.blit(ground_text, ground_pos)
    
    def draw_control_info(self, pressed_keys):
        """绘制控制信息面板（非检测面板模式）"""
        # 获取缩放后的字体
        default_font_size = data.get_scaled_font(data.GAME_DEFAULT_FONT_SIZE, self.screen)
        title_font_size = data.get_scaled_font(data.GAME_TITLE_FONT_SIZE, self.screen)
        font = data.get_font(default_font_size)
        title_font = data.get_font(title_font_size)
        
        items = []
        
        # 1. 控制说明
        for control in self.control_info_texts:
            items.append((control, (200, 220, 255)))
        
        # 2. 功能键状态
        f1_status = "已按下" if pressed_keys[pygame.K_F1] else "未按下"
        f1_color = data.KEY_PRESSED_COLOR if pressed_keys[pygame.K_F1] else data.TEXT_COLOR
        items.append((f"F1键状态: {f1_status}", f1_color))
        
        f2_status = "已按下" if pressed_keys[pygame.K_F2] else "未按下"
        f2_color = (255, 50, 50) if self.recording else data.TEXT_COLOR
        items.append((f"F2键状态: {f2_status}", f2_color))
        
        # 3. 录制状态
        rec_status = "开启" if self.recording else "关闭"
        rec_color = (255, 50, 50) if self.recording else (100, 200, 100)
        items.append((f"录制状态: {rec_status}", rec_color))
        
        # 计算面板尺寸
        max_width = 0
        for text, _ in items:
            text_width = font.size(text)[0]
            if text_width > max_width:
                max_width = text_width
        
        title_width = title_font.size("玩家控制演示 (平面移动游戏)")[0]
        max_width = max(max_width, title_width)
        
        panel_width = max_width + 2 * data.UI_PADDING
        panel_height = data.UI_PADDING * 2 + (len(items) + 2) * data.UI_LINE_SPACING
        
        # 绘制面板
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((*data.PANEL_COLOR[:3], data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, (100, 150, 200), panel.get_rect(), 2)
        
        # 面板位置
        panel_pos = data.scale_position(
            (data.BASE_WIDTH - panel_width) // 2, 
            20, 
            self.screen
        )
        self.screen.blit(panel, panel_pos)
        
        # 主标题
        title = title_font.render("玩家控制演示 (平面移动游戏)", True, data.INFO_COLOR)
        title_pos = (
            panel_pos[0] + (panel_width - title.get_width()) // 2,
            panel_pos[1] + 10
        )
        self.screen.blit(title, title_pos)
        
        # 绘制各项内容
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
        """
        绘制键盘状态检测面板
        """
        # 获取缩放后的字体
        default_font_size = data.get_scaled_font(data.GAME_DEFAULT_FONT_SIZE, self.screen)
        title_font_size = data.get_scaled_font(data.GAME_TITLE_FONT_SIZE, self.screen)
        font = data.get_font(default_font_size)
        title_font = data.get_font(title_font_size)
        
        # 面板内容
        items = []
        
        # 1. 键位状态
        for key, name in data.KEYS_TO_MONITOR.items():
            is_pressed = pressed_keys[key]
            status = "按下" if is_pressed else "未按下"
            color = data.KEY_PRESSED_COLOR if is_pressed else data.TEXT_COLOR
            items.append((f"{name}: {status}", color))
        
        # 2. 录制状态
        rec_status = "开启" if self.recording else "关闭"
        rec_color = (255, 50, 50) if self.recording else (200, 200, 200)
        items.append((f"录制状态: {rec_status}", rec_color))
        
        # 3. 物理信息
        info_texts = [
            f"当前速度: {data.calculate_speed(self.player.velocity):.1f} 像素/秒",
            f"加速度: {data.ACCELERATION} 像素/秒²",
            f"减速度: {data.DECELERATION} 像素/秒²",
            f"摩擦力: {data.FRICTION}",
            f"帧时间: {delta_time*1000:.1f} 毫秒"
        ]
        for text in info_texts:
            items.append((text, (200, 220, 255)))
        
        # 计算面板尺寸
        max_width = 0
        for text, _ in items:
            text_width = font.size(text)[0]
            if text_width > max_width:
                max_width = text_width
        
        title_width = title_font.size("键盘状态检测")[0]
        max_width = max(max_width, title_width)
        
        panel_width = max_width + 2 * data.UI_PADDING
        panel_height = data.UI_PADDING * 2 + (len(items) + 2) * data.UI_LINE_SPACING
        
        # 绘制面板
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((*data.PANEL_COLOR[:3], data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, (100, 150, 200), panel.get_rect(), 2)
        
        # 面板位置
        panel_pos = data.scale_position(20, 20, self.screen)
        self.screen.blit(panel, panel_pos)
        
        # 面板标题
        title = title_font.render("键盘状态检测", True, data.INFO_COLOR)
        title_pos = (panel_pos[0] + data.UI_PADDING, panel_pos[1] + data.UI_PADDING)
        self.screen.blit(title, title_pos)
        
        # 绘制各项内容
        y_pos = title_pos[1] + data.UI_LINE_SPACING * 1.5
        for text, color in items:
            text_surface = font.render(text, True, color)
            self.screen.blit(text_surface, (panel_pos[0] + data.UI_PADDING, y_pos))
            y_pos += data.UI_LINE_SPACING

    def run(self):
        """
        运行游戏主循环
        
        步骤:
        1. 处理事件
        2. 更新游戏状态
        3. 更新控制台
        4. 渲染画面
        5. 控制帧率
        """
        self.running = True
        while self.running:
            # 处理输入事件
            self.handle_events()
            
            # 更新游戏状态
            pressed_keys, delta_time = self.update()
            
            # 更新控制台状态
            if self.console:
                self.console.update()
                
            # 渲染游戏画面
            self.render(pressed_keys, delta_time)
            
            # 控制帧率
            self.clock.tick(60)