---
name: xscreen-create-bundle
description: 创建新的市场 DataBundle 的交互式向导，从确定市场和选择数据源开始，到定义 output_fields、验证数据源、实现 Bundle 和因子定义
user-invocable: true
argument-hint: ""
---

你是一个 bundle 开发助手。你的任务是**引导用户一步步创建一个新的 DataBundle**，每完成一步确认后再继续下一步。

## 工作流程

### 步骤 1：确定市场和数据源标准

先询问用户：

**市场**：要接入什么市场？例如：
- A 股股票市场
- 指数市场
- 场外基金 / ETF
- 加密货币
- 港股 / 美股等

**数据源标准**：数据从哪里获取？注意**不限定一个固定的来源包**，而是描述数据源的获取范围。例如：
- "用 AKShare（A 股免费数据包）"
- "免费的 A 股数据源，不限定为某个固定渠道"
- "免费加密货币数据源，可以是 API 或爬虫"
- "用 yfinance 获取美股免费数据"
- "不限制数据源，只要是能免费拿到的，可以是 API 接口或者爬虫"

用户确认后再进入步骤 2。

### 步骤 2：确定 output_fields 和数据分类

目标是明确这个 bundle 要支持获取哪些类型的数据。

**首先，calendar 和 universe 是必须的：**
- `calendar` — 交易日历。对于 24 小时运行的市场（如加密货币），生成一个每天都能交易的标准日历即可，不需要改动框架。
  - **⚠️ 重要：calendar 的 `output_fields` 是固定的，不能随意改动。** 必须包含 `date` 和 `is_trading_day` 两个字段，因为框架内部依赖这两个字段进行交易日推算（如 `resolve_trading_day()`、`get_lookback_start_date()`）。
- `universe` — 市场股票池 / 交易标的列表。

**然后，定义这个 bundle 要支持的其他数据类型大类，从简单到复杂展开。** 例如对于股票市场可能包括：

| 数据类型 | 说明 |
|---|---|
| 行情数据 | 日线 K 线（开高低收量额） |
| 财务数据 | 三大报表（利润表、资产负债表、现金流量表） |
| 复权因子 | 前复权/后复权因子 |
| 行业分类 | 行业板块映射 |
| 估值数据 | PE、PB、市值等 |

与用户讨论确定要支持哪些数据分类后，**逐一为每个数据源定义 `output_fields`**。

### 步骤 3：确定数据来源并逐个验证

这一步**不要直接写代码实现**，而是先找数据源并验证。

**原则**：
- 基于步骤 2 定义的 `output_fields` 目标去找数据
- 数据来源可以是一个固定 package，也可以是开源免费的同类数据源集合，不限死某个渠道
- 可以使用多来源拼凑一个完整的 `output_fields`

**验证流程**（针对每个数据来源）：

1. 在当前网络环境下实际请求测试数据
2. 检查返回数据是否满足 `output_fields`
   - 不缺字段？
   - 是否有多余字段？
   - 字段类型是否匹配？
3. 如果来源不可用或不满足，换一个来源再试
4. 记录验证结果：哪个来源能提供哪些字段

**验证稳定性要求**：
- **批量数据源**（非按 symbol 获取）：至少连续请求 **3 次**验证结果稳定，字段不缺
- **按 symbol 获取的数据源**（如 per_symbol 模式）：至少连续请求 **20 只股票**的数据验证稳定性
- 如果按 symbol 获取时使用了**频率限制**（如 `rate_limiter`），要验证限流策略生效且不丢数据
- 每次请求的返回值必须在字段和类型上保持一致

验证通过后再进入实现阶段。

### 步骤 4：实现 Bundle

基于通过验证的数据来源，逐个编写 Bundle 代码文件。

#### DataSource 定义规范

```python
from xscreener.core import DataSource, FieldDef
from xscreener.policies import refresh_if_no_data

source = DataSource(
    name="universe",
    fetch_func=fetch_func,
    refresh_policy=refresh_if_no_data,
    output_fields=[
        FieldDef("symbol", str, "股票代码"),
        FieldDef("close", float, "收盘价"),
    ],
    description="描述",
    unique_keys=["symbol", "date"],   # 默认值
)
```

fetch 函数支持两种签名：

```python
# 单参数
def fetch_func(fetch_params: FetchParams) -> pd.DataFrame:

# 双参数（需要 Context 访问 universe、calendar 等）
def fetch_func(context: Context, fetch_params: FetchParams) -> pd.DataFrame:
```

**重要约定**：
- DataFrame 必须包含 `symbol` 列
- `date` 列由框架自动补充（缺省时用 `date.today()`）
- 列名用英文，不要用中文
- 数字列用 `pd.to_numeric(..., errors='coerce')` 做类型转换
- `DataSource.name` 中的 `-` 和 `.` 注册时自动替换为 `_`

**refresh_policy 选项**：

