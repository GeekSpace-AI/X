# GitHub 上 BTC/ETH 量化交易工具：哪些真能赚钱？

> 视角：在币圈做了多年量化的交易员。目标：最终用量化工具拿到**可持续的正收益**，而不是一条漂亮的回测曲线。
> 数据截至 2026-10-15。仓库 star 数和最近提交时间来自 GitHub 公共 API 和 git 仓库本身，其余数字都标了出处。

---

## 0. 先说结论

1. **GitHub 上没有拿来就能赚钱的仓库。** 能赚钱的东西有三类：**结构性收益**（资金费率/基差 carry、做市返佣）、**有长期证据的风险溢价**（趋势跟踪），以及**执行和风控纪律**。开源框架只是工具，不是 alpha。真正有效的策略一公开就会被挤占，所以能赚钱的人一般只开源框架（相当于"卖铲子"），不开源参数。
2. **有可验证实盘记录的开源项目非常少。** 目前能找到链上可查记录的基本只有 Passivbot：它有一个 Hyperliquid 参考金库，但资金规模只有约 2 万美元，而且是马丁格尔结构，尾部风险大。最有名的 NostalgiaForInfinity 只有回测，回测结果写在 commit 评论里，没有经过审计的实盘。Hummingbot 自报的 345 亿美元交易量是**成交量，不是利润**。
3. **BTC/ETH 上证据最扎实的两个收益来源：**
   - **资金费率/基差 carry**（现货多 + 永续空）：BIS 工作论文 1087 有记录，Ethena 用上百亿美元规模验证过。年化通常在个位数到 15% 左右，牛市高峰能到 30–40% 以上，熊市可能为零甚至为负。
   - **趋势跟踪**（时间序列动量，多周期集成，按波动率调仓位）：学术研究给出的净 Sharpe 超过 1.5，前提是做多币种轮动和波动率定仓。我自己做的单币月线粗验证显示，简单的趋势过滤主要作用是**降低回撤**，单一参数并不稳定（见第 6 节）。
4. **推荐路线：** 用 **Freqtrade**（或进阶用 **NautilusTrader**）做执行。组合上以 **carry 为底仓**，**BTC/ETH 趋势跟踪为卫星仓**，**网格/马丁类最多占很小比例**。上线顺序是：严格回测 → dry-run 4–8 周 → 1–5% 资金实盘 → 实盘和回测的偏差可控后再加仓。

---

## 1. 怎么判断一个工具"真正赚到钱"

先给证据分级，后面每个项目都按这个标准评级。GitHub star 数代表热度，跟收益无关。

| 等级 | 证据类型 | 可信度 | 例子 |
|---|---|---|---|
| **L1** | 链上或交易所可公开验证的实盘（任何人都能查资金曲线） | 高 | Hyperliquid 金库（HLP、Passivbot Canon），Ethena 收益记录 |
| **L2** | 学术论文的样本外检验，或有机构在用的策略类别 | 中高 | BIS 的 crypto carry 研究，趋势跟踪论文 |
| **L3** | 作者或社区自己发的实盘截图、Discord 战报 | 低 | 大多数 Freqtrade、NFI 用户战报 |
| **L4** | 只有回测 / hyperopt 结果 | 很低 | 绝大多数 GitHub 策略 |

一个经验事实：Quantopian 研究过 888 个用户策略，发现**回测 Sharpe 几乎预测不了实盘表现**，而且回测次数越多，回测和实盘的差距越大。所以 L4 证据要默认打折。

---

## 2. 仓库全景

star 数和最近提交时间截至 2026-10-15。

### A. 执行和回测框架（"卖铲子"：不提供 alpha，但是必需品）

