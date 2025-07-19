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

def main_menu():
    """
    游戏主菜单
    提供游戏选项入口
    """
    pygame.init()
    # 创建可调整大小的窗口
    screen = pygame.display.set_mode((data.SCREEN_WIDTH, data.SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("游戏主菜单")
    
    # 创建字体
    font_title = pygame.font.SysFont("simhei", data.UI_TITLE_FONT_SIZE)
    font_option = pygame.font.SysFont("simhei", data.UI_DEFAULT_FONT_SIZE)
    
    # 主菜单循环
    while True:
        screen.fill(data.BACKGROUND)
        
        # 绘制标题 (居中)
        title = font_title.render("游戏主菜单", True, (220, 220, 255))
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, screen.get_height()*0.2))
        
        # 菜单选项
        options = [
            ("开始游戏", (0, 100, 200)),  # 蓝色
            ("回放游戏", (0, 150, 200)),  # 蓝色
            ("退出", (200, 50, 50))       # 红色
        ]
        
        # 绘制选项
        for i, (text, color) in enumerate(options):
            option = font_option.render(text, True, color)
            # 计算位置 (水平居中，垂直间隔)
            x = screen.get_width() // 2 - option.get_width() // 2
            y = screen.get_height() * 0.4 + i * screen.get_height() * 0.1
            screen.blit(option, (x, y))
        
        pygame.display.flip()
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 窗口关闭
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:  # 窗口大小调整
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN:  # 鼠标点击
                x, y = event.pos
                # 检查点击了哪个选项
                for i, (text, _) in enumerate(options):
                    option_width = font_option.size(text)[0]
                    option_height = font_option.size(text)[1]
                    option_x = screen.get_width() // 2 - option_width // 2
                    option_y = screen.get_height() * 0.4 + i * screen.get_height() * 0.1
                    
                    # 检查点击位置是否在选项范围内
                    if (option_x <= x <= option_x + option_width and 
                        option_y <= y <= option_y + option_height):
                        if text == "开始游戏":
                            game = Game(screen)
                            game.run()
                        elif text == "回放游戏":
                            run_replay_mode(screen)
                        elif text == "退出":
                            pygame.quit()
                            sys.exit()

if __name__ == "__main__":
    """程序入口"""
    main_menu()