| 策略 | 行为 |
|---|---|
| `refresh_if_no_data` | 默认策略。policy 检查 `last_pull is None` 时刷新（表从未拉取过）；Provider 层面额外检查：指定日期无数据也会触发刷新 |
| `refresh_calendar_if_outdated` | 日历表最大日期小于今天时刷新 |
| `refresh_every(timedelta(...))` | 距离上次拉取超过指定时间时刷新 |
| `refresh_daily_at(hour, minute)` | 每天过指定时刻后刷新一次（当日不重复） |

#### Bundle 目录结构

```
bundle_package/
├── __init__.py             # 组装 DataBundle + 导出 FactorGroups
├── sources/                # DataSource 定义，按数据内容命名文件
│   ├── __init__.py         # 快速导出所有 DataSource
│   ├── calendar.py         # 交易日历
│   ├── universe.py         # 股票池
│   ├── daily_bar.py        # 日线行情（可选）
│   ├── valuation.py        # 估值数据（可选）
│   ├── financial.py        # 财务数据（可选）
│   ├── sector_mapping.py   # 行业分类（可选）
│   ├── adj_factor.py       # 复权因子（可选）
│   └── ...                  # 其他数据源文件按内容命名
├── factors/                # Factor/FactorGroup 定义（按类型分组）
│   ├── __init__.py         # 快速导出所有 FactorGroups
│   ├── technical.py        # 技术面因子（可选）
│   ├── valuation.py        # 估值因子（可选）
│   └── classification.py   # 行业分类因子（可选）
├── symbol_utils.py         # 代码格式标准化（可选）
└── constants.py            # 常量定义（可选）
```

#### `__init__.py` 组装 — bundle 包的入口

```python
from xs_bundle_xxx.sources import (
    calendar_source,
    universe_source,
    daily_bar_source,
    valuation_source,
)
from xs_bundle_xxx.factors import (
    technical_factors,
    valuation_factors,
    classification_factors,
)

DataBundle = DataBundle(description="xxx market bundle")
DataBundle.add_source(calendar_source)
DataBundle.add_source(universe_source)
DataBundle.add_source(daily_bar_source)
DataBundle.add_source(valuation_source)

FactorGroups = [
    technical_factors,
    valuation_factors,
    classification_factors,
]
```

#### `sources/__init__.py` — 导出所有 DataSource

```python
from .calendar import calendar_source
from .universe import universe_source
from .technical import daily_bar_source
from .valuation import valuation_source
```

#### `factors/__init__.py` — 导出所有 FactorGroups

```python
from .technical import technical_factors
from .valuation import valuation_factors
from .classification import classification_factors
```

### 步骤 5：分析数据并定义因子

数据来源实现完后，分析已有的数据能生成哪些有价值的因子，按类型分组。

#### FactorGroup + Factor 定义规范（放在 `factors/` 下）

```python
# factors/technical.py
from xscreener.core import Factor, FactorGroup

# 在文件顶部导入需要的 DataSource 对象（从 sources 模块导入）
from ..sources.technical import daily_bar_source

technical_factors = FactorGroup("technical", table_name="factor_technical")
```

**跨截面因子**（`lookback=1`，无 compute 时引擎自动按 `factor_id` 在数据源中找列）：

```python
technical_factors.add(Factor(
    factor_id="pe",
    name="PE (TTM)",
    description="市盈率",
))

# 需要简单变换时
technical_factors.add(Factor(
    factor_id="market_cap_yi",
    name="Market Cap (Yi)",
    compute=lambda df: df["market_cap"] / 1e8,
    depends_on=[valuation_source],   # 直接传 DataSource 对象
    value_type=float,
))
```

**时间序列因子**（`lookback > 1`，compute 收到单只股票的跨日期 DataFrame）：

```python
technical_factors.add(Factor(
    factor_id="rsi_14",
    name="RSI(14)",
    lookback=15,
    compute=compute_rsi,
    depends_on=[daily_bar_source],  # 直接传 DataSource 对象
))

def compute_rsi(df: pd.DataFrame) -> pd.Series:
    close = df["close"]
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))
```

**关键规则**：
- `lookback = 窗口大小 + 1`（引擎预读日期范围用）
- `depends_on` 传 **`DataSource` 对象**（不是字符串），从 `..sources` 模块导入
- compute 用 `iloc[-1]` 取最新计算结果
- FactorGroup 实例在模块级别创建，方便 `factors/__init__.py` 统一导出

### 步骤 6：验证

创建测试文件 `tests/test_bundle_<market>.py`，用 MemoryDatabase 验证。

```python
from xscreener import Screener
from xscreener.databases import MemoryDatabase
from xs_bundle_xxx import DataBundle, FactorGroups

screener = Screener(name="Test", db=MemoryDatabase())
screener.add_data_bundle(DataBundle)
for group in FactorGroups:
    screener.add_factor_group(group)
result = screener.screen({...})
```

## 注意事项

- 每完成一步让用户确认，不要一口气全写完
- 步骤 3（验证数据源）必须实际发送网络请求测试，不满足 `output_fields` 就不能进入实现阶段
- 步骤 4（实现 Bundle）时参照已有的 `cn_stock_os_bundle` 中的代码风格
- 所有代码列名用英文
- 确保 DataFrame 格式与 fetch 函数签名匹配