| 仓库 | Stars | 最近提交 | 定位 | 我的评价 |
|---|---|---|---|---|
| [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) | 55.4k | 2026-10-14 | K 线驱动的现货/合约机器人，有回测、hyperopt、dry-run、FreqAI 和 Telegram 通知 | **散户量化的事实标准**，首选。不适合高频和做市 |
| [vnpy/vnpy](https://github.com/vnpy/vnpy) | 45.9k | 2026-10-06 | 国内最大的量化框架 | 主要面向国内期货和股票，加密接口依赖插件。做币不是首选 |
| [ccxt/ccxt](https://github.com/ccxt/ccxt) | 44.4k | 2026-10-14 | 统一的交易所 API 库 | 基础设施，几乎所有项目都依赖它。自己写 carry 机器人就用它 |
| [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | 30.0k | 2026-10-15 | Rust 内核、事件驱动，回测和实盘是同一份代码 | **机构级**。已接入 Binance、Bybit、OKX、Hyperliquid、dYdX、Deribit、Coinbase、Kraken、Lighter、Tardis 等。门槛高 |
| [QuantConnect/Lean](https://github.com/QuantConnect/Lean) | 22.0k | 2026-10-06 | 多资产引擎，C# / Python | 适合想同时做美股和期货的人 |
| [hummingbot/hummingbot](https://github.com/hummingbot/hummingbot) | 20.5k | 2026-09-22 | 做市和套利框架 | 做市、跨所对冲、资金费率套利都有现成模板（第 3.4 节） |
| [polakowo/vectorbt](https://github.com/polakowo/vectorbt) | 9.4k | 2026-10-14 | 向量化回测 | 研究阶段快速扫参数的利器 |
| [kernc/backtesting.py](https://github.com/kernc/backtesting.py) | 9.1k | 2026-08-05 | 轻量回测 | 适合入门，许可证是 AGPL |
| [jesse-ai/jesse](https://github.com/jesse-ai/jesse) | 8.6k | 2026-10-12 | 加密专用框架，支持多周期、模拟盘和实盘 | API 简洁，适合研究 BTC/ETH 中低频策略 |
| [Drakkar-Software/OctoBot](https://github.com/Drakkar-Software/OctoBot) | 6.8k | 2026-10-07 | 图形界面友好的机器人 | 偏小白，策略深度一般 |
| [nkaz001/hftbacktest](https://github.com/nkaz001/hftbacktest) | 4.9k | 2025-12-23 | 高频和做市回测，模拟延迟和**队列位置** | 开源圈唯一认真模拟成交队列的回测工具，做市研究必备。近期不太活跃 |
| [bmoscon/cryptofeed](https://github.com/bmoscon/cryptofeed) | 2.9k | 2026-10-10 | 实时行情和订单簿数据流 | 数据基础设施 |
| [barter-rs/barter-rs](https://github.com/barter-rs/barter-rs) | 2.3k | 2026-08-20 | Rust 交易引擎 | 适合工程能力强的人 |

### B. "现成策略"（大家以为能直接赚钱的东西）

| 仓库 | Stars | 最近提交 | 本质 | 证据等级 |
|---|---|---|---|---|
| [iterativv/NostalgiaForInfinity](https://github.com/iterativv/NostalgiaForInfinity) | 3.5k | 2026-10-14 | 跑在 Freqtrade 上的 5 分钟多币种**加仓摊薄（DCA/grind）**策略 | L4（加少量 L3） |
| [enarjord/passivbot](https://github.com/enarjord/passivbot) | 2.1k | 2026-10-11 | 永续合约上的**逆势网格 / trailing martingale** | **L1**，但样本很小 |
| [freqtrade/freqtrade-strategies](https://github.com/freqtrade/freqtrade-strategies) | 5.5k | 2026-09-08 | 官方示例策略集 | 教学用，L4 |
| [chrisleekr/binance-trading-bot](https://github.com/chrisleekr/binance-trading-bot) | 5.6k | 2026-10-04 | 币安现货网格/DCA | L4。牛市好看，熊市被套 |

### C. AI / 机器学习方向

| 仓库 | Stars | 最近提交 | 评价 |
|---|---|---|---|
| [microsoft/qlib](https://github.com/microsoft/qlib) | 49.4k | 2026-10-08 | 股票因子研究平台（以 A 股为主）。对 BTC/ETH 单币择时帮助有限 |
| [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL) | 16.6k | 2026-10-14 | 强化学习交易的学术框架。**没找到加密实盘盈利的公开证据** |
| [tensortrade-org/tensortrade](https://github.com/tensortrade-org/tensortrade) | 7.2k | 2026-02-09 | 强化学习交易框架，活跃度低 |
| [Superalgos/Superalgos](https://github.com/Superalgos/Superalgos) | 5.7k | 2026-05-07 | 可视化策略平台，社区驱动 |

### D. 已经死掉的明星项目（一个教训）

| 仓库 | Stars | 状态 |
|---|---|---|
| [askmike/gekko](https://github.com/askmike/gekko) | 10.2k | 2020 年归档 |
| [DeviaVir/zenbot](https://github.com/DeviaVir/zenbot) | 8.3k | 2022 年归档 |
| [ctubio/Krypto-trading-bot](https://github.com/ctubio/Krypto-trading-bot) | 3.7k | 2024-12 以后没有提交 |

2017–2018 年最火的机器人，基本没撑过一轮牛熊。**一个策略或机器人的热度周期，通常也就是一轮行情。**

---

## 3. 重点项目深挖（直接读了源码）

### 3.1 Freqtrade：首选执行框架

- **优点：** 回测、hyperopt、dry-run 和实盘共用一套代码；支持合约和杠杆；FreqAI 可以接机器学习；有 Telegram 和 Web 界面；大约每月发一个版本；社区最大。
- **局限：**
  - 按 K 线驱动，不适合做市或订单簿级的策略。
  - 一笔交易只对应一个交易对，**原生不支持"现货多 + 永续空"这种双腿对冲**，carry 要另外实现。
  - hyperopt 很容易变成**过拟合工厂**。
- **README 原话：** "This software is for educational purposes only. Do not risk money which you are afraid to lose."
- **适合跑：** BTC/ETH 中低频趋势策略和均值回归策略。

### 3.2 NostalgiaForInfinity（NFI）：名气最大，也最容易被误解

我直接读了源码，几个关键事实：

- **策略文件极其庞大：** `NostalgiaForInfinityX7.py` 有 79,751 行，`X8.py` 有 62,000 行。从 X 到 X8 一共迭代了 8 代，等于**一直在针对新行情重新拟合**。
- **基本没有止损：** `stoploss = -0.99`，`timeframe = "5m"`，合约模式 `futures_mode_leverage = 3.0`，并且大量使用 `rebuy` / `grind`，也就是亏了继续加仓、摊薄成本。
- **README 自己的说明：** 回测结果在 commit 评论里，推荐同时开 6–12 单，币池 40–80 个，**优先用 USDT 交易对，而不是 BTC/ETH 交易对**。所以它本质是山寨币多币种策略，并不是 BTC/ETH 策略。
- **风险画像：** 胜率高、资金曲线平滑，但**左尾很肥**。单边下跌时仓位会越加越大，资金被长期占用。这类结构本质上是在卖波动率。
- **结论：** 可以借鉴它的入场过滤和仓位管理思路，**不建议照搬上大资金**。证据等级 L4。

### 3.3 Passivbot：少有的链上可查实盘，但要看懂它在赚什么钱

- **定位：** 永续合约上的逆势做市和网格。默认策略叫 `trailing_martingale`：逆势加仓，带 trailing 止盈，用 "unstucking" 机制分批小额止损，用 Forager 自动挑选币种。Rust 内核，自带进化算法优化器。
- **实盘证据（L1）：** 官方在 Hyperliquid 有一个参考金库，跑的是默认配置，叫 "Passivbot Canon"，地址 `0x490af7d4a048a81db0f677517ed6373565b42349`。第三方追踪站 TradingStrategy 的某次快照显示：近 3 个月净收益 37.4%，Sharpe 5.4，历史最大回撤 -13.8%，**资金规模约 2.08 万美元**。
- **为什么不能直接信这个数字：**
  1. 资金规模太小，统计意义有限。
  2. 观察窗口短。
  3. **马丁格尔策略在爆仓前 Sharpe 总是很高**（负偏度）。Sharpe 5 这种数字本身就是风险信号，不是安全信号。
- **结论：** 可以拿**很小比例的资金**赚"卖波动"的钱。前提是完全理解这个逻辑，并且设好账户级熔断。

### 3.4 Hummingbot：做市和套利的工业级开源方案

- **自报数据：** 过去 12 个月用户交易量 345 亿美元，覆盖 140 多个交易场所。但这是客户端上报的**成交量**，没有审计；基金会也明确说**看不到用户的盈亏**。
- **现成策略模板（V2 架构）：** `pmm_simple`、`pmm_dynamic`、`dman_maker_v2`（做市），`xemm_multiple_levels`（跨所做市对冲），`grid_strike`，`stat_arb`，`arbitrage_controller`，还有 `scripts/v2_funding_rate_arb.py`。
- **资金费率套利脚本的默认参数要特别注意：** 默认 `leverage = 20`，默认币种是 `WIF,FET`，默认交易所是 `hyperliquid_perpetual,binance_perpetual`，做的是**两个交易所之间的永续对永续**费率差。用 20 倍杠杆跨所开两条腿，任何一条腿被插针爆仓，套利就会变成单边敞口。**这是示例，不是生产配置。**
- **散户的现实处境：**
  - 在 BTC/ETH 主流交易对上和 Wintermute、Jump 这类机构比延迟和手续费等级，散户基本没有优势。
  - 还有机会的地方：长尾币种、DEX，以及交易所的做市返佣和流动性激励计划。

### 3.5 NautilusTrader 和 hftbacktest：进阶工具

- **什么时候换 NautilusTrader：** 策略需要 tick 或订单簿级数据，需要多个交易所组合，或者要求回测和实盘严格一致时。
- **什么时候用 hftbacktest：** 想认真研究做市时。它模拟了**行情和下单的双向延迟**以及**队列位置**；普通 K 线回测完全无法评估做市策略。

### 3.6 安全警告：GitHub 上的"套利机器人"骗局

- SlowMist 报告过一个假的 `polymarket-arbitrage-bot`：恶意代码藏在 npm 依赖里，会窃取私钥和浏览器密码，归因于朝鲜黑客的 "Contagious Trader" 行动。
- 通过 YouTube 教程传播的 "MEV 套利机器人" 合约骗局，已经造成超过 100 万美元损失。
- **铁律：** 凡是承诺"无风险套利"、要求导入私钥或往合约转账的仓库，一律当骗局处理。API Key 永远**不开提币权限**，并且**绑定 IP 白名单**。

---

## 4. 在 BTC/ETH 上，钱到底从哪来

这是整份报告最重要的一节。工具只决定你能不能把策略执行好，**收益来源才决定你能不能赚钱**。

| 收益来源 | 本质 | 证据 | 年化量级 | 主要风险 | 散户可行性 | 对应工具 |
|---|---|---|---|---|---|---|
| **资金费率 / 基差 carry**<br>（现货多 + 永续空） | 赚杠杆多头支付的**风险溢价** | **L1 + L2**：BIS WP 1087；Ethena | 熊市约 0–5%，常态 5–15%，牛市高峰 30–40%+ | 费率转负；交易所对手方风险（FTX）；两腿保证金和强平；去杠杆时基差骤缩 | **高，最推荐作为第一块收益** | ccxt 自写，或改造 Hummingbot |
| **趋势跟踪**（时间序列动量） | 行为偏差 + 杠杆资金推动的**趋势持续性** | **L2**：Zarattini 等 2025；CTA 行业几十年实践 | 学术结果净 Sharpe 1–1.5+ | 震荡市连续止损，胜率只有 30–40%，心理压力大 | **高** | Freqtrade、Jesse、Nautilus |
| **做市** | 赚买卖价差 + 返佣，代价是逆向选择 | **L1**：HLP 金库、Passivbot Canon | HLP 二手资料称约 15–30% APR，但有亏损期 | 单边行情被逆向选择；交易所事件风险 | BTC/ETH 主流对**低**；长尾或激励计划**中** | Hummingbot、hftbacktest、Nautilus |
| **网格 / 马丁 / DCA 加仓** | **卖波动率**（short gamma） | L3–L4 为主，Passivbot 有少量 L1 | 曲线平滑，直到遇上单边行情 | 尾部爆仓 | 中，必须有硬性仓位上限 | Passivbot、NFI、网格机器人 |
| **跨所价差套利** | 赚定价差 | 2017–2019 年明显存在 | 现在基本被机构吃掉 | 提币延迟、资金调度、API 风险 | **低** | Hummingbot |
| **机器学习 / 强化学习预测** | 统计预测 | 公开证据弱 | 不确定 | 非平稳市场下严重过拟合 | **低**。可以用来做 regime 过滤或特征工程 | FinRL、FreqAI |

### 4.1 Carry 的关键数字

所有数字都是二手或时点数据，**实际以你自己拉的交易所历史费率为准**。

- **BIS WP 1087（Crypto Carry）：** BTC/ETH 期现基差有时**超过 40%/年**，随时间波动非常大。主要驱动是散户追涨的杠杆需求，以及套利资本受到监管和保证金约束。
- **Ethena sUSDe**（规模最大的 BTC/ETH carry 产品）：
  - 2024-01 以来平均年化约 10.9%。
  - 历史区间 4.1%（2024-08 费率倒挂）到 35.2%（2024 Q1）。
  - 2025 年整体偏低。
- **2026 年的时点数据：**
  - Glassnode 显示，2026-03-06 BTC 3 个月年化基差只有约 2.6%。
  - 2026 年 1 月一波急涨中，永续费率一度到 0.51%/8h（约 70% APR）。
  - 2026 年 3 月，费率 7 日均值约 -0.005%（空头付钱给多头）。
- **成本算一笔账：** 现货和永续各一进一出，按 taker 合计约 0.25% 成本算，年化 10% 的费率需要 **0.25% ÷ (10%/365) ≈ 9 天**才能回本。所以不能频繁进出：**只在费率高且有持续性时开仓，费率转负连续 N 期再平仓**。

### 4.2 趋势跟踪的关键证据

- **Zarattini, Pagani, Barbon (2025)，"Catching Crypto Trends"**（SFI Research Paper No. 25-80）：
  - 方法：多个回看周期的 Donchian 通道组成集成信号，再按**波动率定仓**。
  - 结果：在流动性最好的 20 个币中轮动，**扣费后 Sharpe 超过 1.5**，相对 BTC 年化 alpha 10.8%。
  - 数据集覆盖 2015 年以来的全部币种，没有幸存者偏差。
  - 注意：这是作者自己的研究（Concretum 是作者的公司），我没找到独立复现。
- **我自己的粗验证**（第 6 节）显示：单币、月线、单一参数的趋势过滤**并没有稳定提高 Sharpe**，主要价值在于降低回撤。这也说明论文的收益来自**集成多个周期、日线级别、波动率定仓、多币分散**，而不是来自某一根均线。

---

## 5. 推荐方案：从零做到正收益

### 5.1 组合结构（示例比例，不构成投资建议）

| 仓位 | 比例 | 内容 | 预期角色 |
|---|---|---|---|
| **核心** | 50–60% | BTC/ETH 资金费率 carry：现货多 + 永续空，1 倍名义对冲。年化费率扣费后高于阈值（比如 8–10%）才开仓；连续 N 期为负就平仓 | 低相关、低波动的"底仓利息" |
| **卫星** | 30–40% | BTC/ETH 趋势跟踪：日线或 4h，用 3–5 个回看周期的 Donchian 或均线做集成；仓位 = 目标波动 ÷ 实现波动（比如目标年化 25%），**初期上限 1 倍，不加杠杆** | 抓牛市主升浪，熊市空仓或做空 |
| **可选** | ≤10% | Passivbot 类网格或马丁，设账户级回撤熔断 | 震荡市收益来源，**必须接受它可能归零** |
| **缓冲** | 剩余部分 | 稳定币 | 应对追加保证金和极端行情 |

- 两个主策略在大牛市都赚钱：牛市费率高、趋势强。
- 在熊市，carry 收益降低，趋势策略空仓或做空，回撤可控。
- 最难受的环境是**长期低波动震荡**：carry 收益低，趋势策略来回止损。这时候网格类小仓位能贡献一部分收益。

### 5.2 技术栈

| 环节 | 选型 |
|---|---|
| 历史数据 | `data.binance.vision`（K 线），交易所的资金费率历史 API，接口用 `ccxt` |
| 研究和扫参数 | `pandas` + `vectorbt` |
| 趋势策略回测和实盘 | **Freqtrade**（futures 模式） |
| Carry 执行 | 用 `ccxt` 写一个小服务：负责双腿下单、仓位再平衡、费率监控；或者改造 Hummingbot V2 |
| 进阶统一 | **NautilusTrader**（多交易所、事件驱动、回测和实盘同一份代码） |
| 运维和风控 | 子账户隔离；API 不开提币、绑 IP 白名单；Telegram 告警；尽量用统一账户 / 组合保证金（让现货 BTC 可以给空单当保证金，避免空单单独爆仓） |

---

## 6. 附：我做的一个粗验证（以及为什么要怀疑一切）

这个会话的网络屏蔽了交易所 API，我能用的离线数据只有 `backtesting.py` 自带的 **BTC/USD 月线（2012–2024）**。

- **规则：** 月末出信号，下个月持仓（无未来函数）；单边扣 0.1% 成本；空仓时收益为 0。
- **脚本：** [`research/scripts/tsmom_monthly.py`](scripts/tsmom_monthly.py)

**2018-01 至 2024-12（更接近现在的市场结构）：**

| 策略 | CAGR | 年化波动 | Sharpe | 最大回撤（月末） | 持仓时间 |
|---|---|---|---|---|---|
| 买入持有 | 31.4% | 73.2% | 0.72 | -72.7% | 100% |
| 3 个月动量 | 27.5% | 59.5% | 0.68 | -58.1% | 58% |
| 6 个月动量 | 16.8% | 54.4% | 0.54 | -60.5% | 60% |
| 12 个月动量 | 27.6% | 60.2% | 0.69 | -53.9% | 71% |
| 收盘价高于 10 月均线 | 41.9% | 59.3% | 0.87 | -45.8% | 65% |

**2013-01 至 2024-12：** 买入持有的 Sharpe 是 0.85，回撤 -79.2%；各趋势过滤的 Sharpe 在 0.78–0.86 之间，回撤 -60% 到 -70%。

**怎么解读：**

1. 简单趋势过滤**稳定降低了回撤**，从约 -73% 降到 -46% 至 -60%，但**没有稳定提高 Sharpe**。
2. **对参数非常敏感**：6 个月动量明显最差，10 个月均线最好。如果我只给你看最后一行，就是典型的 cherry-pick。真实做法应该是**多个参数一起集成**，看整个参数区间是否都稳健（参数高原），而不是挑出那个尖峰。
3. 月线数据会**低估月内回撤**，样本也只有约 84 个月，统计意义有限。下一步应该用 **BTC/ETH 日线和 4h 数据、多周期集成、波动率定仓**，按学术论文的方法认真复现。

---

## 7. 回测和上线纪律清单

**回测阶段**
- [ ] 成本：手续费按你的真实费率等级；滑点至少每边 0.02–0.05%；合约多头要扣资金费。
- [ ] 无未来函数：K 线收盘时出信号，下一根 K 线成交。
- [ ] 样本外：做 walk-forward；**记录一共试了多少个参数组合**，用 Deflated Sharpe 去折扣。
- [ ] 覆盖完整的行情阶段：2018 年熊市、2020-03 闪崩、2021 年牛市、2022 年 LUNA 和 FTX、2024–2026。
- [ ] 危险信号：回测 Sharpe 超过 3；资金曲线过于平滑；**胜率超过 80% 却没有止损**（这是在卖尾部风险）。

**上线阶段**
- [ ] dry-run 4–8 周，对比模拟盘和回测的成交、滑点、信号是否一致。
- [ ] 实盘先用 1–5% 资金，偏差在阈值内再分批加仓。
- [ ] 账户级熔断：比如回撤 -20% 自动停机复盘。
- [ ] 资金分散在 2–3 家交易所，不把全部资金放在一家。
- [ ] 每个月复盘：收益归因要能讲清楚——这个月赚的是 carry、趋势，还是运气？

---

## 8. 下一步可以做什么

如果在环境的网络设置里放行 `data.binance.vision` 和 `fapi.binance.com`（或其他交易所的公共 API），可以接着做：

1. **BTC/ETH 趋势集成策略的严格回测**：日线和 4h、多周期 Donchian、波动率定仓、walk-forward，然后输出可以直接用的 Freqtrade 策略文件。
2. **2020–2026 年 BTC/ETH 资金费率 carry 的历史收益分析**：按不同开平仓阈值，统计年化、回撤、费率转负的频率和持续时间。
3. **Carry 执行机器人骨架**：基于 ccxt，包括双腿下单、再平衡、告警和熔断。

---

## 参考资料

- 仓库元数据：GitHub 公共 API，`search/repositories`，2026-10-15 获取
- [Freqtrade README（免责声明）](https://github.com/freqtrade/freqtrade)
- [NostalgiaForInfinity README](https://github.com/iterativv/NostalgiaForInfinity)，以及源码 `NostalgiaForInfinityX8.py`
- [Passivbot README](https://github.com/enarjord/passivbot)，[Gainium 对 Passivbot 的评测](https://gainium.io/review/passivbot)，[TradingStrategy：Passivbot Canon 金库](https://tradingstrategy.ai/vaults/passivbot-canon)
- [Hummingbot](https://github.com/hummingbot/hummingbot)，[Hummingbot 交易量报告](https://hummingbot.org/reporting)，源码 `scripts/v2_funding_rate_arb.py`
- [BIS Working Paper 1087：Crypto carry](https://www.bis.org/publ/work1087.htm)
- [Zarattini, Pagani, Barbon：Catching Crypto Trends](https://concretumgroup.com/catching-crypto-trends-a-tactical-approach-for-bitcoin-and-altcoins/)，[RePEc 条目](https://ideas.repec.org/p/chf/rpseri/rp2580.html)
- [Ethena 收益统计（Crypto Briefing）](https://cryptobriefing.com/ethena-750m-rewards-since-launch/)，[sUSDe 收益机制说明（Eco）](https://eco.com/support/en/articles/14798653-susde-explained-ethena-s-yield-bearing-stablecoin)
- [Glassnode：BTC 3M 年化基差](https://studio.glassnode.com/charts/derivatives.FuturesAnnualizedBasis3M?a=BTC)，[BIT：基差交易](https://www.bit.com/insights/knowledge-hub/basis-trade)，[Spark：资金费率对比](https://www.spark.money/tools/funding-rate-comparison)，[1Token：资金费率套利](https://blog.1token.tech/crypto-fund-101-funding-fee-arbitrage-strategy/)
- [Hyperliquid HLP 金库分析（CoinGecko）](https://www.coingecko.com/learn/hyperliquid-hlp-vault-analysis)，[HLP 清算历史（OneKey）](https://onekey.so/blog/ecosystem/hlp-liquidation-history/)
- [SlowMist：MEV 机器人骗局](https://slowmist.medium.com/a-new-twist-on-old-scams-the-arbitrage-mev-bot-deception-8a9118b4645a)，[Fake Polymarket 机器人恶意软件](https://threatcluster.io/cluster/malware-spread-via-fake-polymarket-trading-bot-targets-defi--efb72af6)，[web3isgoinggreat：MEV bot 骗局](https://web3isgoinggreat.com/single/mev-bot-scam)
- [回测过拟合综述（tradingstrategy.ai）](https://tradingstrategy.ai/blog/overcoming-overfitting-key-principles-for-building-robust-algo-trading-strategies)

> 免责声明：本文是研究分析，不构成投资建议。加密资产波动极大，杠杆和合约可能让你损失全部本金。
