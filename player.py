"""
玩家模块
包含玩家类(Player)，实现玩家移动、碰撞检测和渲染功能
实现基于物理的移动系统(加速、减速、摩擦力)
"""

import pygame
import data

class Player:
    """
    玩家类
    
    功能概述:
    1. 管理玩家位置、速度和状态
    2. 实现基于物理的移动系统
    3. 处理屏幕边界碰撞
    4. 渲染玩家图形
    
    属性说明:
    - position: 玩家位置[x, y]
    - velocity: 玩家速度[x, y]
    - sprinting: 是否正在冲刺
    - grounded: 是否在地面上
    - image: 玩家图像表面
    - rect: 玩家碰撞矩形
    - render_position: 用于平滑渲染的位置(与真实位置有延迟)
    """

    def __init__(self):
        """初始化玩家对象"""
        # 初始位置在屏幕中央
        self.position = [data.SCREEN_WIDTH / 2.0, data.SCREEN_HEIGHT / 2.0]
        self.velocity = [0.0, 0.0]  # 初始速度为0
        self.sprinting = False  # 冲刺状态
        self.grounded = True  # 是否在地面上(本游戏中始终为True)
        
        # 加载玩家图像
        self.image = data.load_player_image()
        # 创建碰撞矩形
        self.rect = pygame.Rect(0, 0, 80, 80)
        self.rect.center = (int(self.position[0]), int(self.position[1]))
        
        # 用于平滑渲染的位置
        self.render_position = self.position.copy()

    def update(self, pressed_keys, delta_time):
        """
        更新玩家状态
        
        参数:
        - pressed_keys: 当前按下的按键状态
        - delta_time: 距离上一帧的时间
        
        说明:
        1. 检测冲刺状态
        2. 根据按键计算移动方向
        3. 应用加速度和摩擦力
        4. 更新位置和渲染位置
        """
        # 检测是否按下Shift键(冲刺)
        self.sprinting = pressed_keys[pygame.K_LSHIFT] or pressed_keys[pygame.K_RSHIFT]
        
        # 计算最大速度(冲刺时使用冲刺速度)
        max_speed = data.SPRINT_SPEED if self.sprinting else data.WALK_SPEED
        
        # 计算期望移动方向
        wish_dir = [0.0, 0.0]
        if pressed_keys[pygame.K_w]: wish_dir[1] -= 1  # 上
        if pressed_keys[pygame.K_s]: wish_dir[1] += 1  # 下
        if pressed_keys[pygame.K_a]: wish_dir[0] -= 1  # 左
        if pressed_keys[pygame.K_d]: wish_dir[0] += 1  # 右
        
        # 标准化移动方向向量
        wish_length = (wish_dir[0]**2 + wish_dir[1]**2)**0.5
        if wish_length > 0.001:
            wish_dir[0] /= wish_length
            wish_dir[1] /= wish_length
        
        # 计算当前速度在移动方向上的分量
        current_speed = self.velocity[0] * wish_dir[0] + self.velocity[1] * wish_dir[1]
        # 计算可增加的速度
        add_speed = max_speed - current_speed
        
        # 如果可增加速度大于0，则应用加速度
        if add_speed > 0:
            accel = data.ACCELERATION
            # 计算加速度增加的速度
            accel_speed = min(accel * max_speed * delta_time, add_speed)
            # 应用加速度
            self.velocity[0] += accel_speed * wish_dir[0]
            self.velocity[1] += accel_speed * wish_dir[1]
        
        # 计算速度大小
        speed = (self.velocity[0]**2 + self.velocity[1]**2)**0.5
        if speed > 0.001:
            # 应用摩擦力
            drop = speed * data.FRICTION * delta_time
            new_speed = max(speed - drop, 0)
            # 调整速度向量
            self.velocity[0] *= new_speed / speed
            self.velocity[1] *= new_speed / speed
        else:
            # 速度过小时重置为0
            self.velocity = [0.0, 0.0]
        
        # 根据速度更新位置
        self.position[0] += self.velocity[0] * delta_time
        self.position[1] += self.velocity[1] * delta_time
        # 更新碰撞矩形位置
        self.rect.center = (int(self.position[0]), int(self.position[1]))
        
        # 平滑更新渲染位置(用于视觉效果)
        self.render_position[0] += (self.position[0] - self.render_position[0]) * 0.5
        self.render_position[1] += (self.position[1] - self.render_position[1]) * 0.5
    
    def check_ground(self, ground_y):
        """
        检查是否在地面上
        
        参数:
        - ground_y: 地面Y坐标
        
        说明:
        本游戏中始终返回True，预留用于后续扩展
        """
        self.grounded = True
    
    def check_bounds(self):
        """
        检查边界碰撞，防止玩家移出屏幕
        
        说明:
        1. 计算玩家图像尺寸
        2. 限制玩家位置在屏幕范围内
        3. 更新碰撞矩形位置
        """
        # 获取玩家图像尺寸
        img_width, img_height = self.image.get_size()
        
        # 限制X坐标在屏幕范围内
        self.position[0] = max(img_width/2, min(self.position[0], data.SCREEN_WIDTH - img_width/2))
        # 限制Y坐标在屏幕范围内
        self.position[1] = max(img_height/2, min(self.position[1], data.SCREEN_HEIGHT - img_height/2))
        
        # 更新碰撞矩形位置
        self.rect.center = (int(self.position[0]), int(self.position[1]))
    
    def draw(self, screen):
        """
        渲染玩家到屏幕
        
        参数:
        - screen: 游戏屏幕表面
        
        说明:
        使用render_position而不是真实位置，实现平滑的移动效果
        """
        # 计算图像位置(基于渲染位置)
        img_rect = self.image.get_rect(
            center=(int(self.render_position[0]), 
                    int(self.render_position[1]))
        )
        # 渲染玩家图像
        screen.blit(self.image, img_rect)