# -*- coding: utf-8 -*-
"""
主入口模块
包含游戏主菜单和程序入口
"""

from game import Game
from Replay_System import run_replay_mode
import data
import pygame
import sys
from data import MENU_TITLE_FONT_SIZE, MENU_OPTION_FONT_SIZE
from console import Console, ConsoleState  # 导入控制台模块和控制台状态

def main_menu():
    """
    游戏主菜单
    提供游戏选项入口
    """
    pygame.init()
    # 创建可调整大小的窗口
    screen = pygame.display.set_mode((data.SCREEN_WIDTH, data.SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("游戏主菜单")
    
    # 创建控制台实例
    console = Console()
    
    # 主菜单循环
    while True:
        screen.fill(data.BACKGROUND)
        
        # 获取缩放后的字体大小
        title_font_size = data.get_scaled_font(data.MENU_TITLE_FONT_SIZE, screen)
        # 修复这里：添加缺失的屏幕参数
        option_font_size = data.get_scaled_font(data.MENU_OPTION_FONT_SIZE, screen)
        font_title = data.get_font(title_font_size)
        font_option = data.get_font(option_font_size)
        
        # 绘制标题 (居中)
        title = font_title.render("游戏主菜单", True, data.TEXT_COLOR)
        title_pos = (
            screen.get_width() // 2 - title.get_width() // 2,
            data.scale_value(screen.get_height() * 0.2, screen, False)
        )
        screen.blit(title, title_pos)
        
        # 菜单选项
        options = [
            ("开始游戏", data.INFO_COLOR),  # 使用信息文本极速
            ("回放游戏", data.INFO_COLOR),  # 使用信息文本极速
            ("退出", data.EXIT_BUTTON_COLOR)       # 使用退出按钮颜色
        ]
        
        # 绘制选项
        for i, (text, color) in enumerate(options):
            option = font_option.render(text, True, color)
            # 计算位置 (水平居中，垂直间隔)
            x = screen.get_width() // 2 - option.get_width() // 2
            y = data.scale_value(screen.get_height() * 0.4 + i * screen.get_height() * 0.1, screen, False)
            screen.blit(option, (x, y))
        
        # 更新和渲染控制台
        console.update()
        console.render(screen)
        
        pygame.display.flip()
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 窗口关闭
                pygame.quit()
                sys.exit()
            
            # 窗口大小调整事件
            elif event.type == pygame.VIDEORESIZE:  # 窗口大小调整
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:  # 按键事件
                # 反引号键触发控制台
                if event.key == pygame.K_BACKQUOTE:  # 反引号键（`）
                    console.toggle()
                else:
                    # 将事件传递给控制台处理
                    if console.handle_event(event):
                        continue  # 如果控制台处理了事件，跳过其他处理
            
            elif event.type == pygame.MOUSEBUTTONDOWN:  # 鼠标点击
                # 如果控制台打开，跳过菜单点击
                if console.state != ConsoleState.CLOSED:
                    continue
                
                x, y = event.pos
                # 检查点击了哪个选项
                for i, (text, _) in enumerate(options):
                    # 重新获取缩放后的字体大小，确保位置计算准确
                    # 修复这里：添加缺失的屏幕参数
                    current_font_size = data.get_scaled_font(data.MENU_OPTION_FONT_SIZE, screen)
                    current_font = data.get_font(current_font_size)
                    option_surface = current_font.render(text, True, options[i][1])
                    
                    option_width = option_surface.get_width()
                    option_height = option_surface.get_height()
                    option_x = screen.get_width() // 2 - option_width // 2
                    option_y = data.scale_value(screen.get_height() * 0.4 + i * screen.get_height() * 0.1, screen, False)
                    
                    # 检查点击位置是否在选项范围内
                    if (option_x <= x <= option_x + option_width and 
                        option_y <= y <= option_y + option_height):
                        if text == "开始游戏":
                            game = Game(screen)
                            # 将控制台传递给游戏实例
                            game.console = console
                            game.console.game = game  # 设置游戏实例引用
                            game.run()
                        elif text == "回放游戏":
                            run_replay_mode(screen)
                        elif text == "退出":
                            pygame.quit()
                            sys.exit()

if __name__ == "__main__":
    """程序入口"""
    main_menu()