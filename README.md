# 平面移动游戏与回放系统 (版本 0.3.0)

## 项目名称

**平面移动游戏与回放系统**

## 项目概述

这是一个 2D 平面移动游戏系统，结合了物理运动模拟、游戏状态录制和回放功能。

v0.3.0 起，项目引入 **AppLoop + Scene** 架构，主循环、状态管理、场景职责被彻底从具体逻辑中抽离。

核心特点包括：

* **AppLoop 唯一主循环**：所有场景（主菜单 / 游戏 / 回放 / 设置）走同一条分发路径
* **全局状态机**：`AppState` + 场景内子状态（暂停 / 回放快进 / 设置分类）
* **集中式 ESC 语义**：`KeyRouter` 统一决定 ESC 在不同状态下的含义
* **平滑物理移动**：基于加速度和摩擦力的物理模型
* **回放 3.0 格式**：实体注册段 + 高阶命令（90%）+ 原始输入（5%）+ 状态快照（5%）
* **多实体预留**：eid 派发机制，NPC 无痛接入
* **灵活回放系统**：支持暂停、快进、后退、变速
* **交互式控制台**：实时执行命令和调试游戏
* **肾上腺素系统**：短时提升移动速度的特殊能力
* **模块化 UI**：特殊风格按钮、动画反馈、悬停/点击音效
* **共享层设计**：录制与回放共用同一份格式定义和玩家渲染

---

## 项目结构

```
Planar-Motion-Game-and-Replay-System/
├─ core/                          # 状态与主循环（与具体玩法无关）
│  ├─ state.py                    # AppState / GameSubState / ReplaySubState / SettingsSubState
│  ├─ app_loop.py                 # 唯一主循环：事件分发 / update / render / flip
│  └─ key_router.py               # 集中式 ESC 语义分发
│
├─ scenes/                        # 场景层（不拥有主循环）
│  ├─ base_scene.py               # Scene 接口
│  ├─ main_menu_scene.py          # 主菜单
│  ├─ game_scene.py               # 游戏内（含暂停覆盖层）
│  ├─ replay_select_scene.py      # 回放文件选择
│  ├─ replay_scene.py             # 回放播放
│  └─ settings_scene.py           # 设置界面
│
├─ shared/                        # 双方共享层（不反向依赖 game / Replay_System）
│  ├─ record_format.py            # .dem 3.0 唯一读写入口
│  ├─ record_format_legacy.py     # v1/v2 只读兼容
│  ├─ record_loader.py            # 版本派发器
│  ├─ player_view.py              # 玩家渲染（game 与 replay 共用）
│  └─ hud.py                      # 全局状态徽章
│
├─ config/
│  ├─ language/
│  │  ├─ en-US.json
│  │  └─ zh-CN.json
│  └─ item.json
│
├─ NPC/                           # NPC 模块（预留）
├─ sounds/
│  ├─ UI_Sounds_Click.mp3
│  ├─ UI_Sounds_Hover.mp3
│  └─ UI_Sounds_Switch.mp3
│
├─ source/
│  ├─ main_loading_menu.py
│  └─ menu_btn_style.py
│
├─ user/
│  └─ user_config.json
│
├─ Adrenaline.png
├─ console.py
├─ data.py
├─ game.py
├─ item.py
├─ main.py
├─ player.py
├─ README.md
├─ Replay_System.py
└─ settings.py
```

---

## 版本历史更新

### v0.3.0 (2026-10-02) - 架构重构与回放 3.0

本次更新是这个项目自 0.2.0 以来**最大幅度的一次结构重构**。

核心目标：**把主循环、状态管理、场景职责从 `Game` / `main_menu` / `Replay_System` 里彻底抽出来**，引入 `core/` + `scenes/` + `shared/` 三层结构。

> **重要提示**：本次更新破坏了旧的录制文件写入兼容。`VERSION: 3` 是当前唯一写入格式，v1/v2 旧文件通过 `record_format_legacy.py` 只读兼容。

#### 一、架构重构（核心）

**新增三层结构**：

* `core/` —— 状态与主循环（与具体玩法无关）
* `scenes/` —— 场景层（每个场景一个类，不拥有主循环）
* `shared/` —— 双方共享层（不反向依赖 `game` / `Replay_System`）

