# 平面移动游戏与回放系统 (版本0.2.6)

## 项目名称

**平面移动游戏与回放系统**

## 项目概述

这是一个2D平面移动游戏系统，结合了物理运动模拟、游戏状态录制和回放功能。核心特点包括：

* **平滑物理移动**：基于加速度和摩擦力的物理模型
* **游戏状态录制**：以64ticks频率记录玩家位置、速度和状态
* **灵活回放系统**：支持暂停、快进、后退、变速
* **模块化架构**：清晰分离游戏逻辑、物理计算和UI渲染
* **交互式控制台**：实时执行命令和调试游戏
* **肾上腺素系统**：短时提升移动速度的特殊能力
* **UI系统**：COD风格按钮与动画反馈
* **音效反馈系统**：悬停/点击音效集成

---

## 版本历史更新

### v0.2.6(2025-08-15) - 设置系统与加载界面重构

* **重构设置界面**：
  * 优化了设置菜单的处理逻辑
  * 实现分页式设置界面（界面/音频/游戏性/控制）
  * 添加可视化设置控件（样式选择器）
* **用户保存机制集成**：
  * 实现了用户配置文件的保存功能
  * 自动创建user目录和配置文件
  * 支持按钮样式持久化保存
* **模块化重构**：
  * 将设置系统从主程序剥离为独立模块
  * 新增settings.py模块
* **数据文件增加**：
  * 在data.py中增加UI颜色、常量定义
  * 添加缩放计算工具函数
* **新增加载界面**：
  * 实现游戏加载界面
  * 加载界面会加载用户配置文件
  * 支持动画效果（线条动画/文字淡入淡出）

### v0.2.5(2025-08-09) - 代码重构

* **主要重构内容**：
  * 移除了所有硬编码的文本字符串，替换为data.py中定义的常量
  * 移除了所有硬编码的颜色值，替换为data.py中定义的颜色常量
  * 使用格式化字符串常量来统一文本格式
  * 简化了UI元素的创建，直接从data.py获取预设文本
  * 统一了字体大小的获取方式
* **新增文件夹**：
  * 新增user文件夹
  * 新增user_config.json文件，用于保存用户设置
  * 注意：功能未集成

### v0.2.4 (2025-08-06) - UI系统升级与性能优化

* **新UI系统**：
  * 新增COD风格按钮交互系统
  * 两种可切换按钮风格（COD风格/默认风格）
  * 按钮悬停/点击动画反馈
* **音效系统升级**：
  * 新增悬停、点击、切换三种音效
  * 悬停和点击音效应用到所有按钮
* **设置界面增强**：
  * 新增按钮风格切换功能
  * 新增设置按钮和界面
* **文件结构调整**：
  * 新增source文件夹
  * 新增menu_btn_style.py按钮样式库
* **代码优化**：
  * 优化main.py、console.py、data.py等核心模块
