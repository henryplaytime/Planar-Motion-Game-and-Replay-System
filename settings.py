"""
设置模块
包含设置界面相关的所有常量、函数和UI逻辑
当主程序需要进入设置界面时，会调用此模块
"""

import pygame
import os
import json
import sys
from data import (
    BACKGROUND, TEXT_COLOR, ACCENT_COLOR, PANEL_COLOR, UI_HIGHLIGHT,
    MENU_TITLE_FONT_SIZE, DEFAULT_FONT_SIZE, INFO_FONT_SIZE,
    SOUND_MENU_CLICK, SOUND_MENU_HOVER,
    get_font, get_scaled_font, scale_value, get_scaled_button_rect,
    STYLE_NAMES, BUTTON_CLICK_ANIMATION_DELAY
)
from source.menu_btn_style import create_button

# === 设置界面常量 ===
SETTINGS_MENU_TITLE = "设置"
SETTINGS_MENU_INFO = "按ESC键返回主菜单"

# 设置分类
SETTINGS_CATEGORIES = [
    {"name": "界面", "icon": ""},
    {"name": "音频", "icon": ""},
    {"name": "游戏性", "icon": ""},
    {"name": "控制", "icon": ""},
]

# 设置项描述
SETTINGS_DESCRIPTIONS = {
    "界面": [
        "此部分允许您自定义游戏的视觉外观。",
        "",
        "按钮样式: 选择游戏按钮的视觉风格。",
        "使命召唤风格提供更现代、更专业的",
        "外观，而默认风格则更简洁。"
    ],
    "音频": [
        "此部分控制游戏的所有音频设置。"
    ],
    "游戏性": [
        "此部分控制游戏的玩法设置。"
    ],
    "控制": [
        "此部分控制游戏的按键绑定。"
    ]
}

# === 设置项控件类 ===
class StyleSelector:
    """按钮样式选择器"""
    def __init__(self, x, y, width, height, current_style, available_styles):
        """
        初始化样式选择器
        
        参数:
            x, y: 位置
            width: 总宽度
            height: 高度
            current_style: 当前样式名称
            available_styles: 可用样式列表
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.available_styles = available_styles
        self.current_index = available_styles.index(current_style)
        
        # 创建左右箭头按钮
        arrow_width = height  # 箭头宽度等于高度
        self.left_arrow = pygame.Rect(x, y, arrow_width, height)
        self.right_arrow = pygame.Rect(x + width - arrow_width, y, arrow_width, height)
        self.text_area = pygame.Rect(x + arrow_width, y, width - 2 * arrow_width, height)

        # 添加悬停状态
        self.left_hovered = False
        self.right_hovered = False
        self.text_hovered = False

    def draw(self, screen):
        """绘制样式选择器"""
        # 绘制背景
        pygame.draw.rect(screen, PANEL_COLOR, self.rect, border_radius=5)
        pygame.draw.rect(screen, ACCENT_COLOR, self.rect, 2, border_radius=5)
        
        # 绘制左右箭头
        font_size = get_scaled_font(DEFAULT_FONT_SIZE, screen)
        font = get_font(font_size)
        
        # 左箭头
        left_color = UI_HIGHLIGHT if self.left_hovered else TEXT_COLOR
        pygame.draw.polygon(screen, left_color, [
            (self.left_arrow.centerx + 5, self.left_arrow.centery - 8),
            (self.left_arrow.centerx - 5, self.left_arrow.centery),
            (self.left_arrow.centerx + 5, self.left_arrow.centery + 8)
        ])
        
        # 右箭头
        right_color = UI_HIGHLIGHT if self.right_hovered else TEXT_COLOR
        pygame.draw.polygon(screen, right_color, [
            (self.right_arrow.centerx - 5, self.right_arrow.centery - 8),
            (self.right_arrow.centerx + 5, self.right_arrow.centery),
            (self.right_arrow.centerx - 5, self.right_arrow.centery + 8)
        ])
        
        # 绘制当前样式名称
        text_color = UI_HIGHLIGHT if self.text_hovered else TEXT_COLOR
        style_name = STYLE_NAMES.get(self.get_current_style(), "默认")
        text = font.render(style_name, True, text_color)
        screen.blit(text, (self.text_area.centerx - text.get_width() // 2, 
                  self.text_area.centery - text.get_height() // 2))
    
    def handle_event(self, event):
        """处理选择器点击事件"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.left_arrow.collidepoint(event.pos):
                # 添加点击反馈
                self.left_hovered = True
                pygame.display.flip()
                pygame.time.delay(BUTTON_CLICK_ANIMATION_DELAY)

                self.current_index = (self.current_index - 1) % len(self.available_styles)
                return True
            elif self.right_arrow.collidepoint(event.pos):
                # 添加点击反馈
                self.right_hovered = True
                pygame.display.flip()
                pygame.time.delay(BUTTON_CLICK_ANIMATION_DELAY)

                self.current_index = (self.current_index + 1) % len(self.available_styles)
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # 重置点击状态
            self.left_hovered = False
            self.right_hovered = False
        return False
    
    def get_current_style(self):
        """获取当前选中的样式"""
        return self.available_styles[self.current_index]
    
    def check_hover(self, mouse_pos):
        """检查鼠标是否悬停在控件上"""
        return (
            self.left_arrow.collidepoint(mouse_pos) or 
            self.right_arrow.collidepoint(mouse_pos) or 
            self.text_area.collidepoint(mouse_pos)
        )
    
    def update_hover_state(self, mouse_pos):
        """更新悬停状态（避免重复触发）"""
        prev_left = self.left_hovered
        prev_right = self.right_hovered
        prev_text = self.text_hovered
        
        self.left_hovered = self.left_arrow.collidepoint(mouse_pos)
        self.right_hovered = self.right_arrow.collidepoint(mouse_pos)
        self.text_hovered = self.text_area.collidepoint(mouse_pos)
        
        # 返回是否状态有变化
        return (prev_left != self.left_hovered or 
                prev_right != self.right_hovered or 
                prev_text != self.text_hovered)