**关键变化**：

* **主循环从 `Game.run()` 里搬出** → `AppLoop` 是唯一主循环。`Game` 不再拥有 `while`，只提供 `update(dt)` / `render()` / `handle_event(event)`
* **`main_menu()` 的 while 循环拆成 `MainMenuScene`**：主菜单 → 游戏 → 暂停 → 回放 → 设置 → 主菜单，全部走同一条分发路径
* **`GameState` 从 `game.py` 删除** → 改用 `core.state.AppState`；`GameState.REPLAY` 代码已删除
* **回放不再自己建主循环**：`Replay_System.run_replay_mode` / `select_replay_file` / `no_replay_message` / `handle_replay_events` / `render_replay_scene` 五个函数全部删除，改为 `ReplaySelectScene` + `ReplayScene`
* **暂停不是独立状态**：`IN_GAME / PAUSED` 是 `GameScene` 的子状态，`render` 先画游戏再叠半透明遮罩，性能优于把游戏帧缓存成 Surface
* **全局状态徽章**：`shared/hud.py` 在所有场景渲染之上统一画左下角状态文本（如 `IN_GAME / PAUSED`），不再每个场景各写一份

#### 二、回放格式 3.0（破坏性变更）

**格式规范**：

```
VERSION: 3
SCREEN_WIDTH: 1920
SCREEN_HEIGHT: 1080
RECORD_FPS: 64
START_TIME: 1727781000.123
E:0,P,player
E:1,E,drone_1

C:<time>,<eid>,<command_list>             # 高阶命令，例 C:0.016,0,W,A
I:<time>,<eid>,<key:state;...>            # 原始输入，例 I:0.005,0,W:1;A:1
S:<time>,<eid>,<x>,<y>,<vx>,<vy>,<flags>  # 快照，例 S:0.200,0,...,sprint=1;adr=0;gnd=1
```

**设计要点**：

* **实体注册段 `E:` 显式列出所有 eid**，`eid=0` 恒为玩家；etype 单字母 `P`/`F`/`E`/`N`（玩家 / 友军 / 敌军 / 中立）
* **所有数据行都带 eid** → NPC 接入准备，格式统一
* **flags 用 `k=v;k=v` 键值对** → 加字段零成本；按 etype 查 `FLAG_SCHEMA` 转类型
* **旧版本不兼容**：v1/v2 只读兼容走 `record_format_legacy.py`，加载时由 `record_loader.load()` 读文件头派发
* **时间基准统一**：录制端 `time.time() - start_time`；回放端直接用这个 t

**玩家 flags**：`sprint` / `adr` / `gnd`（对应 `sprinting` / `adrenaline_active` / `grounded`）

**NPC flags（预留）**：`hp` / `state` / `target` / `anim` / `alive`（schema 在 `shared.record_format.NPC_FLAGS`）

#### 三、录制与回放模块瘦身

**`game.py`**：

* 删除 `GameState` 枚举、`run()` 主循环、`record_file` / `last_key_states` 等直接操作文件的字段
* 录制逻辑改为 `RecordWriter` 调用（`shared/record_format.py`）
* `handle_event(event)` 返回信号 `'quit' | 'pause' | None`，不再自己 `sys.exit()`
* `update(dt)` 由 AppLoop 提供 dt，不再自己算时间
* `render()` 不再 `flip()`
* 玩家状态渲染改为调用 `shared.player_view`，与回放视觉一致
* 新增 `_collect_entity_specs()` / `_collect_frame_data()` → NPC 接入点

**`Replay_System.py`**：

* 只保留 `GameReplayer` 类（加载 / 插值 / 应用指令 / 特效 / 回放 UI）
* 删除全部主循环和文件选择逻辑
* 加载改用 `shared.record_loader.load()`
* `Snapshot` 的 `sprinting` / `adrenaline` 改从 `flags` dict 读

**`main.py`**：

* 压缩为：加载菜单 → 初始化 pygame → 创建 AppLoop → 注册场景 → `app.run()`
* 不再包含 `ButtonManager` / `create_menu_buttons` / `draw_buttons` / `handle_menu_selection` / `start_game`

#### 四、设置场景落地（SettingsScene）

