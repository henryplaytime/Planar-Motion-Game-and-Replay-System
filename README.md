# 平面移动游戏与回放系统 (版本0.2.5)

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
```

### 2. `player.py` - 玩家角色实现

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

### 3. `game.py` - 游戏主逻辑

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

### 4. `Replay_System.py` - 回放系统

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

### 5. `console.py` - 控制台系统

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

### 6. `item.py` - 物品系统

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

### 7. `main.py` - 游戏入口

#### **专业UI系统实现**：

```python
# 全局按钮样式设置
BUTTON_STYLE = "COD"  # 默认使用COD风格

class ButtonManager:
    """管理按钮创建和样式的类"""
    @staticmethod
    def set_style(style):
        global BUTTON_STYLE
        BUTTON_STYLE = style
  
    @staticmethod
    def get_style():
        return BUTTON_STYLE
  
    @staticmethod
    def create_button(x, y, width, height, text, screen):
        return create_button(BUTTON_STYLE, x, y, width, height, text, screen)

def create_menu_buttons(screen):
    """创建主菜单按钮的函数"""
    button_width = 300
    button_height = 60
    start_y = data.SCREEN_HEIGHT * 0.4
  
    return [
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y, button_width, button_height, "开始游戏", screen),
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y + 100, button_width, button_height, "回放游戏", screen),
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y + 200, button_width, button_height, "设置", screen),
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y + 300, button_width, button_height, "退出", screen)
    ]
```

#### **设置菜单实现**：

```python
def settings_menu(screen, console):
    """
    设置菜单函数
    允许用户调整游戏设置，如按钮样式
    返回布尔值表示是否需要重新创建主菜单按钮
    """
    # 初始化
    button_width = 300
    button_height = 60
    start_y = data.SCREEN_HEIGHT * 0.4

    # 创建按钮文本
    button_style_text = f"按钮样式: {'COD风格' if ButtonManager.get_style() == 'COD' else '默认'}"
  
    # 音频
    try:
        click_sound = pygame.mixer.Sound(data.SOUND_MENU_CLICK)
        hover_sound = pygame.mixer.Sound(data.SOUND_MENU_HOVER)
    except:
        click_sound = None
        hover_sound = None
  
    # 创建按钮
    buttons = [
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y, button_width, button_height, 
                    button_style_text, screen),
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y + 100, button_width, button_height, 
                    "返回", screen)
    ]
  
    # 当前选中的选项索引
    current_selected = -1
    last_hover_index = -1
  
    # 设置菜单循环
    running = True
    style_changed = False  # 记录按钮样式是否被更改
```

### 8. `source/menu_btn_style.py` - 按钮样式库

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
      "speed_multiplier": 1.5,  # 速度倍率 (默认1.5倍)
      "duration": 5.0,          # 持续时间 (秒)
      "cooldown": 15.0          # 冷却时间 (秒)
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
│   └── item.json        # 肾上腺素物品参数
├── sounds/              # 音效资源
│   ├── UI_Sounds_Click.mp3
│   ├── UI_Sounds_Switch.mp3
│   └── UI_Sounds_Hover.mp3
├── source/              # 源码组件
│   └── menu_btn_style.py # 按钮样式库
├── Adrenaline.png       # 物品图标
├── console.py           # 控制台系统
├── data.py              # 常量与工具
├── game.py              # 游戏主逻辑
├── main.py              # 程序入口
├── player_image.png     # 玩家角色纹理
├── player.py            # 玩家角色系统
├── README.md            # 项目文档
├── Replay_System.py     # 高级回放系统
└── item.py              # 游戏物品系统
```

### 新增文件说明

**source/menu_btn_style.py**：

* 按钮样式库实现
* 包含COD风格和默认风格两种按钮
* 实现按钮工厂模式
* 提供悬停/点击动画效果
* 支持分辨率自适应

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

* **GitHub**: [henryplaytime](https://github.com/henryplaytime)
* **邮箱**: henryplaytime@outlook.com

---

## 感谢词

感谢所有参与测试的用户和贡献者，特别感谢开源社区提供的宝贵建议和支持。我们将继续努力完善这个项目！

**项目仓库**: [https://github.com/henryplaytime/Planar-Motion-Game-and-Replay-System](https://github.com/henryplaytime/Planar-Motion-Game-and-Replay-System)

**问题提交**: 请在GitHub Issues页面报告任何问题
