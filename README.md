# LXMC to CSV Converter - 洛雪音乐歌单转CSV工具

> 🎵 将洛雪音乐(LXMC)格式的歌单导出文件转换为标准CSV格式的开源工具

![License](https://img.shields.io/badge/license-GPL--3.0-green)
![Python](https://img.shields.io/badge/Python-3.6+-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

---

## ⚠️ 声明

**本项目100%由AI编写，包括此README文档。使用本项目产生的任何问题与作者无关，请自行承担风险。**

### 🔴 **数据无价，谨慎操作**

**使用前请先备份重要歌单数据！**

---

## 📝 项目初衷

本项目用来帮助用户在各种音乐平台间**迁移和转换歌单**。

### 🎯 使用建议

1. **优先使用原平台导入功能**：大多数新音乐平台支持从其他平台直接导入歌单（如Spotify支持导入Apple Music、YouTube Music等）
   - 这种方式最准确，匹配度最高

2. **使用本工具查漏补缺**：
   - 在导入过程中难免有部分歌曲无法匹配
   - 使用此工具将歌单转换为CSV格式，手动补充缺失的歌曲
   - 或者进一步转移到其他平台

---

## 🚀 快速开始

### 方式1️⃣：下载EXE文件（Windows用户推荐）

1. 在 [Releases](https://github.com/bukall/lxmc2csv/releases) 中下载最新的 `lxmc2csv.exe` 文件
2. 将您的LXMC文件拖动到exe文件上
3. **自动完成转换**，输出CSV文件到同目录

✅ **优点**：无需安装Python，一拖一放，可视化操作
❌ **缺点**：仅支持Windows，功能有限（使用默认配置）

---

### 方式2️⃣：Python命令行（推荐用于更多功能）

#### 安装

```bash
# 克隆项目
git clone https://github.com/bukall/lxmc2csv.git
cd lxmc2csv

# 确保已安装Python 3.6+
python --version
```

#### 快速模式（推荐日常使用）

```bash
# 直接拖拽LXMC文件到命令行，或者输入文件路径
python main.py input.lxmc

# 自动输出到同目录
# output.csv 或 output/ (多歌单时)
```

**此模式的特点**：
- ✅ 快速高效，一条命令完成
- ✅ 所有参数使用默认值
- ✅ 多歌单时自动创建文件夹
- ✅ 出错时10秒后自动关闭

#### 交互式模式（更多控制）

```bash
# 不提供任何参数
python main.py

# 按照提示完成以下步骤：
# 1️⃣  选择LXMC文件（支持拖拽文件或输入路径）
# 2️⃣  选择导出方式（单个歌单或全部导出）
# 3️⃣  检查歌单合法性
# 4️⃣  配置重复歌曲处理
# 5️⃣  查看处理结果并导出
```

**此模式的特点**：
- 🎛️ 完整的交互式界面
- 📊 详细的歌单信息展示
- 🔍 重复歌曲检测与去重选项
- 💾 可选输出重复歌曲列表
- ⚙️ 更多自定义选项

---

## 📚 使用示例

### 示例：从酷我音乐迁移歌单到Spotify

本示例展示如何使用本工具将酷我音乐的歌单迁移到Spotify。

#### 第1步：在酷我音乐获取歌单链接或ID
#### 第2步：在洛雪音乐导入歌单
#### 第3步：在洛雪音乐导出LXMC格式歌单文件
#### 第4步：使用本工具转换为CSV格式
#### 第5步：在 [tunemymusic](www.tunemymusic.com) 上传CSV格式的歌单文件转移到Spotify

---

## 🔌 编程接口（API）

除了命令行工具外，本项目也可作为Python模块被其他程序调用。

### 导入模块

```python
from main import (
    extract_lxmc,
    detect_and_validate_json,
    find_duplicates,
    remove_duplicates,
    export_to_csv,
    sanitize_filename,
    get_unique_filename
)
```

### API 文档

#### 1. 解压LXMC文件

```python
def extract_lxmc(lxmc_path: str) -> Optional[Dict]:
    """
    解压LXMC文件并提取JSON内容
    
    参数：
        lxmc_path (str): LXMC文件的完整路径
        
    返回：
        Dict: 解析后的JSON字典
        None: 如果解压失败
        
    异常：
        - LXMC文件损坏
        - 文件不存在
        - JSON格式错误
        
    示例：
        >>> json_data = extract_lxmc("my_playlist.lxmc")
        >>> print(json_data['type'])
        'playListPart_v2'
    """
```

**使用示例**：
```python
# 将LXMC格式的歌单文件转换为JSON格式
json_data = extract_lxmc("my_playlist.lxmc")

# 直接输出JSON内容
import json
print(json.dumps(json_data, indent=2, ensure_ascii=False))

# 或者保存到文件
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)
```

#### 2. 验证和检测JSON类型

```python
def detect_and_validate_json(json_data: Dict) -> Tuple[str, bool, str, Union[Dict, List[Dict]]]:
    """
    检测JSON文件类型并进行验证
    
    参数：
        json_data (Dict): 解析后的JSON数据
        
    返回：
        Tuple[str, bool, str, Union]: 
        - str: 类型 ("single"单歌单, "multi"多歌单, "unknown"未知)
        - bool: 是否合法
        - str: 错误信息（当不合法时）
        - Union: 歌单数据（当合法时）
        
    示例：
        >>> playlist_type, valid, error, data = detect_and_validate_json(json_data)
        >>> if valid:
        ...     print(f"找到{len(data)}首歌曲")
    """
```

#### 3. 查找重复歌曲

```python
def find_duplicates(songs: List[Dict]) -> Dict[str, int]:
    """
    查找歌单中的重复歌曲
    
    参数：
        songs (List[Dict]): 歌曲列表
        
    返回：
        Dict: 重复歌曲字典
        - 键: "歌曲名|艺术家|专辑"
        - 值: 出现次数
        
    判重标准：
        歌曲名、艺术家、专辑三个字段完全相同
        
    示例：
        >>> duplicates = find_duplicates(playlist['list'])
        >>> for key, count in duplicates.items():
        ...     print(f"{key} 出现了 {count} 次")
    """
```

#### 4. 去除重复歌曲

```python
def remove_duplicates(songs: List[Dict]) -> List[Dict]:
    """
    从歌单中去除重复歌曲
    
    参数：
        songs (List[Dict]): 歌曲列表
        
    返回：
        List[Dict]: 去重后的歌曲列表（保留首次出现）
        
    示例：
        >>> unique_songs = remove_duplicates(playlist['list'])
        >>> print(f"删除了 {len(playlist['list']) - len(unique_songs)} 首重复")
    """
```

#### 5. 导出为CSV

```python
def export_to_csv(songs: List[Dict], output_path: str) -> Tuple[bool, str]:
    """
    将歌曲列表导出为CSV文件
    
    参数：
        songs (List[Dict]): 歌曲列表
        output_path (str): 输出CSV文件路径
        
    返回：
        Tuple[bool, str]:
        - bool: 是否成功
        - str: 成功/失败信息
        
    CSV格式：
        第1行: Track name,Artist name,Album
        后续行: 歌曲名,艺术家,专辑
        编码: UTF-8
        
    示例：
        >>> success, msg = export_to_csv(songs, "output.csv")
        >>> if success:
        ...     print(msg)
    """
```

#### 6. 清理文件名

```python
def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    清理文件名中的非法字符
    
    参数：
        filename (str): 原始文件名
        max_length (int): 最大长度（默认100字符）
        
    返回：
        str: 清理后的合法文件名
        
    清理规则：
        1. 移除非法字符: < > : " / \\ | ? * 和ASCII控制字符
        2. 如果清理后为空: 使用文件名的6位MD5哈希
        3. 如果超过max_length: 截断+8位哈希值
        
    示例：
        >>> sanitize_filename("我的<>歌单:2024\\/")
        '我的歌单2024'
        
        >>> sanitize_filename("这是一个非常非常长的歌单名称" * 10)
        '这是一个非常非常长的歌单名称这是一个非常非常长的歌单_a1b2c3d4'
    """
```

#### 7. 处理文件名冲突

```python
def get_unique_filename(filepath: str) -> str:
    """
    如果文件已存在，自动生成新的唯一文件名
    
    参数：
        filepath (str): 目标文件路径
        
    返回：
        str: 唯一的文件路径（添加_2、_3等后缀）
        
    示例：
        >>> get_unique_filename("output.csv")
        'output.csv'  # 不存在时
        
        >>> get_unique_filename("output.csv")
        'output_2.csv'  # 当output.csv已存在时
    """
```

### 完整编程示例

#### 示例1：转换LXMC为JSON

```python
from main import extract_lxmc
import json

# 解压并提取JSON
lxmc_file = "my_playlist.lxmc"
json_data = extract_lxmc(lxmc_file)

if json_data:
    # 保存为JSON文件
    output_json = "my_playlist.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"✓ 已转换为 {output_json}")
else:
    print("✗ 转换失败")
```

#### 示例2：批量处理多个LXMC文件

```python
from main import extract_lxmc, detect_and_validate_json, export_to_csv
import glob

# 处理目录中所有LXMC文件
for lxmc_file in glob.glob("*.lxmc"):
    print(f"处理: {lxmc_file}")
    
    # 提取JSON
    json_data = extract_lxmc(lxmc_file)
    if not json_data:
        print(f"  ✗ 无法解压")
        continue
    
    # 验证JSON
    playlist_type, valid, error, data = detect_and_validate_json(json_data)
    if not valid:
        print(f"  ✗ 验证失败: {error}")
        continue
    
    # 处理不同类型的歌单
    if playlist_type == "single":
        playlists = [data]
    else:
        playlists = data
    
    # 导出CSV
    for playlist in playlists:
        output_csv = f"{playlist['name']}_{playlist['id']}.csv"
        success, msg = export_to_csv(playlist['list'], output_csv)
        if success:
            print(f"  ✓ {output_csv}")
        else:
            print(f"  ✗ {msg}")
```

#### 示例3：检测和处理重复歌曲

```python
from main import extract_lxmc, detect_and_validate_json, find_duplicates, remove_duplicates

# 解压并验证
json_data = extract_lxmc("playlist.lxmc")
playlist_type, valid, error, data = detect_and_validate_json(json_data)

if valid and playlist_type == "single":
    songs = data['list']
    
    # 查找重复
    duplicates = find_duplicates(songs)
    if duplicates:
        print(f"发现 {len(duplicates)} 种重复歌曲:")
        for key, count in duplicates.items():
            song_name, artist, album = key.split('|')
            print(f"  《{song_name}》- {artist} (出现{count}次)")
        
        # 去重
        unique_songs = remove_duplicates(songs)
        print(f"\n去重后: {len(songs)} -> {len(unique_songs)} 首")
    else:
        print("没有发现重复歌曲")
```

#### 示例4：自定义CSV导出格式

```python
from main import extract_lxmc, detect_and_validate_json

# 获取歌单数据
json_data = extract_lxmc("playlist.lxmc")
_, valid, _, data = detect_and_validate_json(json_data)

if valid and isinstance(data, dict):
    songs = data['list']
    
    # 自定义导出格式（例如：包含歌曲ID）
    with open("custom_output.csv", "w", encoding="utf-8") as f:
        # 自定义标题
        f.write("ID,Track,Artist,Album\n")
        
        # 写入数据
        for song in songs:
            song_id = song.get('id', '')
            name = song.get('name', '').replace(',', '，')
            artist = song.get('singer', '').replace(',', '，')
            album = song.get('meta', {}).get('albumName', '').replace(',', '，')
            
            f.write(f'{song_id},{name},{artist},{album}\n')
    
    print("✓ 自定义CSV已生成")
```

---

## 📋 支持的文件格式

### 输入格式

**LXMC文件** - 洛雪音乐导出的歌单文件
- 实际上是GZIP或ZIP压缩的JSON文件
- 包含歌曲元数据（名称、艺术家、专辑等）
- 支持单歌单和多歌单格式

### 输出格式

**CSV文件** - 逗号分隔值格式
- 标准格式：`Track name,Artist name,Album`
- UTF-8编码，兼容Excel和Google Sheets
- 可被大多数音乐转移服务识别

---

## 🔍 功能特性

### 核心功能

- ✅ **LXMC文件解压**：支持ZIP和GZIP两种压缩格式
- ✅ **格式验证**：自动检测单/多歌单并进行合法性检查
- ✅ **重复检测**：智能识别相同的歌曲（基于名称、艺术家、专辑）
- ✅ **去重处理**：可选保留或删除重复歌曲
- ✅ **CSV导出**：标准化格式，兼容所有平台
- ✅ **文件清理**：自动处理非法字符和文件名冲突
- ✅ **多语言支持**：完美处理中文、日文等多字节字符

### 安全特性

- 🔒 **只读操作**：不修改原始LXMC文件
- 🔒 **UTF-8编码**：防止字符编码问题
- 🔒 **错误恢复**：详细的错误提示和日志

### 易用性

- 🎯 **快速模式**：一条命令完成转换
- 🎯 **交互模式**：通过菜单引导完成所有操作
- 🎯 **EXE版本**：无需Python环境，拖拽即用
- 🎯 **API接口**：可作为模块集成到其他程序

---

## 📊 工作流程

```
输入 LXMC 文件
    ↓
[解压] GZIP/ZIP → JSON
    ↓
[验证] 检查JSON格式和必需字段
    ↓
[检测] 区分单歌单/多歌单
    ↓
[选择] 用户选择处理方式（仅交互模式）
    ↓
[检查] 验证歌曲列表合法性
    ↓
[重复] 检测并处理重复歌曲（仅交互模式）
    ↓
[转换] 转换为CSV格式
    ↓
[输出] 保存CSV文件
    ↓
完成 ✓
```

---

## 🛠️ 技术细节

### 系统要求

- **Python版本**：3.6 或更高
- **操作系统**：Windows / macOS / Linux
- **依赖项**：无（仅使用Python标准库）

### 文件结构

```
lxmc2csv/
├── main.py              # 主程序（所有功能集中）
├── README.md            # 项目文档
├── requirements.txt     # 依赖说明（实际为空）
└── build_exe.py         # EXE构建脚本（可选）
```

### 核心算法

**重复检测**：
```
对每首歌曲生成唯一键: "歌曲名|艺术家|专辑"
统计键的出现次数
次数 > 1 的即为重复歌曲
```

**文件名清理**：
```
1. 移除非法字符 (< > : " / \ | ? * 等)
2. 如果为空 → 使用6位MD5哈希
3. 如果超长 → 截断+8位哈希值
4. 如果已存在 → 添加_2, _3等后缀
```

---

## 📦 下载和使用

### 方式1：直接下载源代码

```bash
git clone https://github.com/bukall/lxmc2csv.git
cd lxmc2csv
python main.py
```

### 方式2：下载打包的EXE文件

前往 [Releases](https://github.com/bukall/lxmc2csv/releases) 页面下载最新的 `lxmc2csv.exe`

```
将LXMC文件拖拽到exe文件上 → 自动生成CSV
```

---

## 📝 常见问题

**Q: 支持哪些格式的导入？**
A: 目前仅支持洛雪音乐导出的LXMC格式

**Q: 支持哪些格式的导出？**
A: 目前仅支持导出为csv格式 包含歌曲名称、艺术家和专辑信息

**Q: 转换过程中会修改原始文件吗？**
A: 不会。本工具只读取原文件，不做任何修改

**Q: 可以处理有多少首歌的歌单？**
A: 理论上没有限制，但实际受限于内存大小。

**Q: CSV文件可以直接导入Spotify吗？**
A: 不能直接导入。需要通过第三方服务如TuneMyMusic转移
  
**Q: 为什么有些歌曲转移失败了？**
A: 可能的原因：
   - 歌曲在目标平台下架
   - 歌手名称或歌曲名称不匹配
   - 目标平台没有该歌曲版本

**Q: 支持批量处理吗？**
A: 可以。通过API接口，编写Python脚本实现批量处理

---

## 📄 许可证

本项目采用 **GPL-3.0许可证**

> GPL-3.0是自由软件许可证，允许：
> - ✅ 自由使用和修改
> - ✅ 发布修改版本
> - ❌ 但必须公开源代码
> - ❌ 不能用于闭源项目

详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- 感谢洛雪音乐提供便利的歌单导出功能