* **功能性调整**：
  * 移除1、2、3键快捷操作，改用鼠标操作
  * 保留ESC按键退出、~(`)按键切换控制台

### v0.2.3 (2025-07-26) - 肾上腺素系统与控制台增强

* **肾上腺素效果集成**：
  * 完全集成肾上腺素效果系统
  * 添加肾上腺素激活视觉反馈（红色粒子效果）
  * 肾上腺素参数可在item.json中配置
* **控制台改进**：
  * 控制台高度可通过 `data.CONSOLE_HEIGHT`参数配置
  * 优化控制台显示效果
  * 修复控制台滚动问题
* **命令系统更新**：
  * 重新启用 `give`命令
  * 新增 `replay`命令（强制播放指定回放文件）
* **代码重构**：
  * 优化Replay_System.py架构
  * 优化game.py架构

### v0.2.2 (2025-07-23) - 框架重置与控制台优化

* **框架重置**：对整个框架进行了大幅度重构，提高代码可维护性
* **控制台调整**：移除了控制台可拖拽调整大小的能力，控制台高度固定为250像素
* **稳定性增强**：优化了控制台渲染逻辑，减少资源消耗

### v0.2.1 (2025-07-22) - 控制台优化补丁

* 修复了控制台拖拽卡死问题
* 添加了表面创建频率限制（1秒内最多创建1次）

### v0.2.0 (2025-07-21) - 控制台与回放系统增强

* 新增交互式控制台系统
* 回放系统增加高阶指令（90%）+原始输入（5%）+状态快照（5%）的数据格式
* 添加物品系统框架
* 录制系统优化（版本2格式）
* UI和交互优化

---

## 项目的整体架构详细说明

### 1. `data.py` - 游戏常量与工具函数

#### **核心功能**：

* 定义屏幕尺寸、颜色、物理参数等全局常量
* 提供加载玩家图像、获取字体等工具函数
* 屏幕坐标和尺寸缩放工具

#### **关键属性**：

```python
# 物理参数（可修改）
WALK_SPEED = 250.0  # 基础移动速度
SPRINT_SPEED = 320.0  # 冲刺移动速度
ACCELERATION = 20.0  # 加速度系数
FRICTION = 5.0  # 地面摩擦力系数
RECORD_FPS = 64  # 录制采样率

# 控制台高度配置
CONSOLE_HEIGHT = 400  # 控制台默认高度

# 颜色定义
BACKGROUND = (30, 30, 50)  # 背景色
TEXT_COLOR = (220, 220, 255)  # 文本颜色
ADRENALINE_COLOR = (255, 50, 50, 180)  # 肾上腺素效果色

# 使命召唤风格UI颜色
BUTTON_IDLE = (30, 40, 50)  # 深灰蓝色
BUTTON_HOVER = (50, 70, 90)  # 浅灰蓝色
BUTTON_ACTIVE = (180, 150, 20)  # COD标志性琥珀色
ACCENT_COLOR = (180, 150, 20)  # 琥珀色高亮
GLOW_COLOR = (180, 150, 20, 100)  # 半透明琥珀色光晕
CONFIRM_BG = (10, 15, 20, 220)  # 半透明确认背景

# === UI 常量 ===
UI_PADDING = 15  # UI元素内边距
UI_LINE_SPACING = 25  # UI行间距
UI_PANEL_ALPHA = 180  # UI面板透明度
ITEM_SLOT_SIZE = 60  # 物品槽尺寸
ITEM_SLOT_MARGIN = 20  # 物品槽外边距

# === 菜单界面常量 ===
# 主菜单按钮设置
MENU_BUTTON_WIDTH = 300
MENU_BUTTON_HEIGHT = 60
MENU_BUTTON_START_Y_RATIO = 0.4  # 起始Y位置（屏幕高度的比例）
MENU_BUTTON_SPACING = 100  # 按钮之间的垂直间距
MENU_TITLE_Y_RATIO = 0.2  # 标题的Y位置（屏幕高度的比例）
MENU_TITLE_LINE_Y_RATIO = 0.25  # 标题下方装饰线的Y位置（屏幕高度的比例）
MENU_INFO_BOTTOM_MARGIN = 50  # 说明文字距离屏幕底部的距离

# 按钮文本
BUTTON_TEXT_START = "开始游戏"
BUTTON_TEXT_REPLAY = "回放游戏"
BUTTON_TEXT_SETTINGS = "设置"
BUTTON_TEXT_EXIT = "退出"
BUTTON_TEXT_BACK = "返回"
BUTTON_TEXT_STYLE_FORMAT = "按钮样式: {}"  # 格式化字符串用于按钮样式文本

# 菜单标题文本
MAIN_MENU_TITLE = "游戏主菜单"
SETTINGS_MENU_TITLE = "设置"

# 信息文本
MAIN_MENU_INFO = "点击按钮选择功能 | 按ESC键退出 | ~键打开控制台"
SETTINGS_MENU_INFO = "按ESC键返回主菜单"

# 样式名称映射
STYLE_NAMES = {
    "COD": "COD风格",
    "Default": "默认"
}
```

#### **工具函数**：

```python
def get_scaled_button_rect(button, screen):
    """
    获取按钮的缩放后矩形区域
  
    参数:
        button: 按钮对象
        screen: 当前屏幕Surface对象
  
    返回:
        pygame.Rect: 缩放后的按钮矩形
    """
    # 获取按钮原始矩形
    original_rect = button.rect
  
    # 计算缩放比例
    width_ratio = screen.get_width() / BASE_WIDTH
    height_ratio = screen.get_height() / BASE_HEIGHT
  
    # 计算缩放后的位置和尺寸
    x = original_rect.x * width_ratio
    y = original_rect.y * height_ratio
    width = original_rect.width * width_ratio
    height = original_rect.height * height_ratio
  
    return pygame.Rect(x, y, width, height)

def scale_value(value, screen, is_width=True):
    """
    缩放数值(基于基准分辨率)
    """
    if is_width:
        return value * (screen.get_width() / BASE_WIDTH)
    return value * (screen.get_height() / BASE_HEIGHT)

def get_scaled_font(base_size, screen, min_size=12):
    """
    获取缩放后的字体大小
    """
    width_scale = screen.get_width() / BASE_WIDTH
    height_scale = screen.get_height() / BASE_HEIGHT
    scale = min(width_scale, height_scale)
    scaled_size = int(base_size * scale)
    return max(scaled_size, min_size)
```

### 2. `settings.py` - 设置模块

#### **核心功能**：

* 实现分页式设置界面（界面/音频/游戏性/控制）
* 提供样式选择器等可视化控件
* 管理用户配置的保存与加载

#### **设置选择器实现**：

```python
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
```

#### **设置保存功能**：

```python
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
```

### 3. `source/main_loading_menu.py` - 加载菜单

#### **核心功能**：

* 实现游戏加载界面
* 加载用户配置文件
* 提供动画效果（线条动画/淡入淡出）

#### **关键实现**：

```python
def show_loading_menu():
    """
    显示加载菜单界面，当用户按下空格键或回车键时退出
    返回加载的用户配置字典
    """
    # 使用data.py中的默认配置
    config = DEFAULT_MENU_CONFIG
  
    # 加载用户配置文件
    user_config = load_user_config()
  
    # 初始化pygame
    pygame.init()
    screen = pygame.display.set_mode(config["window"]["size"], pygame.RESIZABLE)
    pygame.display.set_caption(config["window"]["title"])
    screen_width, screen_height = screen.get_size()
  
    # 设置标题文本
    title_text = None
    title_rect = None
    if config["title"]["enabled"]:
        title_cfg = config["title"]
        font = load_font(title_cfg["font_path"], title_cfg["font_size"])
        title_text = font.render(title_cfg["text"], True, title_cfg["color"])
        title_x = int(title_cfg["position"][0] * screen_width)
        title_y = int(title_cfg["position"][1] * screen_height)
        title_rect = title_text.get_rect(center=(title_x, title_y))
  
    # 设置提示文本
    prompt_text = None
    prompt_rect = None
    if config["prompt"]["enabled"]:
        prompt_cfg = config["prompt"]
        font = load_font(prompt_cfg["font_path"], prompt_cfg["font_size"])
        prompt_text = font.render(prompt_cfg["text"], True, prompt_cfg["color"])
        prompt_x = int(prompt_cfg["position"][0] * screen_width)
        prompt_y = int(prompt_cfg["position"][1] * screen_height)
        prompt_rect = prompt_text.get_rect(center=(prompt_x, prompt_y))
  
    # 初始化音频系统
    if config["music"]["enabled"] and pygame.mixer.get_init() is None:
        pygame.mixer.init()
  
    # 播放背景音乐
    if config["music"]["enabled"]:
        try:
            pygame.mixer.music.load(config["music"]["path"])
            pygame.mixer.music.play(-1)  # 循环播放
            pygame.mixer.music.set_volume(config["music"]["volume"])
        except pygame.error as e:
            print(f"音乐播放失败: {e}")
  
    # 初始化动画计时器
    line_start_time = pygame.time.get_ticks()
  
    # 初始化淡入淡出参数
    fade_alpha = config["fade"]["initial_alpha"]
    fade_in = True
  
    # 主循环
    clock = pygame.time.Clock()
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - line_start_time
  
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    # 按空格键或回车键退出
                    running = False
  
        # 清屏
        screen.fill(config["window"]["background_color"])
  
        # 绘制标题
        if title_text and title_rect:
            screen.blit(title_text, title_rect)
  
        # 绘制动画线条
        if config["animation_lines"]["enabled"]:
            draw_animation_lines(screen, elapsed, config)
  
        # 绘制提示文本
        if prompt_text and prompt_rect:
            if config["fade"]["enabled"]:
                fade_alpha, fade_in = update_fade(fade_alpha, fade_in, elapsed, config)
                prompt_text.set_alpha(fade_alpha)
            screen.blit(prompt_text, prompt_rect)
  
        pygame.display.flip()
        clock.tick(config["game"]["fps"])
  
    # 清理资源
    if pygame.mixer.get_init() and config["music"]["enabled"]:
        pygame.mixer.music.stop()
    pygame.quit()
  
    # 返回加载的用户配置
    return user_config
```

### 4. `player.py` - 玩家角色实现

#### **核心功能**：

* 实现基于物理的角色移动系统
* 处理碰撞检测和边界限制
* 管理玩家状态（位置、速度、冲刺状态）
* 肾上腺素效果激活与冷却管理

#### **关键属性与方法**：

```python
class Player:
    def __init__(self):
        self.position = [SCREEN_WIDTH/2, SCREEN_HEIGHT/2]  # 初始位置
        self.velocity = [0.0, 0.0]  # 速度向量
        self.sprinting = False  # 冲刺状态
        self.grounded = True  # 地面状态
        self.adrenaline_active = False  # 肾上腺素激活状态
        self.adrenaline_active_end = 0.0  # 激活结束时间
        self.adrenaline_cooldown_end = 0.0  # 冷却结束时间
        self.speed_multiplier = 1.0  # 速度倍率
  
    def update(self, pressed_keys, delta_time):
        # 物理移动系统实现（包含肾上腺素效果）
  
    def activate_adrenaline(self, duration, cooldown, speed_multiplier):
        # 激活肾上腺素效果
        current_time = pygame.time.get_ticks() / 1000.0
        # 检查冷却状态
        if current_time < self.adrenaline_cooldown_end:
            return False
        # 激活效果
        self.adrenaline_active = True
        self.adrenaline_active_end = current_time + duration
        self.adrenaline_cooldown_end = current_time + cooldown
        self.speed_multiplier = speed_multiplier
        return True
```

#### **肾上腺素集成物理系统**：

```python
def update(self, pressed_keys, delta_time):
    # 更新肾上腺素状态
    current_time = pygame.time.get_ticks() / 1000.0
    if self.adrenaline_active and current_time >= self.adrenaline_active_end:
        self.adrenaline_active = False
        self.speed_multiplier = 1.0
  
    # 1. 确定最大速度（考虑肾上腺素倍率）
    base_speed = data.SPRINT_SPEED if self.sprinting else data.WALK_SPEED
    max_speed = base_speed * self.speed_multiplier
    ...
```

### 5. `game.py` - 游戏主逻辑

#### **核心功能**：

* 管理游戏主循环（update/render）
* 处理游戏事件（键盘/窗口大小）
* 实现录制系统（开始/停止录制）
* 协调玩家、控制台和录制系统
* 肾上腺素效果集成

#### **肾上腺素效果激活**：

```python
def update(self):
    ...
    # 处理肾上腺素激活
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
    ...
```

#### **录制系统更新（记录肾上腺素状态）**：

```python
def record_frame(self, player, pressed_keys):
    ...
    # 记录状态快照（包含肾上腺素状态）
    if current_time - self.last_snapshot_time >= snapshot_interval:
        self.record_file.write(
            f"S:{current_time:.3f},"
            f"{player.position[0]:.3f},{player.position[1]:.3f},"
            f"{player.velocity[0]:.3f},{player.velocity[1]:.3f},"
            f"{int(player.sprinting)},"
            f"{int(player.adrenaline_active)}\n"  # 记录肾上腺素状态
        )
        self.last_snapshot_time = current_time
```

### 6. `Replay_System.py` - 回放系统

#### **肾上腺素回放效果实现**：

```python
def apply_interpolated_snapshot(self):
    ...
    # 处理肾上腺素激活
    adrenaline = prev.adrenaline if blend < 0.5 else next.adrenaline
    if adrenaline and not self.adrenaline_active:
        self._activate_adrenaline_effect()  # 激活粒子效果
    self.adrenaline_active = adrenaline
    ...
  
def _activate_adrenaline_effect(self):
    """激活肾上腺素特效(创建粒子)"""
    self.adrenaline_particles = []
    for _ in range(20):
        self._create_adrenaline_particle()
  
def _create_adrenaline_particle(self):
    """创建单个肾上腺素粒子"""
    angle = random.uniform(0, 2 * math.pi)
    speed = random.uniform(50, 200)
    size = random.uniform(3, 10)
    self.adrenaline_particles.append({
        'pos': list(self.player.position),  # 初始位置为玩家位置
        'vel': [math.cos(angle) * speed, math.sin(angle) * speed],  # 速度向量
        'size': size,  # 粒子大小
        'life': 1.0,  # 当前生命周期
        'max_life': random.uniform(0.3, 0.8)  # 最大生命周期
    })
```

### 7. `console.py` - 控制台系统

#### **replay命令实现**：

```python
def _cmd_replay(self, args, game=None):
    """
    强制读取并播放指定的回放文件命令
  
    参数:
    - args: 命令参数列表
    - game: 游戏实例
    """
    if not game or not hasattr(game, 'force_replay'):
        self.add_output("错误: 未连接到游戏实例或游戏不支持强制回放功能")
        return
  
    if not args:
        # 如果没有提供文件名，列出所有可用回放文件
        replay_files = glob.glob("*.dem")
        if not replay_files:
            self.add_output("没有找到回放文件")
            return
  
        self.add_output("可用回放文件:")
        for i, file in enumerate(replay_files):
            self.add_output(f"  {i+1}. {file}")
        self.add_output("使用: replay [文件名 或 编号]")
        return
  
    # 尝试将参数解释为索引或文件名
    replay_files = glob.glob("*.dem")
    file_arg = args[0].strip()
  
    # 检查是否是数字索引
    if file_arg.isdigit():
        index = int(file_arg) - 1
        if 0 <= index < len(replay_files):
            filename = replay_files[index]
        else:
            self.add_output(f"错误: 无效的索引 {file_arg}，可用索引范围 1-{len(replay_files)}")
            return
    else:
        # 直接使用文件名
        filename = file_arg
        # 确保文件扩展名正确
        if not filename.endswith(".dem"):
            filename += ".dem"
  
        # 检查文件是否存在
        if not os.path.exists(filename):
            self.add_output(f"错误: 文件 '{filename}' 不存在")
            return
  
    # 调用游戏实例的强制回放方法
    try:
        game.force_replay(filename)
        self.add_output(f"正在强制播放回放文件: {filename}")
        self.add_output("关闭控制台后回放将开始...")
    except Exception as e:
        self.add_output(f"播放回放失败: {str(e)}")
```

#### **控制台高度配置**：

```python
class Console:
    def __init__(self, game_instance=None):
        ...
        self.ui.console_height = data.CONSOLE_HEIGHT  # 使用配置的高度
```

### 8. `item.py` - 物品系统

#### **肾上腺素物品实现**：

```python
class AdrenalineItem(Item):
    """
    肾上腺素物品类
  
    功能概述:
    1. 实现肾上腺素物品的具体效果
    2. 管理物品的激活和冷却
    """
  
    def __init__(self):
        """初始化肾上腺素物品"""
        super().__init__("adrenaline")
  
    def use(self, player):
        """
        使用肾上腺素物品
  
        返回:
        - bool: 使用是否成功
        """
        # 获取配置
        effects = self.config.get("effects", {})
        duration = effects.get("duration", 5.0)
        cooldown = effects.get("cooldown", 15.0)
        speed_multiplier = effects.get("speed_multiplier", 1.5)
  
        # 激活肾上腺素效果
        return player.activate_adrenaline(duration, cooldown, speed_multiplier)
```

### 9. `main.py` - 游戏入口

#### **专业UI系统实现**：

```python
def main_menu(user_config):
    """
    游戏主菜单函数 - 只保留ESC键和~键功能

    参数:
        user_config (dict): 加载的用户配置
    """
    # 从配置中获取按钮样式
    button_style = user_config.get("button_style", "COD")
  
    print(f"主菜单使用的按钮样式: {button_style}")

    # 初始化Pygame
    screen = init_pygame()
    pygame.display.set_caption(data.MAIN_MENU_TITLE)

    # 初始化音频系统
    pygame.mixer.init()
    try:
        click_sound = pygame.mixer.Sound(data.SOUND_MENU_CLICK)
        hover_sound = pygame.mixer.Sound(data.SOUND_MENU_HOVER)
    except Exception as e:
        print(f"无法加载音效: {e}")
        click_sound = None
        hover_sound = None
  
    # 创建控制台对象
    console = Console()
  
    # 使用配置中的样式创建按钮
    buttons = create_menu_buttons(screen, button_style)
  
    # 当前选中的选项索引（基于鼠标悬停）
    current_selected = -1
    last_hover_index = -1
  
    # 主菜单循环
    running = True
    while running:
        # 获取当前鼠标位置
        mouse_pos = pygame.mouse.get_pos()
  
        # 处理所有事件
        for event in pygame.event.get():
            # ===== 1. 处理窗口事件 =====
            if event.type == pygame.QUIT:
                running = False
      
            # 窗口大小调整事件
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                # 重新创建按钮以适应新尺寸
                buttons = create_menu_buttons(screen, button_style)
      
            # ===== 2. 处理键盘事件 =====
            elif event.type == pygame.KEYDOWN:
                # 2.1 只保留控制台切换键（反引号键）
                if event.key == pygame.K_BACKQUOTE:
                    console.toggle()
                    continue
          
                # 2.2 只保留控制台事件处理
                if console.handle_event(event):
                    continue
          
                # 2.3 只保留ESC键退出功能
                elif event.key == pygame.K_ESCAPE:
                    running = False
      
            # ===== 3. 处理鼠标事件 =====
            # 3.1 鼠标移动事件
            elif event.type == pygame.MOUSEMOTION:
                # 更新鼠标位置
                mouse_pos = event.pos
          
                # 检查鼠标悬停状态
                found_hover = False
                for i, button in enumerate(buttons):
                    # 获取按钮缩放后的矩形
                    scaled_rect = get_scaled_button_rect(button)
              
                    # 检查鼠标是否悬停在按钮上
                    if scaled_rect.collidepoint(mouse_pos):
                        # 更新当前选择
                        current_selected = i
                  
                        # 如果切换到新按钮，播放悬停音效
                        if i != last_hover_index and hover_sound:
                            hover_sound.play()
                        last_hover_index = i
                        found_hover = True
                        break
          
                # 如果没有按钮被悬停
                if not found_hover:
                    current_selected = -1
                    last_hover_index = -1
      
            # 3.2 鼠标点击事件
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 左键点击
                if event.button == 1:
                    # 检查点击了哪个按钮
                    for i, button in enumerate(buttons):
                        scaled_rect = get_scaled_button_rect(button)
                  
                        # 如果点击在当前按钮上
                        if scaled_rect.collidepoint(event.pos):
                            if click_sound:
                                click_sound.play()
                      
                            # 设置按钮点击状态
                            button.state = "active"
                      
                            # 立即绘制一次动画状态
                            screen.fill(data.BACKGROUND)
                            title_font_size = data.get_scaled_font(data.MENU_TITLE_FONT_SIZE, screen)
                            font_title = data.get_font(title_font_size)
                            title = font_title.render(data.MAIN_MENU_TITLE, True, data.TEXT_COLOR)
                            title_pos = (
                                screen.get_width() // 2 - title.get_width() // 2,
                                data.scale_value(screen.get_height() * data.MENU_TITLE_Y_RATIO, screen, False)
                            )
                            line_y = data.scale_value(screen.get_height() * data.MENU_TITLE_LINE_Y_RATIO, screen, False)
                            draw_buttons(screen, buttons, title_pos, line_y)
                            pygame.display.flip()
                            pygame.time.delay(data.BUTTON_CLICK_ANIMATION_DELAY)  # 短暂延迟让动画可见
                      
                            # 处理菜单选择
                            result = handle_menu_selection(button.text, screen, console, button_style)
                            recreate_buttons, new_style = result
                  
                            # 更新按钮样式
                            if new_style != button_style:
                                button_style = new_style
                                user_config["button_style"] = new_style
                                print(f"按钮样式已更新为: {button_style}")
                  
                            # 重新创建按钮
                            if recreate_buttons:
                                buttons = create_menu_buttons(screen, button_style)
                            break
```

### 10. `source/menu_btn_style.py` - 按钮样式库

#### **专业按钮系统实现**：

```python
class CODButton:
    def __init__(self, x, y, width, height, text, screen):
        # COD风格按钮初始化
        self.rect = pygame.Rect(x, y, width, height)
        self.base_rect = pygame.Rect(x, y, width, height)
        self.current_rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.state = "idle"
        self.glow_alpha = 0
        self.pulse_direction = 1
        self.anim_progress = 0
        self.anim_direction = 0
        self.screen = screen
  
    def draw(self, surface):
        # 绘制COD风格按钮
        # ... [完整实现]

class DefaultButton:
    def __init__(self, x, y, width, height, text, screen):
        # 默认风格按钮初始化
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.state = "idle"
        self.screen = screen
  
    def draw(self, surface):
        # 绘制默认风格按钮
        # ... [完整实现]

# 按钮工厂函数
def create_button(style, x, y, width, height, text, screen):
    if style == "COD":
        return CODButton(x, y, width, height, text, screen)
    else:
        return DefaultButton(x, y, width, height, text, screen)
```

---

## 肾上腺素系统配置说明

### 肾上腺素效果参数可通过 `config/item.json`文件配置：

```json
{
  "adrenaline": {
    "name": "肾上腺素",
    "description": "注射后短时间内大幅提升移动速度",
    "effects": {
      "speed_multiplier": 1.5,  
      "duration": 5.0,  
      "cooldown": 15.0    
    }
  }
}
```

### **使用方法**：

1. 游戏中按 `Q`键激活肾上腺素效果
2. 控制台使用 `give adrenaline`命令直接获得效果
3. 效果激活期间显示红色粒子特效

---

## 控制台命令更新

| 命令   | 参数          | 功能                 | 例子             |
| ------ | ------------- | -------------------- | ---------------- |
| give   | adrenaline    | 给予玩家肾上腺素效果 | give adrenaline  |
| replay | [文件名/编号] | 强制播放指定回放文件 | replay demo1.dem |
| help   | 无            | 显示所有可用命令     | help             |
| clear  | 无            | 清除控制台输出       | clear            |
| exit   | 无            | 关闭控制台           | exit             |
| time   | 无            | 显示游戏运行时间     | time             |
| fps    | 无            | 显示当前帧率         | fps              |
| pos    | 无            | 显示玩家坐标         | pos              |
| speed  | [数值]        | 设置玩家移动速度     | speed 260        |
| record | 无            | 开始/停止录制        | record           |
| show   | 无            | 显示/隐藏检测面板    | show             |

---

## 项目文件结构说明

```
平面移动游戏与回放系统/
├── config/              # 配置文件
│   └└── item.json        # 肾上腺素物品参数
├── user/               # 用户配置文件
│   └└── user_config.json  # 用户设置文件
├── sounds/             # 音效资源
│   ├── UI_Sounds_Click.mp3
│   ├── UI_Sounds_Switch.mp3
│   └└── UI_Sounds_Hover.mp3
├── source/             # 源码组件
│   ├── main_loading_menu.py # 加载菜单实现
│   └└── menu_btn_style.py   # 按钮样式库
├── Adrenaline.png      # 物品图标
├── console.py          # 控制台系统
├── data.py             # 常量与工具
├── game.py             # 游戏主逻辑
├── main.py             # 程序入口
├── player_image.png    # 玩家角色纹理
├── player.py           # 玩家角色系统
├── README.md           # 项目文档
├── Replay_System.py    # 高级回放系统
├── item.py             # 游戏物品系统
└└── settings.py         # 设置模块
```

### 新增文件说明

**settings.py**：

* 设置菜单系统实现
* 分页式设置界面（界面/音频/游戏性/控制）
* 可视化设置控件（样式选择器）
* 配置保存/加载机制

**source/main_loading_menu.py**：

* 游戏加载界面实现
* 加载用户配置文件
* 支持动画效果（线条动画/淡入淡出）
* 响应式设计

---

## 项目扩展建议

1. **修改物理参数**：调整加速度、摩擦力等获得不同手感
2. **添加游戏元素**：实现障碍物、收集物等游戏对象
3. **扩展物品系统**：添加新物品类型（如药水）
4. **网络功能扩展**：添加多人游戏支持
5. **肾上腺素视觉增强**：添加屏幕特效和角色视觉效果
6. **音效管理系统**：添加音效设置界面
7. **更多UI风格**：增加额外的按钮风格选项

---

## 项目作者的联系方式

* **GitHub**: [https://github.com/henryplaytime](https://github.com/henryplaytime)
* **邮箱**: [henryplaytime@outlook.com](mailto:henryplaytime@outlook.com)

---

## 感谢词

感谢所有参与测试的用户和贡献者，特别感谢开源社区提供的宝贵建议和支持。我们将继续努力完善这个项目！

**项目仓库**: [https://github.com/henryplaytime/Planar-Motion-Game-and-Replay-System](https://github.com/henryplaytime/Planar-Motion-Game-and-Replay-System)

**问题提交**: 请在GitHub Issues页面报告任何问题