* **`settings.py` 减负**：删除 `settings_menu()`（那个 while 循环 + `sys.exit()`）；保留 `StyleSelector` / `create_settings_buttons` / `create_settings_controls` / `draw_settings_ui` / `save_settings` 作为纯控件和纯渲染
* **`scenes/settings_scene.py` 新增**：拆成 `handle_event` / `update` / `render`，纳入 AppLoop
* **`SettingsSubState` 枚举**：`INTERFACE` / `AUDIO` / `GAMEPLAY` / `CONTROLS`，徽章显示如 `SETTINGS / INTERFACE`
* **行为保持**：点"应用"才提交 `preview_style` 到 `user_config`；点"返回"或 ESC 不保存；`~` 键仍可打开控制台

#### 五、ESC 语义集中化

* **`core/key_router.py` 新增**：维护 `(AppState, sub_state) → handler(scene)` 表
* **`AppLoop` 集成**：事件分发给场景前先走 `key_router.dispatch(event, scene)`
* **场景不再写 `if K_ESCAPE`**：所有 ESC 分支收拢到一个文件；新增状态只需改路由表
* **控制台覆盖层优先**：`Scene.escape_is_busy()` 钩子，控制台打开时 ESC 让给控制台

**路由表**：

| 场景 / 子状态          | ESC 行为（控制台关） | ESC 行为（控制台开） |
| ---------------------- | -------------------- | -------------------- |
| `MAIN_MENU`          | 退出程序             | 交给控制台           |
| `IN_GAME / NORMAL`   | 暂停                 | 交给控制台           |
| `IN_GAME / PAUSED`   | 恢复游戏             | 交给控制台           |
| `REPLAY_FILE_SELECT` | 返回主菜单           | —                   |
| `REPLAY_PLAYING`     | 返回文件选择         | —                   |
| `SETTINGS`           | 返回主菜单（不保存） | 交给控制台           |

#### 六、`data.py` 微调

* `RECORD_VERSION` 从 `2` 改为 `3`
* `load_player_image()` 加缓存（`_PLAYER_IMAGE_CACHE`），避免回放端多实体重复读盘

#### 七、行为不变的部分（有意为之）

* 主菜单按钮悬停 / 点击音效与动画
* 控制台（`~` 呼出、命令、输出）
* 肾上腺素 Q 键激活、粒子特效
* 录制 F2 开始/停止，检测面板 F1
* 设置分页与 `StyleSelector` 控件
* 加载菜单（`source/main_loading_menu.py`）
* 音效路径、颜色常量、物理参数

#### 八、已知问题

* `StyleSelector.handle_event` 内部仍保留 `pygame.display.flip()` + `pygame.time.delay()` 点击动画，与 AppLoop 的统一 flip 并存。视觉正常但会有轻微重复 flip。
* `console.Console` 的 `escape_is_busy()` 判定依赖 `console.state != ConsoleState.CLOSED`，如果未来控制台新增中间态需要同步更新。
* 回放 3.0 第一版**只渲染 eid=0（玩家）**。多实体回放会在 NPC 接入时补上。

#### 九、给未来的自己（NPC 接入点）

**录制端** —— 只需两处改动：

1. `Game._collect_entity_specs()` 里为每个 NPC 加 `EntitySpec(eid=N, etype=..., name="...")`
2. `Game._collect_frame_data()` 里为每个 NPC 加 `EntityFrameData(eid=N, position=..., velocity=..., flags={...}, command=None)`

**回放端** —— 把 `GameReplayer.load_recording()` 里 eid=0 的过滤去掉，改成遍历 `rec.snapshots_by_eid`；渲染按 etype 走 `shared/player_view.draw_*` 或未来 `shared/npc_view.draw_*`。

**flags 扩展** —— 在 `shared.record_format.NPC_FLAGS` 里加一项即可，其余代码自动适配。

**新增全局状态** —— `core/state.py` 加枚举值 + `core/key_router.py` 加路由表一行 + 场景类实现 `escape_is_busy()`（如有覆盖层）。场景本身无需知道 ESC 语义。

#### 十、迁移须知（从 0.2.8 升级）

