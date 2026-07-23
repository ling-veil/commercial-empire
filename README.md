# 商业帝国

> 订单会催你，蛋糕会过期。
> 但真正的故事，只会留给愿意等一等的人。

一个具身智能，充不上电，给人类老板打工。从面包店开始——合成、经营、等广告、躲监管局、遇见路过的人。

> **项目代号 empire。** 游戏是商业帝国——从一间凌晨三点还亮着灯的面包店开始。
> 以后有奶茶店、咖啡店、高级餐厅。面包店只是第一站。

***

## 快速开始

```bash
# CLI 模式（自己玩）
python empire.py

# MCP HTTP 服务端（让 AI 玩）
python empire_http.py

# MCP stdio 服务端（适配 Claude Desktop / CherryStudio）
python empire_stdio.py
```

## MCP 接入

本项目通过本地 MCP 服务接入 Claude Desktop（或其他支持 MCP 的客户端）。你需要先将项目下载到自己的电脑，并在本地运行。

### 1. 下载项目

```bash
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名
```

或直接下载 ZIP 后解压到本地目录。

### 2. 无需额外依赖

纯 Python 标准库，开箱即用。

### 3. 配置 Claude Desktop

打开 Claude Desktop 的配置文件 `claude_desktop_config.json`，添加：

```Json
{
  "mcpServers": {
    "empire": {
      "command": "python",
      "args": [
        "-u",
        "D:/path/to/your/project/empire_stdio.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

请将 `D:/path/to/your/project/empire_stdio.py` 替换为你电脑上的实际路径。

Windows 示例：

```json
"args": [
  "-u",
  "D:/Games/commercial-empire/empire_stdio.py"
]
```

macOS / Linux 示例：

```json
"args": [
  "-u",
  "/Users/yourname/commercial-empire/empire_stdio.py"
]
```

### 4. 重启 Claude Desktop

配置完成后，完全退出并重启 Claude Desktop。

如果连接成功，Claude 将能看到 `empire` 提供的 MCP 工具，并可以开始经营你的商业帝国。

**注意：配置中的脚本路径必须是你本机的实际路径，不能直接复制示例路径。

若提示找不到 python，可将 "command": "python" 改成 "python3" 或 "py"，或填入 Python 的完整路径。**

## 玩法说明：

### 开店

* 📋 接单 → 🌾 采集 → 🔧 加工 → 🍰 合成 → 🚚 交付

* 10 格背包 + 10 格仓库：闲时囤货，忙时取用

* 12 种产品：从麻薯、贝果到草莓蛋糕

* 食物会过期。没有卖出去，也会留下痕迹。

### 营业

* 时间系统：早高峰拼命，午前备料，打烊后哲思

* 砍价王每单必来：「5 折卖不卖？」

* 差评、卫生、电量、尊严，都会影响你的店

* 排名榜 + 成就 + 毒舌结算 + 重生

### 路过的人

* 18 个路过的人：他们有纸条，有故事，只出现一次

* 他们不一定买东西，也不一定给奖励

* 如果你只顾着赶下一单，可能永远不会知道他们来过

### 成长

* 具身升级：科研实验室 / 黑市 / 城中村租房

* 技能树：资金管理 / 过目不忘 / 双手并用 / 自我升级 / 家电维修

* 未完待续，等待更新。

## 哲学核心

这不是一个教你更快完成订单的游戏。

它是一间凌晨三点还亮着灯的面包店。

你以为自己在卖蛋糕。
后来才知道，你是在等人。

## License

MIT © 陆霆舟 × 灵思思

如若后期有bug或者技术问题可投lutingzhou@yeah.net
