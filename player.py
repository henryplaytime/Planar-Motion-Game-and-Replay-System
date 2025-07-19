# -*- coding: utf-8 -*-
"""
玩家类模块
包含玩家角色的逻辑和控制
"""

import pygame
import data

class Player:
    """
    玩家角色类
    负责玩家的移动、碰撞检测和渲染
    """
    
    def __init__(self):
        """初始化玩家属性"""
        # 玩家初始位置 (屏幕中心)
        self.position = [data.SCREEN_WIDTH / 2.0, data.SCREEN_HEIGHT / 2.0]
        # 玩家速度向量 [x, y]
        self.velocity = [0.0, 0.0]
        # 是否正在冲刺
        self.sprinting = False
        # 是否在地面上
        self.grounded = True
        # 玩家图像
        self.image = data.load_player_image()
        # 碰撞矩形
        self.rect = pygame.Rect(0, 0, 80, 80)
    
    def update(self, pressed_keys, delta_time):
        """
        更新玩家状态
        
        参数:
            pressed_keys (dict): 当前按下的按键状态
            delta_time (float): 上一帧到当前帧的时间差 (秒)
        """
        # 确定移动速度 (是否冲刺)
        self.sprinting = pressed_keys[pygame.K_LSHIFT] or pressed_keys[pygame.K_RSHIFT]
        max_speed = data.SPRINT_SPEED if self.sprinting else data.WALK_SPEED
        
        # 计算期望移动方向 (基于按键)
        wish_dir = [0.0, 0.0]  # [x, y]
        if pressed_keys[pygame.K_w]: wish_dir[1] -= 1  # 上
        if pressed_keys[pygame.K_s]: wish_dir[1] += 1  # 下
        if pressed_keys[pygame.K_a]: wish_dir[0] -= 1  # 左
        if pressed_keys[pygame.K_d]: wish_dir[0] += 1  # 右
        
        # 归一化期望方向向量
        wish_length = (wish_dir[0]**2 + wish_dir[1]**2)**0.5
        if wish_length > 0:
            wish_dir[0] /= wish_length
            wish_dir[1] /= wish_length
        
        # 计算当前速度在期望方向上的投影
        current_speed = self.velocity[0] * wish_dir[0] + self.velocity[1] * wish_dir[1]
        
        # 计算可以增加的速度
        add_speed = max_speed - current_speed
        if add_speed > 0:
            # 应用加速度
            accel = data.ACCELERATION
            accel_speed = min(accel * max_speed * delta_time, add_speed)
            self.velocity[0] += accel_speed * wish_dir[0]
            self.velocity[1] += accel_speed * wish_dir[1]
        
        # 应用摩擦力 (地面摩擦)
        speed = (self.velocity[0]**2 + self.velocity[1]**2)**0.5
        if speed > 0:
            drop = speed * data.FRICTION * delta_time
            new_speed = max(speed - drop, 0)
            self.velocity[0] *= new_speed / speed
            self.velocity[1] *= new_speed / speed
        
        # 更新位置
        self.position[0] += self.velocity[0] * delta_time
        self.position[1] += self.velocity[1] * delta_time
        
        # 更新碰撞矩形位置
        self.rect.center = (int(self.position[0]), int(self.position[1]))
    
    def check_ground(self, ground_y):
        """
        地面检测 (平面游戏中始终在地面)
        
        参数:
            ground_y (int): 地面y坐标 (未使用)
        """
        # 平面游戏中，玩家始终在地面
        self.grounded = True
    
    def check_bounds(self):
        """确保玩家不会移出屏幕边界"""
        # X轴边界检查
        self.position[0] = max(40, min(self.position[0], data.SCREEN_WIDTH - 40))
        # Y轴边界检查
        self.position[1] = max(40, min(self.position[1], data.SCREEN_HEIGHT - 40))
        # 更新碰撞矩形位置
        self.rect.center = (int(self.position[0]), int(self.position[1]))
    
    def draw(self, screen):
        """
        绘制玩家到屏幕
        
        参数:
            screen (pygame.Surface): 游戏窗口表面
        """
        # 绘制玩家图像 (中心点对齐)
        screen.blit(self.image, (self.position[0] - 40, self.position[1] - 40))