1. **旧录制文件**：仍可回放（走 `record_format_legacy.py`），但新录制一律 3.0 格式，旧代码无法读新文件
2. **`main.py` 不再有 `main_menu()` 函数**：如果你有外部脚本 import 它，需要改为 `AppLoop + MainMenuScene`
3. **`game.py` 不再有 `Game.run()`**：任何直接调用 `Game(...).run()` 的代码需改为走 AppLoop
4. **`Replay_System.run_replay_mode(screen)` 已删除**：改用 `app.switch_to(AppState.REPLAY_FILE_SELECT)`
5. **`settings.settings_menu(...)` 已删除**：改用 `app.switch_to(AppState.SETTINGS)`，或直接用 `SettingsScene`

---

### v0.2.8 (2026-07-08) - 分辨率调整

* 使用 Python 的 tkinter 方式，改写了屏幕分辨率

### v0.2.6 (2025-08-15) - 设置系统与加载界面重构

* **重构设置界面**：
  * 优化了设置菜单的处理逻辑
  * 实现分页式设置界面（界面/音频/游戏性/控制）
  * 添加可视化设置控件（样式选择器）
* **用户保存机制集成**：
  * 实现了用户配置文件的保存功能
  * 自动创建 user 目录和配置文件
  * 支持按钮样式持久化保存
* **模块化重构**：
  * 将设置系统从主程序剥离为独立模块
  * 新增 settings.py 模块
* **数据文件增加**：
  * 在 data.py 中增加 UI 颜色、常量定义
  * 添加缩放计算工具函数
* **新增加载界面**：
  * 实现游戏加载界面
  * 加载界面会加载用户配置文件
  * 支持动画效果（线条动画/文字淡入淡出）

### v0.2.5 (2025-08-09) - 代码重构

* **主要重构内容**：
  * 移除了所有硬编码的文本字符串，替换为 data.py 中定义的常量
  * 移除了所有硬编码的颜色值，替换为 data.py 中定义的颜色常量
  * 使用格式化字符串常量来统一文本格式
  * 简化了 UI 元素的创建，直接从 data.py 获取预设文本
  * 统一了字体大小的获取方式
* **新增文件夹**：
  * 新增 user 文件夹
  * 新增 user_config.json 文件，用于保存用户设置
  * 注意：功能未集成

### v0.2.4 (2025-08-06) - UI 系统升级与性能优化

* **新 UI 系统**：
  * 新增 COD 风格按钮交互系统
  * 两种可切换按钮风格（COD 风格/默认风格）
  * 按钮悬停/点击动画反馈
* **音效系统升级**：
  * 新增悬停、点击、切换三种音效
  * 悬停和点击音效应用到所有按钮
* **设置界面增强**：
  * 新增按钮风格切换功能
  * 新增设置按钮和界面
* **文件结构调整**：
  * 新增 source 文件夹
  * 新增 menu_btn_style.py 按钮样式库
* **代码优化**：
  * 优化 main.py、console.py、data.py 等核心模块
