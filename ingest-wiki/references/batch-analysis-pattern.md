# 批量摄入分析模式参考

## 场景

当 `raw/` 目录下有大量文件（>20个，本例为284个）需要摄入时，手动逐个读取不现实。

## 解决方案：使用 execute_code 批量分析

### 步骤1：分类统计

```python
import os
from collections import defaultdict

raw_dir = "C:/Users/Administrator/Desktop/知识库/<知识库名称>/raw"
files = [f for f in os.listdir(raw_dir) if f.endswith('.md')]

categories = defaultdict(list)
for f in files:
    fname = f.lower()
    # 根据关键词分类
    if any(k in fname for k in ['cpo', '光模块', '光通信']):
        categories['光通信'].append(f)
    elif any(k in fname for k in ['芯片', '半导体']):
        categories['半导体'].append(f)
    # ... 更多分类规则
    else:
        categories['其他'].append(f)

for cat, flist in sorted(categories.items(), key=lambda x: -len(x[1])):
    print(f"{cat}: {len(flist)}个")
```

### 步骤2：识别日期分布

```python
import re

dated_files = []
for f in files:
    # 匹配多种日期格式
    m = re.search(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', f)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        dated_files.append((y, mo, d, f))
    else:
        m2 = re.search(r'(\d{2})月(\d{2})日', f)
        if m2:
            mo, d = int(m2.group(1)), int(m2.group(2))
            dated_files.append((2026, mo, d, f))

dated_files.sort()
# 按月份聚合
monthly = {}
for y, mo, d, f in dated_files:
    key = f"{y}年{mo:02d}月"
    monthly.setdefault(key, []).append(f)
```

### 步骤3：页面组织策略

根据分析结果创建三类页面：

1. **核心概念页面**（按技术领域）
   - 每个分类一个页面
   - 汇总该领域所有文件的要点

2. **行业动态时间线页面**（按月份）
   - 每月一个页面
   - YAML frontmatter 中列出所有来源文件

3. **企业调研/纪要页面**（综合）
   - 汇总所有企业相关文件

## 实际案例

本模式在「人工智能」知识库摄入中验证成功：
- 284个文件 → 16个Wiki页面
- 7个核心概念页面 + 7个月份时间线 + 1个企业调研 + 1个研究方法
- 耗时约15分钟完成全部摄入
