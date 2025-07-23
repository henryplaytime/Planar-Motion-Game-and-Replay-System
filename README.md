
# 平面移动游戏与回放系统 (版本0.2.2)

## 项目名称

**平面移动游戏与回放系统**

## 项目概述

这是一个2D平面移动游戏系统，结合了物理运动模拟、游戏状态录制和回放功能。核心特点包括：

* **平滑物理移动**：基于加速度和摩擦力的物理模型
* **游戏状态录制**：以64ticks频率记录玩家位置、速度和状态
* **灵活回放系统**：支持暂停、快进、后退、变速和精确跳转
* **模块化架构**：清晰分离游戏逻辑、物理计算和UI渲染
* **交互式控制台**：实时执行命令和调试游戏

---

## 版本历史更新

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

**核心功能**：

* 定义屏幕尺寸、颜色、物理参数等全局常量
* 提供加载玩家图像、获取字体等工具函数
* 屏幕坐标和尺寸缩放工具

**关键属性**：

```python
# 物理参数（可修改）
WALK_SPEED = 250.0  # 基础移动速度
SPRINT_SPEED = 320.0  # 冲刺移动速度
ACCELERATION = 20.0  # 加速度系数
FRICTION = 5.0  # 地面摩擦力系数
RECORD_FPS = 8  # 录制采样率

# 颜色定义
BACKGROUND = (30, 30, 50)  # 背景色
TEXT_COLOR = (220, 220, 255)  # 文本颜色
ADRENALINE_COLOR = (255, 50, 50, 180)  # 肾上腺素效果色
```

### 2. `player.py` - 玩家角色实现

**核心功能**：

* 实现基于物理的角色移动系统
* 处理碰撞检测和边界限制
* 管理玩家状态（位置、速度、冲刺状态）

**关键属性与方法**：

```python
class Player:
    def __init__(self):
        self.position = [SCREEN_WIDTH/2, SCREEN_HEIGHT/2]  # 初始位置
        self.velocity = [0.0, 0.0]  # 速度向量
        self.sprinting = False  # 冲刺状态
        self.grounded = True  # 地面状态
      
    def update(self, pressed_keys, delta_time):
        # 物理移动系统实现（见下方详解）
  
    def check_bounds(self):
        # 防止玩家移出屏幕边界
```

**物理系统详解**：

```python
def update(self, pressed_keys, delta_time):
    # 1. 确定最大速度（行走或冲刺）
    max_speed = data.SPRINT_SPEED if self.sprinting else data.WALK_SPEED
  
    # 2. 计算期望方向向量
    wish_dir = [0.0, 0.0]
    if pressed_keys[pygame.K_w]: wish_dir[1] -= 1
    if pressed_keys[pygame.K_s]: wish_dir[1] += 1
    # ...其他方向处理
  
    # 3. 归一化方向向量
    wish_length = (wish_dir[0]**2 + wish_dir[1]**2)**0.5
    if wish_length > 0:
        wish_dir[0] /= wish_length
        wish_dir[1] /= wish_length
  
    # 4. 计算速度投影
    current_speed = self.velocity[0]*wish_dir[0] + self.velocity[1]*wish_dir[1]
  
    # 5. 应用加速度
    add_speed = max_speed - current_speed
    if add_speed > 0:
        accel_speed = min(data.ACCELERATION * max_speed * delta_time, add_speed)
        self.velocity[0] += accel_speed * wish_dir[0]
        self.velocity[1] += accel_speed * wish_dir[1]
  
    # 6. 应用摩擦力
    speed = (self.velocity[0]**2 + self.velocity[1]**2)**0.5
    if speed > 0:
        drop = speed * data.FRICTION * delta_time
        new_speed = max(speed - drop, 0)
        self.velocity[0] *= new_speed / speed
        self.velocity[1] *= new_speed / speed
```

### 3. `game.py` - 游戏主逻辑

**核心功能**：

* 管理游戏主循环（update/render）
* 处理游戏事件（键盘/窗口大小）
* 实现录制系统（开始/停止录制）
* 协调玩家、控制台和录制系统

**关键属性与方法**：

```python
class Game:
    def __init__(self, screen):
        self.running = True  # 游戏运行状态
        self.recording = False  # 录制状态
        self.record_file = None  # 录制文件对象
        self.player = Player()  # 玩家实例
        self.console = console.Console(self)  # 控制台实例
      
    def start_recording(self):
        # 开始录制实现（见下方详解）
      
    def stop_recording(self):
        # 停止录制
      
    def run(self):
        # 游戏主循环
```

**录制系统详解**：

```python
def start_recording(self):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"game_recording_{timestamp}.dem"
    self.record_file = open(filename, 'w')
  
    # 写入文件头信息
    self.record_file.write(f"VERSION: {data.RECORD_VERSION}\n")
    self.record_file.write(f"SCREEN_WIDTH: {data.SCREEN_WIDTH}\n")
    self.record_file.write(f"SCREEN_HEIGHT: {data.SCREEN_HEIGHT}\n")
    self.record_file.write(f"RECORD_FPS: {data.RECORD_FPS}\n")
    self.record_file.write(f"START_TIME: {time.time()}\n")
```