def create_settings_buttons(screen, button_style):
    """
    创建设置界面的按钮
    
    参数:
        screen: Pygame屏幕对象
        button_style: 按钮样式
        
    返回:
        按钮列表
    """
    button_width = 200  # 设置按钮宽度
    button_height = 50   # 设置按钮高度
    button_y = screen.get_height() - 100  # 按钮Y位置
    
    buttons = [
        create_button(
            button_style,
            screen.get_width() // 2 - button_width - 20, 
            button_y, 
            button_width, 
            button_height, 
            "返回", 
            screen
        ),
        create_button(
            button_style,
            screen.get_width() // 2 + 20, 
            button_y, 
            button_width, 
            button_height, 
            "应用", 
            screen
        )
    ]
    
    return buttons

def create_settings_controls(screen, user_config):
    """
    创建设置控件
    参数:
        screen: Pygame屏幕对象
        user_config: 用户配置字典
    返回:
        控件字典，按分类组织
    """
    # 创建控件容器
    controls = {
        "界面": [],
        "音频": [],
        "游戏性": [],
        "控制": []
    }
    
    # 界面设置控件
    settings_panel = pygame.Rect(20, 180, screen.get_width() // 2 - 40, 300)
    control_width = 300  # 控件宽度
    control_height = 50  # 控件高度
    
    # 按钮样式选择器
    available_styles = list(STYLE_NAMES.keys())
    current_style = user_config.get("button_style", available_styles[0])
    style_selector = StyleSelector(
        settings_panel.x + settings_panel.width - control_width - 20,
        settings_panel.y + 20,
        control_width,
        control_height,
        current_style,
        available_styles
    )
    controls["界面"].append(("按钮样式", style_selector))
    
    return controls

def settings_menu(screen, console, current_style, user_config):
    """
    设置菜单函数 - 重构为分页式界面
    
    参数:
        screen: Pygame屏幕对象
        console: 控制台对象
        current_style: 当前按钮样式
        user_config: 用户配置字典
        
    返回:
        元组 (是否需要重新创建主菜单按钮, 新的按钮样式)
    """
    button_style = current_style
    
    
    # 创建设置按钮
    buttons = create_settings_buttons(screen, button_style)
    
    # 创建设置控件
    settings_controls = create_settings_controls(screen, user_config)
    
    # 音频
    try:
        click_sound = pygame.mixer.Sound(SOUND_MENU_CLICK)
        hover_sound = pygame.mixer.Sound(SOUND_MENU_HOVER)
    except:
        click_sound = None
        hover_sound = None
    
    # 当前选中的选项索引
    current_selected = -1
    last_hover_index = -1
    current_category = 0
    
    # 记录初始样式
    initial_style = current_style
    style_changed = False
    
    # 添加变量跟踪悬停状态
    hover_changed = False

    # 设置菜单循环
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        # 更新所有控件的悬停状态
        hover_changed = False
        current_category_name = SETTINGS_CATEGORIES[current_category]["name"]
        category_controls = settings_controls.get(current_category_name, [])
        
        for setting_name, control in category_controls:
            if hasattr(control, 'update_hover_state'):
                hover_changed = control.update_hover_state(mouse_pos) or hover_changed
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # 窗口大小调整
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                buttons = create_settings_buttons(screen, button_style)
                settings_controls = create_settings_controls(screen, user_config)
            
            # 键盘事件
            elif event.type == pygame.KEYDOWN:
                # 控制台切换键
                if event.key == pygame.K_BACKQUOTE:
                    console.toggle()
                    continue
                # ESC键返回主菜单
                elif event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    if console.handle_event(event):
                        continue
            
            # 鼠标移动事件
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
                # 首先更新控件悬停状态
                hover_changed = False
                for setting_name, control in category_controls:
                    if hasattr(control, 'update_hover_state'):
                        hover_changed = control.update_hover_state(mouse_pos) or hover_changed

                
                # 检查分类按钮悬停
                category_hovered = False
                category_width = screen.get_width() // len(SETTINGS_CATEGORIES)
                for i in range(len(SETTINGS_CATEGORIES)):
                    rect = pygame.Rect(i * category_width, 100, category_width, 60)
                    if rect.collidepoint(mouse_pos):
                        if i != last_hover_index:
                            current_selected = i
                            if hover_sound and not hover_changed:
                                hover_sound.play()
                                hover_changed = True
                            last_hover_index = i
                        category_hovered = True
                        break
                    
                # 检查设置选项悬停
                button_hovered = False  # 确保变量被初始化
                if not category_hovered:
                    button_hovered = False
                    for i, button in enumerate(buttons):
                        scaled_rect = get_scaled_button_rect(button, screen)
                        if scaled_rect.collidepoint(mouse_pos):
                            if (len(SETTINGS_CATEGORIES) + i) != last_hover_index:
                                current_selected = len(SETTINGS_CATEGORIES) + i
                                if hover_sound and not hover_changed:
                                    hover_sound.play()
                                    hover_changed = True
                                last_hover_index = len(SETTINGS_CATEGORIES) + i
                            button_hovered = True
                            break
                
                # 如果都没有悬停，重置
                if not category_hovered and not button_hovered and not hover_changed:
                    if last_hover_index != -1:
                        current_selected = -1
                        last_hover_index = -1
            
            # 鼠标点击事件
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    # 检查分类按钮点击
                    category_width = screen.get_width() // len(SETTINGS_CATEGORIES)
                    for i in range(len(SETTINGS_CATEGORIES)):
                        rect = pygame.Rect(i * category_width, 100, category_width, 60)
                        if rect.collidepoint(event.pos):
                            if click_sound:
                                click_sound.play()
                            current_category = i
                            break
                    
                    # 检查底部按钮点击
                    for i, button in enumerate(buttons):
                        scaled_rect = get_scaled_button_rect(button, screen)
                        if scaled_rect.collidepoint(event.pos):
                            if click_sound:
                                click_sound.play()
                            
                            # 设置按钮点击状态
                            button.state = "active"
                            
                            # 立即绘制一次动画状态
                            draw_settings_ui(
                                screen, 
                                console, 
                                SETTINGS_CATEGORIES, 
                                current_category, 
                                buttons, 
                                settings_controls
                            )
                            pygame.display.flip()
                            pygame.time.delay(BUTTON_CLICK_ANIMATION_DELAY)
                            
                            # 处理设置选择
                            if i == 0:  # 返回按钮
                                running = False
                            elif i == 1:  # 应用按钮
                                # 保存设置到配置文件
                                save_settings(user_config, button_style, settings_controls)
                                console.core.add_output("设置已保存")
                                running = False
                            break
                    
                    # 检查设置控件点击
                    current_category_name = SETTINGS_CATEGORIES[current_category]["name"]
                    category_controls = settings_controls.get(current_category_name, [])
                    
                    for setting_name, control in category_controls:
                        if control.handle_event(event):
                            # 添加点击音效
                            if click_sound:
                                click_sound.play()

                            # 处理按钮样式切换
                            if setting_name == "按钮样式":
                                button_style = control.get_current_style()
                                style_changed = True
                                console.core.add_output(f"按钮样式已切换为 {STYLE_NAMES.get(button_style, '默认')}")
                                # 重新创建按钮以应用新样式
                                buttons = create_settings_buttons(screen, button_style)
                            break # 避免多次触发
        
        # 更新按钮状态
        for button in buttons:
            button.state = "idle"
        
        if current_selected >= len(SETTINGS_CATEGORIES) and current_selected < len(SETTINGS_CATEGORIES) + len(buttons):
            buttons[current_selected - len(SETTINGS_CATEGORIES)].state = "hover"
        
        mouse_click = False
        for button in buttons:
            button.update(mouse_pos, mouse_click)
        
        # 渲染设置界面
        draw_settings_ui(
            screen, 
            console, 
            SETTINGS_CATEGORIES, 
            current_category, 
            buttons, 
            settings_controls
        )
        
        pygame.display.flip()
    
    # 返回样式是否被更改
    return style_changed or button_style != initial_style, button_style

def draw_settings_ui(screen, console, categories, current_category, buttons, settings_controls):
    """
    绘制设置界面的UI元素
    
    参数:
        screen: Pygame屏幕对象
        console: 控制台对象
        categories: 设置分类列表
        current_category: 当前选中的分类索引
        buttons: 按钮列表
        settings_controls: 设置控件字典
    """
    # 绘制背景
    screen.fill(BACKGROUND)
    
    # 绘制标题
    title_font_size = get_scaled_font(MENU_TITLE_FONT_SIZE, screen)
    font_title = get_font(title_font_size)
    title = font_title.render(SETTINGS_MENU_TITLE, True, TEXT_COLOR)
    title_pos = (
        screen.get_width() // 2 - title.get_width() // 2,
        scale_value(screen.get_height() * 0.05, screen, False)
    )
    screen.blit(title, title_pos)
    
    # 绘制分类标签栏
    category_width = screen.get_width() // len(categories)
    category_height = 60
    category_y = 100
    
    for i, category in enumerate(categories):
        # 绘制分类背景
        bg_color = UI_HIGHLIGHT if i == current_category else PANEL_COLOR
        category_rect = pygame.Rect(i * category_width, category_y, category_width, category_height)
        pygame.draw.rect(screen, bg_color, category_rect)
        pygame.draw.rect(screen, ACCENT_COLOR, category_rect, 2)
        
        # 绘制分类名称
        cat_font_size = get_scaled_font(DEFAULT_FONT_SIZE, screen)
        font_cat = get_font(cat_font_size)
        text = font_cat.render(f"{category['icon']} {category['name']}", True, TEXT_COLOR)
        screen.blit(text, (i * category_width + category_width // 2 - text.get_width() // 2, 
                          category_y + category_height // 2 - text.get_height() // 2))
    
    # 绘制分割线
    pygame.draw.line(screen, ACCENT_COLOR, (0, category_y + category_height), 
                   (screen.get_width(), category_y + category_height), 3)
    
    # 绘制设置区域
    settings_panel = pygame.Rect(20, category_y + category_height + 20, screen.get_width() // 2 - 40, 
                               screen.get_height() - category_y - category_height - 160)
    description_panel = pygame.Rect(screen.get_width() // 2 + 20, category_y + category_height + 20, 
                                  screen.get_width() // 2 - 40, screen.get_height() - category_y - category_height - 160)
    
    # 绘制面板背景
    pygame.draw.rect(screen, PANEL_COLOR, settings_panel)
    pygame.draw.rect(screen, ACCENT_COLOR, settings_panel, 2)
    pygame.draw.rect(screen, PANEL_COLOR, description_panel)
    pygame.draw.rect(screen, ACCENT_COLOR, description_panel, 2)
    
    # 根据当前分类绘制设置选项
    font_size = get_scaled_font(DEFAULT_FONT_SIZE, screen)
    font_setting = get_font(font_size)
    setting_y = settings_panel.y + 20
    
    # 获取当前分类的设置控件
    current_category_name = categories[current_category]["name"]
    category_controls = settings_controls.get(current_category_name, [])
    
    for setting_name, control in category_controls:
        # 创建一个包裹设置项和控件的框
        item_box_height = 80  # 设置项框的高度
        item_box = pygame.Rect(
            settings_panel.x + 10, 
            setting_y - 10, 
            settings_panel.width - 20, 
            item_box_height
        )
        
        # 绘制设置项框
        pygame.draw.rect(screen, PANEL_COLOR, item_box)
        pygame.draw.rect(screen, ACCENT_COLOR, item_box, 2, border_radius=5)
        
        # 绘制设置项标签
        setting_text = font_setting.render(f"{setting_name}:", True, TEXT_COLOR)
        screen.blit(setting_text, (settings_panel.x + 20, setting_y))
        
        # 绘制控件
        control.draw(screen)
        
        # 在设置项框内绘制分割线
        pygame.draw.line(
            screen, 
            ACCENT_COLOR, 
            (settings_panel.x + settings_panel.width * 0.5, item_box.y + 10),
            (settings_panel.x + settings_panel.width * 0.5, item_box.y + item_box.height - 10),
            2
        )
        
        setting_y += item_box_height + 20  # 移动到下一个设置项
    
    # 绘制右侧描述区域
    desc_font = get_font(get_scaled_font(INFO_FONT_SIZE, screen))
    category_name = categories[current_category]["name"]
    
    if category_name in SETTINGS_DESCRIPTIONS:
        desc_title = desc_font.render(f"{category_name}设置说明", True, ACCENT_COLOR)
        screen.blit(desc_title, (description_panel.x + 20, description_panel.y + 20))
        
        line_y = description_panel.y + 60
        for line in SETTINGS_DESCRIPTIONS[category_name]:
            desc_text = desc_font.render(line, True, TEXT_COLOR)
            screen.blit(desc_text, (description_panel.x + 20, line_y))
            line_y += 30
    
    # 绘制底部按钮
    for button in buttons:
        button.draw(screen)
    
    # 更新和渲染控制台
    console.update()
    console.render(screen)

def save_settings(user_config, button_style, settings_controls):
    """
    保存用户设置到user/user_config.json文件
    
    参数:
        user_config: 用户配置字典
        button_style: 按钮样式
        settings_controls: 设置控件字典
    """
    # 更新配置数据
    user_config["button_style"] = button_style
    
    # 确保user目录存在
    if not os.path.exists("user"):
        try:
            os.makedirs("user")
            print("已创建 user 目录")
        except Exception as e:
            print(f"创建 user 目录失败: {e}")
            return False
    
    # 写入配置文件
    config_path = os.path.join("user", "user_config.json")
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(user_config, f, indent=4, ensure_ascii=False)
        print(f"成功保存设置到: {config_path}")
        return True
    except Exception as e:
        print(f"保存设置失败: {e}")
        return False