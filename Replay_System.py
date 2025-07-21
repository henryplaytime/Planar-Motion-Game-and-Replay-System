# -*- coding: utf-8 -*-
"""
游戏回放系统模块
包含回放功能实现、回放控制和UI界面
"""

import pygame
import sys
import os
import glob
import time
import bisect
import data
import random
import math
import traceback
from enum import Enum
from collections import namedtuple
from data import SCREEN_WIDTH, SCREEN_HEIGHT, BACKGROUND, load_player_image, get_font, calculate_speed, PANEL_COLOR, TEXT_COLOR, INFO_COLOR
from player import Player

# === 回放状态枚举 ===
class ReplayState(Enum):
    """
    回放状态枚举
    定义回放系统的各种播放状态
    """
    PLAYING = 1    # 正常播放状态
    PAUSED = 2     # 暂停状态
    FAST_FORWARD = 3  # 快进状态
    REWIND = 4      # 后退状态

# 定义快照数据结构
Snapshot = namedtuple('Snapshot', ['time', 'pos_x', 'pos_y', 'vel_x', 'vel_y', 'sprinting', 'adrenaline'])

# === 回放系统类 ===
class GameReplayer:
    """
    游戏回放类
    负责加载、解析和控制回放数据
    """
    
    def __init__(self, filename, screen):
        """
        初始化回放器
        
        参数:
            filename (str): 回放文件名
            screen (pygame.Surface): 游戏窗口表面
        """
        self.filename = filename  # 回放文件名
        self.screen = screen      # 游戏窗口表面
        self.commands = []        # 高阶指令序列 (时间戳, 指令)
        self.inputs = []          # 原始输入序列 (时间戳, 输入变化)
        self.snapshots = []       # 状态快照序列 (Snapshot对象)
        self.current_time = 0.0    # 当前播放时间 (秒)
        self.playback_speed = 1.0  # 播放速度倍数
        self.state = ReplayState.PLAYING  # 当前回放状态
        self.start_time = 0        # 回放开始时间
        self.total_time = 0        # 回放总时长
        self.last_update_time = 0  # 上次更新时间
        self.player = Player()     # 回放玩家对象
        self.current_command_index = 0  # 当前处理的高阶指令索引
        self.current_input_index = 0    # 当前处理的原始输入索引
        self.current_snapshot_index = 0  # 当前处理的状态快照索引
        self.last_frame_time = 0  # 用于检测是否卡住
        self.simulated_keys = {  # 模拟按键状态
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_LSHIFT: False,
            pygame.K_RSHIFT: False,
            pygame.K_q: False
        }
        
        # 用于位置插值的关键变量
        self.last_snapshot = None  # 最后应用的状态快照
        self.next_snapshot = None   # 下一个状态快照
        self.snapshot_blend = 0.0   # 快照混合因子
        # 添加肾上腺素状态
        self.adrenaline_active = False
        self.adrenaline_particles = []
        
        # 加载录制数据
        self.load_recording()
    
    def load_recording(self):
        """加载并解析回放文件"""
        try:
            record_version = 1  # 默认版本1 (旧格式)
            with open(self.filename, 'r') as f:
                # 读取文件头
                for line in f:
                    if line.startswith("VERSION:"):
                        record_version = int(line.split(":")[1].strip())
                        continue
                    elif line.startswith("SCREEN_WIDTH:"):
                        # 解析屏幕宽度 (实际未使用，保留兼容性)
                        continue
                    elif line.startswith("SCREEN_HEIGHT:"):
                        # 解析屏幕高度 (实际未使用，保留兼容性)
                        continue
                    elif line.startswith("START_TIME:"):
                        # 解析开始时间
                        self.start_time = float(line.split(":")[1].strip())
                        continue
                    elif line.startswith("RECORD_FPS:"):
                        # 解析录制帧率 (实际未使用，保留兼容性)
                        continue
                    elif "," in line:  # 数据行
                        # 根据版本解析数据
                        if record_version == 1:
                            # 旧格式: 时间,位置x,位置y,速度x,速度y,冲刺状态
                            parts = line.strip().split(",")
                            if len(parts) >= 6:
                                # 旧版本没有肾上腺素字段，默认设为False
                                snapshot = Snapshot(
                                    time=float(parts[0]),
                                    pos_x=float(parts[1]),
                                    pos_y=float(parts[2]),
                                    vel_x=float(parts[3]),
                                    vel_y=float(parts[4]),
                                    sprinting=bool(int(parts[5])),
                                    adrenaline=False  # 旧版本没有肾上腺素
                                )
                                self.snapshots.append(snapshot)
                        elif record_version >= 2:
                            # 新格式: 类型:时间,数据
                            prefix, data_part = line.split(":", 1)
                            data_parts = data_part.strip().split(",")
                            timestamp = float(data_parts[0])
                            
                            if prefix == "C":  # 高阶指令
                                command = data_parts[1] if len(data_parts) > 1 else ""
                                self.commands.append((timestamp, command))
                            
                            elif prefix == "I":  # 原始输入
                                changes = data_parts[1] if len(data_parts) > 1 else ""
                                self.inputs.append((timestamp, changes))
                            
                            elif prefix == "S":  # 状态快照
                                if len(data_parts) >= 6:
                                    # 兼容性处理：检查是否有肾上腺素字段
                                    adrenaline_state = False
                                    if len(data_parts) >= 7:
                                        try:
                                            adrenaline_state = bool(int(data_parts[6]))
                                        except:
                                            adrenaline_state = False
                                
                                    snapshot = Snapshot(
                                        time=timestamp,
                                        pos_x=float(data_parts[1]),
                                        pos_y=float(data_parts[2]),
                                        vel_x=float(data_parts[3]),
                                        vel_y=float(data_parts[4]),
                                        sprinting=bool(int(data_parts[5])),
                                        adrenaline=adrenaline_state
                                    )
                                    self.snapshots.append(snapshot)
        
            # 检查是否有有效数据
            if self.snapshots:
                # 设置总时长 (最后一帧的时间戳)
                self.total_time = max(
                    self.snapshots[-1].time if self.snapshots else 0,
                    self.commands[-1][0] if self.commands else 0,
                    self.inputs[-1][0] if self.inputs else 0
                )
                print(f"已加载回放 (版本 {record_version}):")
                print(f"  高阶指令: {len(self.commands)}条")
                print(f"  原始输入: {len(self.inputs)}条")
                print(f"  状态快照: {len(self.snapshots)}个")
                print(f"  总时长: {self.total_time:.2f}秒")
                
                # 初始化快照参考
                self.find_surrounding_snapshots(self.current_time)
            else:
                print("错误: 回放文件中没有有效数据")
        except Exception as e:
            print(f"加载回放文件失败: {str(e)}")
            traceback.print_exc()
            self.snapshots = []
            self.commands = []
            self.inputs = []
    def find_surrounding_snapshots(self, target_time):
        """找到包围目标时间的两个快照（前一个和后一个）"""
        if not self.snapshots or len(self.snapshots) < 2:
            return None, None
            
        # 获取所有快照的时间列表
        snapshot_times = [snapshot.time for snapshot in self.snapshots]
        
        # 使用二分查找找到目标时间的位置
        idx = bisect.bisect_left(snapshot_times, target_time)
        
        # 处理边界情况
        if idx == 0:
            return self.snapshots[0], self.snapshots[1] if len(self.snapshots) > 1 else self.snapshots[0]
        elif idx >= len(self.snapshots):
            return self.snapshots[-2], self.snapshots[-1] if len(self.snapshots) > 1 else self.snapshots[-1]
        
        return self.snapshots[idx-1], self.snapshots[idx]
    
    def apply_command(self, command_str):
        """
        应用高阶指令到玩家
        
        参数:
            command_str (str): 高阶指令字符串
        """
        if not command_str:
            return
        
        # 解析指令字符串
        commands = command_str.split(",")
        
        # 更新模拟按键状态
        self.simulated_keys[pygame.K_w] = 'W' in commands
        self.simulated_keys[pygame.K_s] = 'S' in commands
        self.simulated_keys[pygame.K_a] = 'A' in commands
        self.simulated_keys[pygame.K_d] = 'D' in commands
        self.simulated_keys[pygame.K_LSHIFT] = 'SHIFT' in commands
        self.simulated_keys[pygame.K_RSHIFT] = 'SHIFT' in commands
        
        # 应用指令到玩家
        self.player.update(self.simulated_keys, 1.0 / data.RECORD_FPS)
    
    def apply_input_changes(self, input_str):
        """
        应用原始输入变化
        
        参数:
            input_str (str): 输入变化字符串
        """
        if not input_str:
            return
        
        # 解析输入变化
        changes = input_str.split(";")
        for change in changes:
            if ":" in change:
                key, state = change.split(":")
                if key.upper() == "SHIFT":
                # 设置左右 Shift 键的状态
                    self.simulated_keys[pygame.K_LSHIFT] = bool(int(state))
                    self.simulated_keys[pygame.K_RSHIFT] = bool(int(state))
                else:
                    try:
                        key_lower = key.lower()
                        key_code = getattr(pygame, f"K_{key_lower}")
                        self.simulated_keys[key_code] = bool(int(state))
                    except AttributeError:
                        print(f"警告: 未知按键 {key}")
            

    def apply_interpolated_snapshot(self):
        """应用插值后的状态快照（平滑过渡）"""
        if not self.last_snapshot or not self.next_snapshot:
            return
        
            
        prev = self.last_snapshot
        next = self.next_snapshot
        blend = self.snapshot_blend

        # 确保prev.time <= next.time
        if prev.time > next.time:
            prev, next = next, prev

        
        
        # 计算混合因子（0.0-1.0）
        total = next.time - prev.time
        if total > 0:
            blend = (self.current_time - prev.time) / total
        else:
            blend = 0.0
            
        # 位置插值
        target_x = prev.pos_x + (next.pos_x - prev.pos_x) * blend
        target_y = prev.pos_y + (next.pos_y - prev.pos_y) * blend
        
        # 速度插值
        target_vel_x = prev.vel_x + (next.vel_x - prev.vel_x) * blend
        target_vel_y = prev.vel_y + (next.vel_y - prev.vel_y) * blend
        
        # 冲刺状态（在0.5阈值处切换）
        sprinting = prev.sprinting if blend < 0.5 else next.sprinting

        # 肾上腺素状态（在0.5阈值处切换）
        adrenaline = prev.adrenaline if blend < 0.5 else next.adrenaline

        # 如果肾上腺素状态变化
        if adrenaline and not self.adrenaline_active:
            self._activate_adrenaline_effect()
        self.adrenaline_active = adrenaline
        
        # 应用插值后的状态（平滑过渡）
        self.player.position[0] += (target_x - self.player.position[0]) * 0.3
        self.player.position[1] += (target_y - self.player.position[1]) * 0.3
        self.player.velocity[0] += (target_vel_x - self.player.velocity[0]) * 0.5
        self.player.velocity[1] += (target_vel_y - self.player.velocity[1]) * 0.5
        self.player.sprinting = sprinting
        
        # 更新碰撞矩形位置
        self.player.rect.center = (int(self.player.position[0]), int(self.player.position[1]))
    
    def update(self, delta_time):
        """
        更新回放状态
        
        参数:
            delta_time (float): 时间差 (秒)
        """
        if self.state == ReplayState.PAUSED:
            return
        
        # 计算实际时间步长 (考虑播放速度)
        actual_delta = delta_time * self.playback_speed

        # 检测是否卡住
        current_frame_time = time.time()
        if (self.state == ReplayState.REWIND and 
            abs(current_frame_time - self.last_frame_time) < 0.001 and
            self.current_time > 0):
            print("检测到卡住，重置索引")
            self.reset_indices()
        self.last_frame_time = current_frame_time
        
        # 根据状态更新当前时间
        if self.state == ReplayState.PLAYING:
            self.current_time += actual_delta
        elif self.state == ReplayState.FAST_FORWARD:
            self.current_time += actual_delta * 2.0
        elif self.state == ReplayState.REWIND:
            self.current_time -= actual_delta * 2.0
        
        # 确保时间在有效范围内 [0, total_time]
        self.current_time = max(0, min(self.current_time, self.total_time))
        
        # 更新快照参考
        self.last_snapshot, self.next_snapshot = self.find_surrounding_snapshots(self.current_time)
        
        # 检查是否需要重置索引（当时间回退超过当前索引）
        if self.state == ReplayState.REWIND:
            # 重置命令索引
            self.current_command_index = 0
            for i, (timestamp, _) in enumerate(self.commands):
                if timestamp <= self.current_time:
                    self.current_command_index = i
                else:
                    break
        
            # 重置输入索引
            self.current_input_index = 0
            for i, (timestamp, _) in enumerate(self.inputs):
                if timestamp <= self.current_time:
                    self.current_input_index = i
                else:
                    break
    
        # 应用所有当前时间点之前的命令
        while (self.current_command_index < len(self.commands) and 
               self.commands[self.current_command_index][0] <= self.current_time):
            _, command = self.commands[self.current_command_index]
            self.apply_command(command)
            self.current_command_index += 1
        
        # 应用所有当前时间点之前的输入变化
        while (self.current_input_index < len(self.inputs) and 
               self.inputs[self.current_input_index][0] <= self.current_time):
            _, input_changes = self.inputs[self.current_input_index]
            self.apply_input_changes(input_changes)
            self.current_input_index += 1
        
        # 应用插值后的状态快照
        if self.last_snapshot and self.next_snapshot:
            self.apply_interpolated_snapshot()
    
    def draw_ui(self, screen):
        """
        绘制回放控制UI
        
        参数:
            screen (pygame.Surface): 游戏窗口表面
        """
        # 获取缩放后的字体
        default_font_size = data.get_scaled_font(data.REPLAY_DEFAULT_FONT_SIZE, screen)
        title_font_size = data.get_scaled_font(data.REPLAY_TITLE_FONT_SIZE, screen)
        font = data.get_font(default_font_size)
        title_font = data.get_font(title_font_size)
        
        # 控制说明文本
        controls = [
            "空格键: 播放/暂停",
            "→: 快进",
            "←: 后退",
            "↑: 增加速度",
            "↓: 减少速度",
            "J: 跳转到指定时间",
            "ESC: 退出回放"
        ]
        
        # === 计算面板尺寸 ===
        # 计算最大文本宽度
        max_width = 0
        for text in controls:
            text_width = font.size(text)[0]
            if text_width > max_width:
                max_width = text_width
        
        # 添加标题和状态文本宽度
        title_width = title_font.size("游戏回放系统")[0]
        time_text = f"时间: {self.current_time:.1f}/{self.total_time:.1f}秒"
        time_width = font.size(time_text)[0]
        state_text = f"状态: {self.state.name} | 速度: x{self.playback_speed:.1f}"
        state_width = font.size(state_text)[0]
        
        max_width = max(max_width, title_width, time_width, state_width)
        
        # 计算面板尺寸
        panel_width = max_width + 2 * data.UI_PADDING
        panel_height = data.UI_PADDING * 2 + (len(controls) + 3) * data.UI_LINE_SPACING
        
        # === 绘制面板 ===
        # 创建半透明面板
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((*data.PANEL_COLOR[:3], data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, (100, 150, 200), panel.get_rect(), 2)
        
        # 位置缩放 (右上角)
        panel_pos = data.scale_position(
            data.BASE_WIDTH - panel_width - 20, 
            20, 
            screen
        )
        screen.blit(panel, panel_pos)
        
        # 标题
        title = title_font.render("游戏回放系统", True, data.INFO_COLOR)
        screen.blit(title, (panel_pos[0] + (panel_width - title.get_width()) // 2, panel_pos[1] + 10))
        
        # 回放时间信息
        time_text = font.render(time_text, True, data.TEXT_COLOR)
        screen.blit(time_text, (panel_pos[0] + (panel_width - time_text.get_width()) // 2, panel_pos[1] + 50))
        
        # 状态信息
        state_text = font.render(state_text, True, data.TEXT_COLOR)
        screen.blit(state_text, (panel_pos[0] + (panel_width - state_text.get_width()) // 2, panel_pos[1] + 80))
        
        # 在状态文本中添加肾上腺素状态
        state_text = f"状态: {self.state.name} | 速度: x{self.playback_speed:.1f}"
        if self.adrenaline_active:
            state_text += " | 肾上腺素激活"

        # 控制说明
        y_pos = panel_pos[1] + 120
        for text in controls:
            ctrl_text = font.render(text, True, data.TEXT_COLOR)
            screen.blit(ctrl_text, (panel_pos[0] + data.UI_PADDING, y_pos))
            y_pos += data.UI_LINE_SPACING
    
    def draw_progress_bar(self, screen):
        """
        绘制回放进度条
        
        参数:
            screen (pygame.Surface): 游戏窗口表面
        """
        if self.total_time <= 0:
            return
        
        # 获取缩放后的字体
        info_font_size = data.get_scaled_font(data.REPLAY_INFO_FONT_SIZE, screen)
        font = data.get_font(info_font_size)
        
        # 进度条尺寸
        bar_width = data.scale_value(600, screen)
        bar_height = data.scale_value(20, screen, False)
        
        # 进度条位置 (底部居中)
        bar_x = (screen.get_width() - bar_width) // 2
        bar_y = screen.get_height() - data.scale_value(50, screen, False)
        
        # 进度条背景
        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (60, 60, 80), bar_rect)
        pygame.draw.rect(screen, (100, 100, 120), bar_rect, 2)
        
        # 进度条前景 (已播放部分)
        progress = self.current_time / self.total_time
        fill_width = int(bar_width * progress)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
        pygame.draw.rect(screen, (80, 180, 250), fill_rect)
        
        # 当前位置标记
        marker_pos = bar_x + fill_width
        pygame.draw.line(screen, (255, 255, 255), 
                        (marker_pos, bar_y - 5), 
                        (marker_pos, bar_y + bar_height + 5), 3)
        
        # 时间标签
        time_text = font.render(
            f"{self.current_time:.1f}s / {self.total_time:.1f}s", 
            True, TEXT_COLOR
        )
        time_pos = (
            (screen.get_width() - time_text.get_width()) // 2,
            bar_y - data.UI_LINE_SPACING
        )
        screen.blit(time_text, time_pos)

    def draw_effects(self, screen):
        """绘制肾上腺素特效"""
        # 绘制粒子
        for particle in self.adrenaline_particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            color = (*data.ADRENALINE_COLOR[:3], alpha)
            pygame.draw.circle(
                screen, 
                color, 
                (int(particle['pos'][0]), int(particle['pos'][1])),
                int(particle['size'] * (particle['life'] / particle['max_life']))
            )
    
        # 如果肾上腺素激活，绘制光环效果
        if self.adrenaline_active:
            pulse = abs(math.sin(pygame.time.get_ticks() / 200.0))
            radius = 50 + 10 * pulse
            pygame.draw.circle(
                screen, 
                data.ADRENALINE_COLOR, 
                (int(self.player.position[0]), int(self.player.position[1])),
                int(radius), 
                3
            )

    def reset_indices(self):
        """完全重置所有索引到当前时间点"""
        # 重置命令索引
        self.current_command_index = 0
        for i, (timestamp, _) in enumerate(self.commands):
            if timestamp <= self.current_time:
                self.current_command_index = i
    
        # 重置输入索引
        self.current_input_index = 0
        for i, (timestamp, _) in enumerate(self.inputs):
            if timestamp <= self.current_time:
                self.current_input_index = i
    
        # 重置快照索引
        self.current_snapshot_index = 0
        for i, snapshot in enumerate(self.snapshots):
            if snapshot.time <= self.current_time:
                self.current_snapshot_index = i

    def _activate_adrenaline_effect(self):
        """激活肾上腺素特效"""
        self.adrenaline_particles = []
        for _ in range(20):
            self._create_adrenaline_particle()

    def _create_adrenaline_particle(self):
        """创建肾上腺素特效粒子"""
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 200)
        size = random.uniform(3, 10)

        self.adrenaline_particles.append({
            'pos': list(self.player.position),
            'vel': [math.cos(angle) * speed, math.sin(angle) * speed],
            'size': size,
            'life': 1.0,
            'max_life': random.uniform(0.3, 0.8)
        })

    def _update_adrenaline_particles(self, delta_time):
        """更新特效粒子"""
        for particle in self.adrenaline_particles[:]:
            particle['life'] -= delta_time
            if particle['life'] <= 0:
                self.adrenaline_particles.remove(particle)
                continue
        
            # 更新位置
            particle['pos'][0] += particle['vel'][0] * delta_time
            particle['pos'][1] += particle['vel'][1] * delta_time

            # 减慢速度
            particle['vel'][0] *= 0.9
            particle['vel'][1] *= 0.9

# === 背景网格创建函数 ===
def create_background_grid(screen):
    """
    创建静态网格背景缓存
    
    参数:
        screen (pygame.Surface): 游戏窗口表面
    
    返回:
        pygame.Surface: 背景网格表面
    """
    ground_y = screen.get_height() - data.scale_value(100, screen, False)
    background_grid = pygame.Surface(screen.get_size())
    background_grid.fill(data.BACKGROUND)
    
    grid_size = data.scale_value(40, screen)
    
    for x in range(0, screen.get_width(), int(grid_size)):
        pygame.draw.line(background_grid, (50, 50, 70), 
                        (x, 0), (x, screen.get_height()), 1)
    for y in range(0, screen.get_height(), int(grid_size)):
        pygame.draw.line(background_grid, (50, 50, 70), 
                        (0, y), (screen.get_width(), y), 1)
    
    pygame.draw.line(background_grid, (100, 150, 100), 
                    (0, ground_y), 
                    (screen.get_width(), ground_y), 3)
    return background_grid

# === 回放模式主循环 ===
def run_replay_mode(screen):
    """
    运行回放模式主循环
    
    参数:
        screen (pygame.Surface): 游戏窗口表面
    """
    pygame.display.set_caption("游戏回放模式")
    clock = pygame.time.Clock()

    # 添加主循环标志
    running_replay = True
    
    pygame.font.init()
    replay_files = glob.glob("*.dem")
    
    if not replay_files:
        # 使用正确的常量名称
        font = pygame.font.SysFont("simhei", data.REPLAY_TITLE_FONT_SIZE)
        title = font.render("没有找到回放文件", True, (255, 100, 100))
        subtitle = font.render("请先玩游戏并录制回放", True, (200, 200, 200))
        
        while running_replay:
            screen.fill(BACKGROUND)
            screen.blit(title, (screen.get_width()//2 - title.get_width()//2, screen.get_height()//2 - 50))
            screen.blit(subtitle, (screen.get_width()//2 - subtitle.get_width()//2, screen.get_height()//2 + 50))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    return
                elif event.type == pygame.VIDEORESIZE:
                    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            
            pygame.display.flip()
            clock.tick(60)
        return
    
    selected_file = None
    # 使用正确的常量名称
    font_title = pygame.font.SysFont("simhei", data.REPLAY_TITLE_FONT_SIZE)
    font_file = pygame.font.SysFont("simhei", data.REPLAY_DEFAULT_FONT_SIZE)
    
    while not selected_file and running_replay:
        screen.fill(BACKGROUND)
        
        title = font_title.render("选择回放文件", True, INFO_COLOR)
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 100))
        
        for i, filename in enumerate(replay_files):
            color = (200, 200, 255)
            text = font_file.render(f"{i+1}. {os.path.basename(filename)}", True, color)
            screen.blit(text, (screen.get_width()//2 - text.get_width()//2, 200 + i*60))
        
        hint = font_file.render("按ESC返回主菜单", True, (150, 200, 150))
        screen.blit(hint, (screen.get_width()//2 - hint.get_width()//2, screen.get_height() - 100))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running_replay = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if pygame.K_1 <= event.key <= pygame.K_9:
                    index = event.key - pygame.K_1
                    if index < len(replay_files):
                        selected_file = replay_files[index]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for i in range(len(replay_files)):
                    text_y = 200 + i*60
                    if text_y <= y <= text_y + 40:
                        selected_file = replay_files[i]
                        break
    
    # 如果用户按ESC取消了选择
    if not selected_file:
        return
    
    
    
    try:
        replayer = GameReplayer(selected_file, screen)
        background = create_background_grid(screen)
        
        if not replayer.snapshots and not replayer.commands:
            print("错误: 没有有效的回放数据")
            # 显示错误信息
            error_font = pygame.font.SysFont("simhei", 36)
            error_text = error_font.render("回放文件无效或格式错误", True, (255, 100, 100))
            screen.fill(BACKGROUND)
            screen.blit(error_text, (screen.get_width()//2 - error_text.get_width()//2, 
                                   screen.get_height()//2 - error_text.get_height()//2))
            pygame.display.flip()
            pygame.time.wait(2000)  # 显示2秒错误信息
            return
        
        pygame.display.set_caption(f"游戏回放: {os.path.basename(selected_file)}")
        
        last_time = time.time()
        
        while running_replay:
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_replay = False
                elif event.type == pygame.VIDEORESIZE:
                    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    background = create_background_grid(screen)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running_replay = False
                    elif event.key == pygame.K_SPACE:
                        if replayer.state == ReplayState.PAUSED:
                            replayer.state = ReplayState.PLAYING
                        else:
                            replayer.state = ReplayState.PAUSED
                    elif event.key == pygame.K_RIGHT:
                        replayer.state = ReplayState.FAST_FORWARD
                    elif event.key == pygame.K_LEFT:
                        replayer.state = ReplayState.REWIND
                    elif event.key == pygame.K_UP:
                        replayer.playback_speed = min(5.0, replayer.playback_speed + 0.5)
                    elif event.key == pygame.K_DOWN:
                        replayer.playback_speed = max(0.1, replayer.playback_speed - 0.5)
                    elif event.key == pygame.K_j:
                        try:
                            target_time = float(input("请输入跳转时间(秒): "))
                            replayer.current_time = max(0, min(target_time, replayer.total_time))
                            
                            # === 完全重置索引 ===
                            # 重置命令索引
                            replayer.current_command_index = 0
                            for i, (timestamp, _) in enumerate(replayer.commands):
                                if timestamp <= replayer.current_time:
                                    replayer.current_command_index = i
                                else:
                                    break
            
                            # 重置输入索引
                            replayer.current_input_index = 0
                            for i, (timestamp, _) in enumerate(replayer.inputs):
                                if timestamp <= replayer.current_time:
                                    replayer.current_input_index = i
                                else:
                                    break
            
                            # 重置快照索引
                            replayer.current_snapshot_index = 0
                            for i, snapshot in enumerate(replayer.snapshots):
                                if snapshot.time <= replayer.current_time:
                                    replayer.current_snapshot_index = i
                                else:
                                    break
                        except:
                            print("无效的时间输入")
            
            # 更新回放状态
            replayer.update(delta_time)
            # 绘制背景
            screen.blit(background, (0, 0))
            # 绘制玩家
            replayer.player.draw(screen)
    
            # 绘制肾上腺素特效
            replayer.draw_effects(screen)
            
            replayer.draw_ui(screen)
            replayer.draw_progress_bar(screen)
            
            pygame.display.flip()
            clock.tick(60)
            
    except Exception as e:
        import traceback
        print(f"回放过程中发生错误: {str(e)}")
        traceback.print_exc()
        
        # 显示错误信息
        error_font = pygame.font.SysFont("simhei", 36)
        error_text = error_font.render(f"回放错误: {str(e)}", True, (255, 100, 100))
        screen.fill(BACKGROUND)
        screen.blit(error_text, (screen.get_width()//2 - error_text.get_width()//2, 
                               screen.get_height()//2 - error_text.get_height()//2))
        pygame.display.flip()
        pygame.time.wait(3000)  # 显示3秒错误信息