### 4. `Replay_System.py` - 回放系统

**核心功能**：

* 加载和解析录制文件
* 实现回放控制（播放/暂停/快进/后退）
* 应用插值快照实现平滑回放
* 渲染回放UI界面

**关键类与方法**：

```python
class GameReplayer:
    def __init__(self, filename, screen):
        self.filename = filename  # 回放文件名
        self.state = ReplayState.PLAYING  # 回放状态
        self.playback_speed = 1.0  # 回放速度
        self.current_time = 0.0  # 当前回放时间
      
    def load_recording(self):
        # 加载录制文件
      
    def update(self, delta_time):
        # 更新回放状态
      
    def draw_ui(self, screen):
        # 渲染回放UI
```

**回放控制功能**：

| 按键 | 功能      | 实现方式                            |
| ---- | --------- | ----------------------------------- |
| 空格 | 播放/暂停 | 切换PLAYING/PAUSED状态              |
| →   | 快进      | 设置为FAST_FORWARD状态              |
| ←   | 后退      | 设置为REWIND状态                    |
| ↑   | 加速      | `playback_speed += 0.5`(最大5.0)  |
| ↓   | 减速      | `playback_speed -= 0.5`(最小0.1)  |
| J    | 跳转      | 输入目标时间并设置 `current_time` |
| ESC  | 退出      | 结束回放循环                        |

### 5. `console.py` - 控制台系统

**核心功能**：

* 实现游戏内控制台功能
* 支持命令输入、历史记录和自动补全
* 管理命令注册和执行
* 渲染控制台界面

**关键类与属性**：

```python
class Console:
    def __init__(self, game_instance=None):
        self.state = ConsoleState.CLOSED  # 控制台状态
        self.core = ConsoleCore()  # 控制台逻辑核心
        self.ui = ConsoleUI()  # 控制台UI渲染
        self.game = game_instance  # 关联的游戏实例
      
    def toggle(self):
        # 切换控制台打开/关闭状态
      
    def handle_event(self, event):
        # 处理控制台输入事件
```

**控制台命令示例**：

| 命令   | 参数   | 功能              | 例子      |
| ------ | ------ | ----------------- | --------- |
| help   | 无     | 显示所有可用命令  | help      |
| clear  | 无     | 清除控制台输出    | clear     |
| exit   | 无     | 关闭控制台        | exit      |
| time   | 无     | 显示游戏运行时间  | time      |
| fps    | 无     | 显示当前帧率      | fps       |
| pos    | 无     | 显示玩家坐标      | pos       |
| speed  | [数值] | 设置玩家移动速度  | speed 260 |
| record | 无     | 开始/停止录制     | record    |
| show   | 无     | 显示/隐藏检测面板 | show      |

### 6. `items.py` - 物品系统

**核心功能**：

* 管理游戏物品系统
* 加载物品配置（JSON文件）
* 实现物品使用逻辑

**关键类与方法**：

```python
class Item:
    def __init__(self, item_id):
        self.id = item_id  # 物品ID
        self.config = self._load_config(item_id)  # 物品配置
      
    def use(self, player):
        # 使用物品（抽象方法）
      
class AdrenalineItem(Item):
    def use(self, player):
        # 肾上腺素物品的具体实现
```

**物品配置示例**：

```json
{
  "adrenaline": {
    "name": "肾上腺素",
    "description": "短时间内大幅提升移动速度",
    "image_path": "assets/adrenaline.png",
    "duration": 10.0,
    "cooldown": 30.0,
    "speed_multiplier": 1.8
  }
}
```

### 7. `main.py` - 游戏入口

**核心功能**：

* 游戏启动入口
* 显示主菜单界面
* 处理游戏模式选择（开始游戏/回放游戏/退出）

**关键方法**：

```python
def main_menu():
    # 初始化Pygame和屏幕
    # 显示主菜单选项
    # 处理用户选择
  
    # 菜单选项：
    # - 开始游戏: 进入游戏主循环
    # - 回放游戏: 进入回放模式
    # - 退出: 退出游戏
```

---

## 项目扩展建议

1. **添加跳跃功能**：扩展物理系统支持垂直移动
2. **修改物理参数**：调整加速度、摩擦力等获得不同手感
3. **添加游戏元素**：实现障碍物、收集物等游戏对象
4. **扩展物品系统**：添加新物品类型（如生命药水）
5. **网络功能扩展**：添加多人游戏支持

---

## 项目作者的联系方式

* **GitHub**: [henryplaytime](https://github.com/henryplaytime)
* **邮箱**: henryplaytime@outlook.com

---

## 感谢词

感谢所有参与测试的用户和贡献者，特别感谢开源社区提供的宝贵建议和支持。我将继续努力完善这个项目！

**项目仓库**: [https://github.com/henryplaytime/Planar-Motion-Game-and-Replay-System](https://github.com/henryplaytime/Planar-Motion-Game-and-Replay-System)

**问题提交**: 请在GitHub Issues页面报告任何问题