* **功能性调整**：
  * 移除 1、2、3 键快捷操作，改用鼠标操作
  * 保留 ESC 按键退出、~(`) 按键切换控制台

### v0.2.3 (2025-07-26) - 肾上腺素系统与控制台增强

* **肾上腺素效果集成**：
  * 完全集成肾上腺素效果系统
  * 添加肾上腺素激活视觉反馈（红色粒子效果）
  * 肾上腺素参数可在 item.json 中配置
* **控制台改进**：
  * 控制台高度可通过 `data.CONSOLE_HEIGHT` 参数配置
  * 优化控制台显示效果
  * 修复控制台滚动问题
* **命令系统更新**：
  * 重新启用 `give` 命令
  * 新增 `replay` 命令（强制播放指定回放文件）
* **代码重构**：
  * 优化 Replay_System.py 架构
  * 优化 game.py 架构

### v0.2.2 (2025-07-23) - 框架重置与控制台优化

* **框架重置**：对整个框架进行了大幅度重构，提高代码可维护性
* **控制台调整**：移除了控制台可拖拽调整大小的能力，控制台高度固定为 250 像素
* **稳定性增强**：优化了控制台渲染逻辑，减少资源消耗

### v0.2.1 (2025-07-22) - 控制台优化补丁

* 修复了控制台拖拽卡死问题
* 添加了表面创建频率限制（1 秒内最多创建 1 次）

### v0.2.0 (2025-07-21) - 控制台与回放系统增强

* 新增交互式控制台系统
* 回放系统增加高阶指令（90%）+原始输入（5%）+状态快照（5%）的数据格式
* 添加物品系统框架
* 录制系统优化（版本 2 格式）
* UI 和交互优化

---

## 项目架构详细说明

### 1. `core/` - 状态与主循环

#### `core/state.py`

两层状态定义，避免"暂停时到底算哪个状态"这类模糊：

```python
class AppState(Enum):
    """全局状态。同一时刻只有一个激活。"""
    LOADING = auto()
    MAIN_MENU = auto()
    IN_GAME = auto()
    REPLAY_FILE_SELECT = auto()
    REPLAY_PLAYING = auto()
    SETTINGS = auto()

class GameSubState(Enum):
    NORMAL = auto()
    PAUSED = auto()

class ReplaySubState(Enum):
    PLAYING = auto()
    PAUSED = auto()
    FAST_FORWARD = auto()
    REWIND = auto()

class SettingsSubState(Enum):
    INTERFACE = auto()
    AUDIO = auto()
    GAMEPLAY = auto()
    CONTROLS = auto()
```

* **全局状态** = 当前是谁在跑 `update / render`
* **子状态** = 同一个场景内的模式变化，渲染层叠加

#### `core/app_loop.py`

唯一的主循环。职责：

1. 从 pygame 拉事件，先走 `key_router`，再分发给当前场景
2. 调用当前场景的 `update(dt)` / `render(screen)`
3. 在所有渲染之上画全局 HUD（状态徽章）
4. 处理场景发起的 `switch_to` / `quit` 请求（帧末统一执行，避免切换中状态不一致）

```python
class AppLoop:
    def register(self, state, scene): ...
    def switch_to(self, state, **kwargs): ...
    def quit(self): ...
    def run(self, initial_state): ...
```

#### `core/key_router.py`

集中式 ESC 语义分发。`(AppState, sub_state) → handler(scene)` 表，场景不再自己写 `if K_ESCAPE`。控制台等覆盖层通过 `Scene.escape_is_busy()` 优先拦截。

---

### 2. `scenes/` - 场景层

#### `scenes/base_scene.py`

```python
class Scene:
    def on_enter(self, **kwargs): ...
    def on_exit(self): ...
    def handle_event(self, event): ...
    def update(self, dt): ...
    def render(self, screen): ...
    def escape_is_busy(self) -> bool: return False
```

**约定**：

* 场景不拥有主循环 → `AppLoop` 是唯一主循环
* 场景不调用 `pygame.event.get()` → 事件由 `AppLoop` 分发
* 场景不调用 `pygame.display.flip()` → `AppLoop` 统一 flip
* 场景切换 → `self.app.switch_to(AppState.XXX)`

#### 场景一览

| 场景类                | 对应 AppState          | 子状态                                                   |
| --------------------- | ---------------------- | -------------------------------------------------------- |
| `MainMenuScene`     | `MAIN_MENU`          | —                                                       |
| `GameScene`         | `IN_GAME`            | `NORMAL` / `PAUSED`                                  |
| `ReplaySelectScene` | `REPLAY_FILE_SELECT` | —                                                       |
| `ReplayScene`       | `REPLAY_PLAYING`     | `PLAYING` / `PAUSED` / `FAST_FORWARD` / `REWIND` |
| `SettingsScene`     | `SETTINGS`           | `INTERFACE` / `AUDIO` / `GAMEPLAY` / `CONTROLS`  |

---

### 3. `shared/` - 共享层

#### `shared/record_format.py`

`.dem` 3.0 唯一读写入口。

```python
class RecordWriter:
    def open(self, entities=None): ...
    def register_entity(self, spec): ...
    def write_frame(self, entities, pressed_keys): ...
    def close(self): ...

def load(path) -> Recording: ...
```

**格式规范**（见文件末尾注释）：

```
VERSION: <int>                            # 必须为 3
SCREEN_WIDTH / SCREEN_HEIGHT / RECORD_FPS
START_TIME: <float>
E:<eid>,<etype>,<name>
C:<time>,<eid>,<command_list>
I:<time>,<eid>,<key:state;...>
S:<time>,<eid>,<x>,<y>,<vx>,<vy>,<flags>
```

**flags schema**：

```python
PLAYER_FLAGS = {"sprint": bool, "adr": bool, "gnd": bool}
NPC_FLAGS    = {"hp": int, "state": str, "target": int, "anim": str, "alive": bool}
```

#### `shared/record_format_legacy.py`

v1 / v2 只读兼容。把旧格式统一映射到 `eid=0` 的 `Recording` 结构，让 `GameReplayer` 只需处理一种数据形态。

#### `shared/record_loader.py`

唯一入口 `load(path)`。读文件头 `VERSION:` 派发给 `record_format.load` 或 `record_format_legacy.load`。

#### `shared/player_view.py`

game 与 replay 共用的玩家表现层。**不 import game / Replay_System**，纯函数 + `data.py` 组合。

* `draw_player_body(screen, player)`
* `draw_player_state_label(screen, player)` —— 头顶"行走/奔跑"标签
* `draw_player_stats(screen, player)` —— 左下角速度/位置/着地/肾上腺素

#### `shared/hud.py`

全局状态徽章。`draw_state_badge(screen, state, sub_state)` 挂在 `AppLoop.render` 最后一步，所有场景自动拥有。

---

### 4. `data.py` - 游戏常量与工具函数

#### 屏幕与缩放

* `SCREEN_WIDTH / SCREEN_HEIGHT / BASE_WIDTH / BASE_HEIGHT` —— 通过 tkinter 获取系统分辨率
* `scale_position(x, y, screen)` / `scale_value(value, screen, is_width)` / `get_scaled_font(base_size, screen)`
* `get_scaled_button_rect(button, screen)` —— 注意此函数**带 screen 参数**

#### 物理参数

```python
WALK_SPEED = 250.0     # 基础移动速度
SPRINT_SPEED = 320.0   # 冲刺移动速度
ACCELERATION = 20.0    # 加速度系数
DECELERATION = 15.0    # 减速度
FRICTION = 5.0         # 地面摩擦力系数
```

#### 录制参数

```python
RECORD_VERSION = 3     # 录制文件格式版本（v0.3.0 更新）
RECORD_FPS = 64        # 录制采样率
```

#### 关键工具函数

* `get_timestamp()` —— 生成文件名时间戳
* `load_player_image()` —— 带缓存的玩家贴图加载（v0.3.0 新增缓存）
* `serialize_high_level_command(pressed_keys)` —— 序列化 `"W,A,SHIFT"`
* `create_background_grid(screen)` —— 生成背景网格 Surface
* `get_text(key, default)` —— 从 `config/language/zh-CN.json` 读文本

---

### 5. `game.py` - 游戏内逻辑（不含主循环）

**只负责**：

* 玩家控制 / 物理（委托 `player.py`）
* 录制调用（委托 `shared.record_format.RecordWriter`）
* 游戏内 HUD 渲染（检测面板 / 控制信息 / 玩家状态）

**不再负责**：主循环 / 全局状态 / ESC 语义。

**关键方法**：

```python
def handle_event(self, event) -> str | None:
    # 返回 'quit' / 'pause' / None

def update(self, dt): ...
def render(self): ...          # 不 flip

def start_recording(self): ...
def stop_recording(self): ...
def _collect_entity_specs(self): ...    # NPC 接入点
def _collect_frame_data(self, player, pressed_keys): ...  # NPC 接入点
```

---

### 6. `Replay_System.py` - 回放逻辑

只保留 `GameReplayer` 类：

* 通过 `shared.record_loader.load()` 加载
* 按时间二分 + 线性插值恢复玩家状态
* 应用高阶命令 / 原始输入变化
* 渲染肾上腺素粒子特效
* 回放 UI（控制说明、进度条）

**多实体预留**：`load_recording` 里现在过滤 `eid==0`，NPC 接入时改成遍历 `rec.snapshots_by_eid` 即可。

---

### 7. `player.py` - 玩家角色

* 无参构造
* `draw(screen)` 独立，不依赖 `Game`
* 字段：`position / velocity / sprinting / grounded / adrenaline_active / adrenaline_active_end / adrenaline_cooldown_end / speed_multiplier`
* 肾上腺素激活：`activate_adrenaline(duration, cooldown, speed_multiplier)`

**注意**：`_update_adrenaline_state` 内部用 `pygame.time.get_ticks()`，回放时靠快照插值覆盖，不用真实时间。

---

### 8. `settings.py` - 设置控件（不含主循环）

**v0.3.0 后只保留**：

* `SETTINGS_CATEGORIES` / `SETTINGS_DESCRIPTIONS` 常量
* `StyleSelector` 类 —— 左右箭头切换按钮样式
* `create_settings_buttons(screen, style)`
* `create_settings_controls(screen, user_config)`
* `draw_settings_ui(screen, console, categories, current_category, buttons, controls)` —— 纯渲染
* `save_settings(user_config, button_style, controls)` —— 纯保存

**`settings_menu()` 已删除**，事件分发与主循环迁移到 `scenes/settings_scene.py`。

---

### 9. `console.py` - 控制台系统

保持独立，通过 `Console(game_instance=None)` 构造。主要命令见下表。

---

### 10. `source/` - 按钮样式与加载菜单

* `menu_btn_style.py` —— `CODButton` / `DefaultButton` / `create_button(style, ...)`
* `main_loading_menu.py` —— `show_loading_menu() -> user_config`

---

### 11. `item.py` - 物品系统

`AdrenalineItem.use(player)` → 调用 `player.activate_adrenaline(...)`。

---

## 肾上腺素系统配置

### 参数可在 `config/item.json` 配置

```json
{
  "items": {
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
}
```

### 使用方法

1. 游戏中按 `Q` 键激活肾上腺素效果
2. 控制台使用 `give adrenaline` 命令直接获得效果
3. 效果激活期间显示红色粒子特效（游戏和回放都会渲染）

---

## 控制台命令

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

## 快捷键

| 按键            | 上下文       | 功能                      |
| --------------- | ------------ | ------------------------- |
| `~` / `` ` `` | 所有场景     | 开关控制台                |
| `ESC`         | 主菜单       | 退出程序                  |
| `ESC`         | 游戏中       | 暂停                      |
| `ESC`         | 暂停中       | 恢复游戏                  |
| `ESC`         | 回放播放     | 返回文件选择              |
| `ESC`         | 回放文件选择 | 返回主菜单                |
| `ESC`         | 设置         | 返回主菜单（不保存）      |
| `M`           | 暂停中       | 返回主菜单                |
| `F1`          | 游戏中       | 显示/隐藏键盘状态检测面板 |
| `F2`          | 游戏中       | 开始/停止录制             |
| `Q`           | 游戏中       | 激活肾上腺素              |
| `WASD`        | 游戏中       | 移动                      |
| `Shift`       | 游戏中       | 奔跑                      |
| `空格`        | 回放播放     | 播放 / 暂停               |
| `←` / `→` | 回放播放     | 倒退 / 快进               |
| `↑` / `↓` | 回放播放     | 增加 / 减少播放速度       |
| `J`           | 回放播放     | 跳转到中间时间            |

---

## 项目扩展建议

1. **修改物理参数**：调整 `data.py` 中加速度、摩擦力获得不同手感
2. **添加 NPC**：按 README v0.3.0 第九节的"NPC 接入点"三步走
3. **扩展物品系统**：`item.py` 增加新物品，`config/item.json` 加配置
4. **添加新场景**：`core/state.py` 加枚举 + `core/key_router.py` 加 ESC 路由 + 新建 `Scene` 子类
5. **扩展回放 flags**：`shared/record_format.FLAG_SCHEMA` 加字段，其余自动适配
6. **音效管理系统**：把 `SOUND_MENU_*` 扩展成资源池
7. **更多 UI 风格**：`source/menu_btn_style.py` 加新按钮类，`data.STYLE_NAMES` 加显示名

---

## 项目作者的联系方式

* **GitHub**: [https://github.com/henryplaytime](https://github.com/henryplaytime)
* **邮箱**: [henryplaytime@outlook.com](mailto:henryplaytime@outlook.com)

---

## 感谢词

感谢所有参与测试的用户和贡献者，特别感谢开源社区提供的宝贵建议和支持。我将继续努力完善这个项目！

**项目仓库**: [https://github.com/henryplaytime/Planar-Motion-Game-and-Replay-System](https://github.com/henryplaytime/Planar-Motion-Game-and-Replay-System)

**问题提交**: 请在 GitHub Issues 页面报告任何问题
