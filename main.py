#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LXMC to CSV Converter
将洛雪音乐(LXMC)格式歌单转换为标准CSV格式
"""

import os
import sys
import json
import time
import zipfile
import gzip
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from collections import defaultdict
import threading

# 设置UTF-8编码以支持Windows环境
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ==================== 配置常量 ====================
VALID_YES = {'1', 'y', 'yes', 't', 'true'}
VALID_NO = {'0', 'n', 'no', 'f', 'false'}
INVALID_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
AUTO_CLOSE_TIMEOUT = 10  # 秒
CSV_HEADER = "Track name,Artist name,Album"
DUPLICATE_DISPLAY_LIMIT = 10  # 重复歌曲显示最大数量


# ==================== 工具函数 ====================

def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    清理文件名和文件夹名，移除不支持的字符
    
    参数:
        filename: 原始文件名
        max_length: 最大长度限制，默认100个字符
    
    返回:
        清理后的文件名
    """
    # 移除不支持的字符
    cleaned = re.sub(INVALID_FILENAME_CHARS, '', filename)
    
    # 如果清理后为空，使用原文件名的6位哈希
    if not cleaned:
        hash_val = hashlib.md5(filename.encode('utf-8')).hexdigest()[:6]
        return f"playlist_{hash_val}"
    
    # 如果超过长度限制，截断并添加8位哈希值
    if len(cleaned) > max_length:
        hash_val = hashlib.md5(cleaned.encode('utf-8')).hexdigest()[:8]
        cleaned = cleaned[:max_length - 9] + f"_{hash_val}"
    
    return cleaned


def get_unique_filename(filepath: str) -> str:
    """
    如果文件已存在，自动在名称中添加_2, _3等后缀
    
    参数:
        filepath: 文件路径
    
    返回:
        唯一的文件路径
    """
    if not os.path.exists(filepath):
        return filepath
    
    path = Path(filepath)
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    
    counter = 2
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return str(new_path)
        counter += 1


def get_unique_dirname(dirpath: str) -> str:
    """
    如果文件夹已存在，自动在名称中添加_2, _3等后缀
    
    参数:
        dirpath: 文件夹路径
    
    返回:
        唯一的文件夹路径
    """
    if not os.path.exists(dirpath):
        return dirpath
    
    counter = 2
    while True:
        new_path = f"{dirpath}_{counter}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def read_user_input(prompt: str, valid_responses: set = None, default: str = None) -> str:
    """
    读取用户输入并验证
    
    参数:
        prompt: 提问文本
        valid_responses: 有效的响应集合，如果为None则接受任意输入
        default: 默认值，用户仅按回车时使用
    
    返回:
        用户的输入（小写）
    
    使用:
        response = read_user_input("是否继续? (y/n): ", {1, y, yes, t, true})
    """
    while True:
        user_input = input(prompt).strip().lower()
        
        if not user_input and default is not None:
            return default
        
        if valid_responses is None or user_input in valid_responses:
            return user_input
        
        print("❌ 输入无效，请重新输入")


def is_yes(response: str) -> bool:
    """
    判断用户输入是否为"是"
    
    参数:
        response: 用户响应
    
    返回:
        True表示是，False表示否
    
    使用:
        if is_yes(read_user_input("是否?")): ...
    """
    return response.lower() in VALID_YES


def is_no(response: str) -> bool:
    """
    判断用户输入是否为"否"
    
    参数:
        response: 用户响应
    
    返回:
        True表示否，False表示是
    """
    return response.lower() in VALID_NO


def print_error(message: str):
    """
    输出错误信息
    
    参数:
        message: 错误信息
    """
    print(f"[ERROR] {message}")


def print_success(message: str):
    """
    输出成功信息
    
    参数:
        message: 成功信息
    """
    print(f"[OK] {message}")


def print_info(message: str):
    """
    输出信息
    
    参数:
        message: 信息内容
    """
    print(f"[INFO] {message}")


def auto_close_with_timeout(timeout: int = AUTO_CLOSE_TIMEOUT):
    """
    若干秒后自动关闭程序（在命令行模式下出错时使用）
    
    参数:
        timeout: 超时秒数，默认10秒
    
    使用:
        print_error("发生错误")
        auto_close_with_timeout()
    """
    print(f"\n程序将在 {timeout} 秒后自动关闭...")
    for i in range(timeout, 0, -1):
        print(f"\r即将关闭: {i} 秒", end='', flush=True)
        time.sleep(1)
    print("\n再见！")
    sys.exit(1)


# ==================== LXMC文件处理模块 ====================

def extract_lxmc(lxmc_path: str) -> Optional[Dict]:
    """
    解压LXMC文件并提取JSON内容
    
    LXMC文件可能是ZIP或GZIP格式的文件，包含JSON歌单数据
    
    参数:
        lxmc_path: LXMC文件路径
    
    返回:
        解析后的JSON字典，如果失败返回None
    
    使用:
        json_data = extract_lxmc("歌单.lxmc")
    """
    try:
        # 先尝试ZIP格式
        try:
            with zipfile.ZipFile(lxmc_path, 'r') as zip_file:
                # 列出ZIP文件中的所有文件
                file_list = zip_file.namelist()
                
                # 查找JSON文件（通常是第一个或唯一的文件）
                json_file = None
                for file in file_list:
                    if file.endswith('.json'):
                        json_file = file
                        break
                
                if not json_file:
                    print_error("LXMC文件中未找到JSON文件")
                    return None
                
                # 提取JSON文件内容
                with zip_file.open(json_file) as f:
                    content = f.read().decode('utf-8')
                    json_data = json.loads(content)
                    return json_data
        except zipfile.BadZipFile:
            # ZIP格式失败，尝试GZIP格式
            with gzip.open(lxmc_path, 'rb') as gz_file:
                content = gz_file.read().decode('utf-8')
                json_data = json.loads(content)
                return json_data
    
    except (zipfile.BadZipFile, EOFError):
        print_error("LXMC文件格式不正确（既不是ZIP也不是GZIP格式）")
        return None
    except json.JSONDecodeError:
        print_error("JSON文件格式有误，无法解析")
        return None
    except Exception as e:
        print_error(f"解压过程中出错: {str(e)}")
        return None


# ==================== JSON验证模块 ====================

def validate_playlist_list(playlist_list: List) -> Tuple[bool, str]:
    """
    验证歌单的歌曲列表是否合法
    
    歌曲列表中每首歌曲必须包含"name"和"singer"字段
    
    参数:
        playlist_list: 歌曲列表
    
    返回:
        (是否合法, 错误信息)
    
    使用:
        valid, msg = validate_playlist_list(songs)
    """
    if not isinstance(playlist_list, list) or len(playlist_list) == 0:
        return False, "歌曲列表为空或格式错误"
    
    for i, song in enumerate(playlist_list):
        if not isinstance(song, dict):
            return False, f"第{i+1}首歌曲不是字典格式"
        
        if 'name' not in song or 'singer' not in song:
            missing = []
            if 'name' not in song:
                missing.append('name')
            if 'singer' not in song:
                missing.append('singer')
            return False, f"第{i+1}首歌曲缺少必需字段: {', '.join(missing)}"
    
    return True, ""


def validate_single_playlist(json_data: Dict) -> Tuple[bool, str, Optional[Dict]]:
    """
    验证单歌单JSON文件格式
    
    单歌单文件结构:
    {
        "type": "playListPart_v2",
        "data": {
            "name": "歌单名",
            "id": "歌单ID",
            "list": [歌曲1, 歌曲2, ...]
        }
    }
    
    参数:
        json_data: 解析后的JSON数据
    
    返回:
        (是否合法, 错误信息, 歌单对象)
    
    使用:
        valid, msg, playlist = validate_single_playlist(json_data)
    """
    # 检查type字段
    if 'type' not in json_data:
        return False, "JSON文件缺少'type'字段", None
    
    # 检查data字段
    if 'data' not in json_data:
        return False, "JSON文件缺少'data'字段，可能只导出了设置或者不是有效的播放列表文件", None
    
    data = json_data.get('data', {})
    
    # 检查必需字段
    if 'name' not in data or 'id' not in data or 'list' not in data:
        missing = []
        if 'name' not in data:
            missing.append('name')
        if 'id' not in data:
            missing.append('id')
        if 'list' not in data:
            missing.append('list')
        return False, f"歌单缺少必需字段: {', '.join(missing)}", None
    
    # 验证歌曲列表
    valid, msg = validate_playlist_list(data.get('list', []))
    if not valid:
        return False, f"歌曲列表验证失败: {msg}", None
    
    return True, "", data


def validate_multi_playlist(json_data: Dict) -> Tuple[bool, str, Optional[List[Dict]]]:
    """
    验证多歌单JSON文件格式
    
    多歌单文件结构:
    {
        "type": "allData_v2",
        "playList": [
            {
                "name": "歌单名",
                "id": "歌单ID",
                "list": [歌曲1, 歌曲2, ...]
            },
            ...
        ]
    }
    
    参数:
        json_data: 解析后的JSON数据
    
    返回:
        (是否合法, 错误信息, 歌单列表)
    
    使用:
        valid, msg, playlists = validate_multi_playlist(json_data)
    """
    # 检查type字段
    if 'type' not in json_data:
        return False, "JSON文件缺少'type'字段", None
    
    # 检查playList字段
    if 'playList' not in json_data:
        return False, "JSON文件缺少'playList'字段，可能只导出了设置或者不是有效的播放列表文件", None
    
    playlists = json_data.get('playList', [])
    
    if not isinstance(playlists, list) or len(playlists) == 0:
        return False, "歌单列表为空或格式错误", None
    
    # 验证每个歌单
    for i, playlist in enumerate(playlists):
        if not isinstance(playlist, dict):
            return False, f"第{i+1}个歌单不是字典格式", None
        
        if 'name' not in playlist or 'id' not in playlist or 'list' not in playlist:
            missing = []
            if 'name' not in playlist:
                missing.append('name')
            if 'id' not in playlist:
                missing.append('id')
            if 'list' not in playlist:
                missing.append('list')
            return False, f"第{i+1}个歌单缺少必需字段: {', '.join(missing)}", None
        
        # 验证歌曲列表
        valid, msg = validate_playlist_list(playlist.get('list', []))
        if not valid:
            return False, f"第{i+1}个歌单('{playlist.get('name')}')的歌曲列表验证失败: {msg}", None
    
    return True, "", playlists


def detect_and_validate_json(json_data: Dict) -> Tuple[str, bool, str, Optional[Union[Dict, List[Dict]]]]:
    """
    检测JSON文件类型并进行验证
    
    参数:
        json_data: 解析后的JSON数据
    
    返回:
        (类型, 是否合法, 错误信息, 歌单数据)
        类型: "single"单歌单, "multi"多歌单, "unknown"未知
    
    使用:
        playlist_type, valid, msg, data = detect_and_validate_json(json_data)
    """
    # 尝试单歌单验证
    valid, msg, data = validate_single_playlist(json_data)
    if valid:
        return "single", True, "", data
    
    # 尝试多歌单验证
    valid, msg, data = validate_multi_playlist(json_data)
    if valid:
        return "multi", True, "", data
    
    # 都不符合
    return "unknown", False, msg, None


# ==================== CSV输出模块 ====================

def extract_album_name(song: Dict) -> str:
    """
    从歌曲字典中提取专辑名称
    
    参数:
        song: 歌曲字典
    
    返回:
        专辑名称，如果不存在则返回空字符串
    
    使用:
        album = extract_album_name(song)
    """
    # 尝试从meta字段获取
    meta = song.get('meta', {})
    if isinstance(meta, dict):
        album = meta.get('albumName', '')
        if album:
            return album
    
    return ''


def export_to_csv(songs: List[Dict], output_path: str) -> Tuple[bool, str]:
    """
    将歌曲列表导出为CSV文件
    
    CSV格式:
    第一行: "Track name,Artist name,Album"
    其后每行: 歌曲名,艺人名,专辑名
    
    参数:
        songs: 歌曲列表
        output_path: 输出CSV文件路径
    
    返回:
        (是否成功, 信息)
    
    使用:
        success, msg = export_to_csv(songs, "output.csv")
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            # 写入标题行
            f.write(CSV_HEADER + '\n')
            
            # 写入每首歌曲
            for song in songs:
                name = song.get('name', '').replace(',', '，')  # 避免逗号破坏CSV格式
                singer = song.get('singer', '').replace(',', '，')
                album = extract_album_name(song).replace(',', '，')
                
                # 处理可能包含换行符的字段
                name = name.replace('\n', '').replace('\r', '')
                singer = singer.replace('\n', '').replace('\r', '')
                album = album.replace('\n', '').replace('\r', '')
                
                f.write(f"{name},{singer},{album}\n")
        
        return True, f"成功导出到: {output_path}"
    
    except Exception as e:
        return False, f"导出CSV时出错: {str(e)}"


# ==================== 去重和重复检测模块 ====================

def find_duplicates(songs: List[Dict]) -> Dict[str, int]:
    """
    查找歌单中的重复歌曲
    
    三个字段完全相同的歌曲视为重复: name, singer, album
    
    参数:
        songs: 歌曲列表
    
    返回:
        字典，键为"name|singer|album"，值为出现次数
    
    使用:
        duplicates = find_duplicates(songs)
    """
    song_key_count = defaultdict(int)
    
    for song in songs:
        name = song.get('name', '')
        singer = song.get('singer', '')
        album = extract_album_name(song)
        key = f"{name}|{singer}|{album}"
        song_key_count[key] += 1
    
    # 过滤出出现次数>1的歌曲
    duplicates = {k: v for k, v in song_key_count.items() if v > 1}
    return duplicates


def remove_duplicates(songs: List[Dict]) -> List[Dict]:
    """
    移除歌单中的重复歌曲，保留第一次出现的版本
    
    参数:
        songs: 歌曲列表
    
    返回:
        去重后的歌曲列表
    
    使用:
        unique_songs = remove_duplicates(songs)
    """
    seen = set()
    unique_songs = []
    
    for song in songs:
        name = song.get('name', '')
        singer = song.get('singer', '')
        album = extract_album_name(song)
        key = f"{name}|{singer}|{album}"
        
        if key not in seen:
            seen.add(key)
            unique_songs.append(song)
    
    return unique_songs


def display_duplicates(duplicates: Dict[str, int], limit: int = DUPLICATE_DISPLAY_LIMIT):
    """
    展示重复歌曲列表
    
    参数:
        duplicates: 重复歌曲字典（来自find_duplicates）
        limit: 显示的最大数量，超出部分提示用户
    
    使用:
        display_duplicates(duplicates, limit=10)
    """
    if not duplicates:
        return
    
    print("\n发现重复歌曲:")
    for i, (key, count) in enumerate(duplicates.items()):
        if i >= limit:
            remaining = len(duplicates) - limit
            print(f"... 还有 {remaining} 首重复歌曲")
            print(f"💡 提示: 可以选择输出重复歌曲列表到文本文件以便查看所有重复项")
            break
        
        parts = key.split('|')
        name = parts[0]
        singer = parts[1]
        album = parts[2] if len(parts) > 2 else ''
        
        print(f"  {i+1}. 《{name}》 - {singer}" + (f" - {album}" if album else ""))


def display_duplicates_with_playlist(playlists: List[Dict], duplicates_per_playlist: Dict[str, Dict], limit: int = DUPLICATE_DISPLAY_LIMIT):
    """
    展示多个歌单的重复歌曲列表，包括所属歌单信息
    
    参数:
        playlists: 歌单列表
        duplicates_per_playlist: 字典，键为歌单名_ID，值为该歌单的重复歌曲字典
        limit: 显示的最大数量
    
    使用:
        display_duplicates_with_playlist(playlists, duplicates_dict)
    """
    total_duplicates = sum(len(d) for d in duplicates_per_playlist.values())
    if total_duplicates == 0:
        return
    
    print("\n发现重复歌曲:")
    count = 0
    for playlist in playlists:
        playlist_key = f"{playlist['name']}_{playlist['id']}"
        if playlist_key not in duplicates_per_playlist:
            continue
        
        duplicates = duplicates_per_playlist[playlist_key]
        if not duplicates:
            continue
        
        print(f"\n歌单《{playlist['name']}》({playlist['id']}):")
        for key, dup_count in duplicates.items():
            if count >= limit:
                remaining = total_duplicates - limit
                print(f"... 还有 {remaining} 首重复歌曲")
                print(f"💡 提示: 可以选择输出重复歌曲列表到文本文件以便查看所有重复项")
                return
            
            parts = key.split('|')
            name = parts[0]
            singer = parts[1]
            album = parts[2] if len(parts) > 2 else ''
            
            print(f"  {count+1}. 《{name}》 - {singer}" + (f" - {album}" if album else ""))
            count += 1


# ==================== 交互式UI模块 ====================

def interactive_mode():
    """
    交互式UI主函数
    
    引导用户:
    1. 选择LXMC文件
    2. 验证文件格式
    3. 选择歌单（如果有多个）
    4. 配置去重选项
    5. 输出CSV文件
    
    使用:
        interactive_mode()
    """
    print("\n" + "="*50)
    print("      洛雪音乐歌单转CSV转换工具")
    print("="*50 + "\n")
    
    # 步骤1: 选择文件
    while True:
        lxmc_path = input("请输入LXMC文件路径: ").strip()
        
        if not lxmc_path:
            print_error("路径不能为空")
            continue
        
        # 移除引号（如果用户复制粘贴时包含）
        lxmc_path = lxmc_path.strip('"\'')
        
        if not os.path.exists(lxmc_path):
            print_error(f"文件不存在: {lxmc_path}")
            continue
        
        if not lxmc_path.lower().endswith('.lxmc'):
            print_error("文件必须是.lxmc格式")
            continue
        
        break
    
    # 步骤2: 解压并验证
    print_info("正在解压并验证文件...")
    json_data = extract_lxmc(lxmc_path)
    if json_data is None:
        print_error("无法解压LXMC文件，请检查文件是否有效")
        return
    
    playlist_type, valid, error_msg, data = detect_and_validate_json(json_data)
    
    if not valid:
        print_error(f"JSON验证失败: {error_msg}")
        print_error("请确认您选择的文件是否正确（可能导出的是设置或其他无效文件）")
        return
    
    print_success("文件验证成功")
    
    # 步骤3: 处理单/多歌单
    if playlist_type == "single":
        playlist = data
        playlists = [playlist]
        selected_playlists = playlists
        is_multi = False
    else:  # multi
        playlists = data
        is_multi = True
        
        # 询问用户是否导出所有歌单
        print(f"\n检测到 {len(playlists)} 个歌单:")
        for i, pl in enumerate(playlists):
            print(f"  {i+1}. {pl['name']} (ID: {pl['id']}) - {len(pl['list'])} 首歌曲")
        
        print("\n选项:")
        print("  1. 导出所有歌单（创建文件夹存放）")
        print("  2. 选择导出某个歌单")
        
        while True:
            choice = read_user_input("\n请选择 (1-2): ", {'1', '2'})
            if choice in {'1', '2'}:
                break
            print_error("请输入1或2")
        
        if choice == '1':
            selected_playlists = playlists
        else:  # choice == '2'
            print("\n请输入要导出的歌单序号:")
            while True:
                try:
                    choice_idx = int(input(f"请选择 (1-{len(playlists)}): "))
                    if 1 <= choice_idx <= len(playlists):
                        selected_playlists = [playlists[choice_idx - 1]]
                        break
                    else:
                        print_error(f"请输入1-{len(playlists)}之间的数字")
                except ValueError:
                    print_error("请输入有效的数字")
    
    # 步骤4: 检查选中歌单的合法性
    print_info("正在检查歌单合法性...")
    valid_playlists = []
    invalid_playlists = []
    
    for playlist in selected_playlists:
        valid, msg = validate_playlist_list(playlist.get('list', []))
        if valid:
            valid_playlists.append(playlist)
        else:
            invalid_playlists.append((playlist, msg))
    
    # 如果有不合法的歌单
    if invalid_playlists:
        if len(selected_playlists) == 1:
            # 只有一个歌单且不合法
            print_error(f"歌单不合法: {invalid_playlists[0][1]}")
            return
        else:
            # 多个歌单，列出合法和不合法的
            print("\n歌单验证结果:")
            print(f"✅ 合法的歌单: {len(valid_playlists)} 个")
            for pl in valid_playlists:
                print(f"   - {pl['name']} ({len(pl['list'])} 首)")
            
            print(f"❌ 不合法的歌单: {len(invalid_playlists)} 个")
            for pl, msg in invalid_playlists:
                print(f"   - {pl['name']}: {msg}")
            
            print("\n注意: 不合法的歌单无法导出")
            
            # 询问是否继续
            response = read_user_input("是否继续导出合法的歌单? (y/n) [默认n]: ", 
                                     VALID_YES | VALID_NO, 'n')
            
            if not is_yes(response):
                print_error("已取消导出")
                return
            
            selected_playlists = valid_playlists
            
            if not selected_playlists:
                print_error("没有合法的歌单可导出")
                return
    
    # 步骤5: 处理去重
    print("\n去重选项:")
    need_dedup = False
    duplicate_info = {}
    
    for playlist in selected_playlists:
        duplicates = find_duplicates(playlist['list'])
        if duplicates:
            need_dedup = True
            playlist_key = f"{playlist['name']}_{playlist['id']}"
            duplicate_info[playlist_key] = duplicates
    
    if need_dedup:
        if len(selected_playlists) == 1:
            display_duplicates(duplicate_info[list(duplicate_info.keys())[0]])
        else:
            display_duplicates_with_playlist(selected_playlists, duplicate_info)
        
        response = read_user_input("\n是否去除重复歌曲? (y/n) [默认n]: ", 
                                 VALID_YES | VALID_NO, 'n')
        
        if is_yes(response):
            for playlist in selected_playlists:
                playlist['list'] = remove_duplicates(playlist['list'])
            print_success("已去除重复歌曲")
        
        # 询问是否输出重复歌曲列表
        response = read_user_input("是否输出重复歌曲列表到文本文件? (y/n) [默认n]: ", 
                                 VALID_YES | VALID_NO, 'n')
        if is_yes(response):
            output_duplicate_list(selected_playlists, duplicate_info, lxmc_path)
    
    # 步骤6: 输出CSV
    print("\n正在导出CSV文件...")
    
    if len(selected_playlists) == 1:
        # 单个歌单，直接导出
        playlist = selected_playlists[0]
        playlist_name = sanitize_filename(f"{playlist['name']}_{playlist['id']}")
        output_path = get_unique_filename(
            os.path.join(os.path.dirname(lxmc_path), f"{playlist_name}.csv")
        )
        
        success, msg = export_to_csv(playlist['list'], output_path)
        if success:
            print_success(msg)
        else:
            print_error(msg)
    else:
        # 多个歌单，创建文件夹
        lxmc_name = os.path.splitext(os.path.basename(lxmc_path))[0]
        output_dir = get_unique_dirname(
            os.path.join(os.path.dirname(lxmc_path), sanitize_filename(lxmc_name))
        )
        os.makedirs(output_dir, exist_ok=True)
        
        for playlist in selected_playlists:
            playlist_name = sanitize_filename(f"{playlist['name']}_{playlist['id']}")
            output_path = get_unique_filename(
                os.path.join(output_dir, f"{playlist_name}.csv")
            )
            
            success, msg = export_to_csv(playlist['list'], output_path)
            if success:
                print_success(f"导出: {os.path.basename(output_path)}")
            else:
                print_error(f"导出 {playlist['name']} 失败: {msg}")
    

    # 按任意键退出
    input("\n✅ 所有操作完成，按任意键退出...")


def output_duplicate_list(playlists: List[Dict], duplicate_info: Dict, lxmc_path: str):
    """
    将重复歌曲列表输出到文本文件
    
    参数:
        playlists: 歌单列表
        duplicate_info: 重复歌曲信息字典
        lxmc_path: 原LXMC文件路径
    
    使用:
        output_duplicate_list(playlists, duplicate_info, lxmc_path)
    """
    try:
        output_file = get_unique_filename(
            os.path.join(os.path.dirname(lxmc_path), 
                        f"{os.path.splitext(os.path.basename(lxmc_path))[0]}_重复歌曲.txt")
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for playlist in playlists:
                playlist_key = f"{playlist['name']}_{playlist['id']}"
                
                if playlist_key not in duplicate_info:
                    continue
                
                duplicates = duplicate_info[playlist_key]
                if not duplicates:
                    continue
                
                f.write(f"\n歌单: {playlist['name']} (ID: {playlist['id']})\n")
                f.write("=" * 60 + "\n")
                
                for i, (key, count) in enumerate(duplicates.items()):
                    parts = key.split('|')
                    name = parts[0]
                    singer = parts[1]
                    album = parts[2] if len(parts) > 2 else ''
                    
                    f.write(f"{i+1}. 《{name}》 - {singer}")
                    if album:
                        f.write(f" - {album}")
                    f.write(f" (出现 {count} 次)\n")
        
        print_success(f"重复歌曲列表已输出: {output_file}")
    
    except Exception as e:
        print_error(f"输出重复列表失败: {str(e)}")


# ==================== 命令行直接参数模式 ====================

def command_line_mode(lxmc_path: str):
    """
    命令行直接参数模式
    
    使用方式: python main.py input.lxmc
    
    参数:
        lxmc_path: LXMC文件路径
    
    特点:
    - 所有设置保持默认值
    - 多歌单时输出全部歌单到文件夹
    - 去重时默认保留
    - 不输出重复歌曲列表
    
    使用:
        command_line_mode("歌单.lxmc")
    """
    print(f"正在处理: {lxmc_path}")
    
    # 验证文件存在
    if not os.path.exists(lxmc_path):
        print_error(f"文件不存在: {lxmc_path}")
        auto_close_with_timeout()
        return
    
    if not lxmc_path.lower().endswith('.lxmc'):
        print_error("文件必须是.lxmc格式")
        auto_close_with_timeout()
        return
    
    # 解压并验证
    json_data = extract_lxmc(lxmc_path)
    if json_data is None:
        print_error("无法解压LXMC文件")
        auto_close_with_timeout()
        return
    
    playlist_type, valid, error_msg, data = detect_and_validate_json(json_data)
    
    if not valid:
        print_error(f"文件验证失败: {error_msg}")
        auto_close_with_timeout()
        return
    
    # 准备导出
    if playlist_type == "single":
        playlists = [data]
    else:
        playlists = data
    
    # 检查歌单合法性
    valid_playlists = []
    for playlist in playlists:
        valid, _ = validate_playlist_list(playlist.get('list', []))
        if valid:
            valid_playlists.append(playlist)
    
    if not valid_playlists:
        print_error("所有歌单都不合法，请检查文件")
        auto_close_with_timeout()
        return
    
    # 去重（默认保留）
    # 这里不主动去重，使用原始数据
    
    # 导出
    if len(valid_playlists) == 1:
        # 单个歌单
        playlist = valid_playlists[0]
        playlist_name = sanitize_filename(f"{playlist['name']}_{playlist['id']}")
        output_path = get_unique_filename(
            os.path.join(os.path.dirname(lxmc_path), f"{playlist_name}.csv")
        )
        
        success, msg = export_to_csv(playlist['list'], output_path)
        if success:
            print_success(msg)
        else:
            print_error(msg)
            auto_close_with_timeout()
            return
    else:
        # 多个歌单
        lxmc_name = os.path.splitext(os.path.basename(lxmc_path))[0]
        output_dir = get_unique_dirname(
            os.path.join(os.path.dirname(lxmc_path), sanitize_filename(lxmc_name))
        )
        os.makedirs(output_dir, exist_ok=True)
        
        for playlist in valid_playlists:
            playlist_name = sanitize_filename(f"{playlist['name']}_{playlist['id']}")
            output_path = get_unique_filename(
                os.path.join(output_dir, f"{playlist_name}.csv")
            )
            
            success, msg = export_to_csv(playlist['list'], output_path)
            if success:
                print_success(f"导出: {os.path.basename(output_path)}")
            else:
                print_error(f"导出 {playlist['name']} 失败: {msg}")
                auto_close_with_timeout()
                return
    
    print_success("所有歌单转换完成！")
    # print("✅ 所有操作完成，程序将在2秒后退出...")
    # time.sleep(2)
    auto_close_with_timeout()


# ==================== 主函数 ====================

def main():
    """
    程序主函数
    
    逻辑:
    1. 检查命令行参数
    2. 如果有参数，使用命令行模式（直接参数）
    3. 如果没有参数，使用交互式模式
    
    使用:
        python main.py                    # 交互式UI模式
        python main.py input.lxmc         # 命令行直接参数模式
    """
    if len(sys.argv) > 1:
        # 命令行直接参数模式
        lxmc_path = sys.argv[1]
        command_line_mode(lxmc_path)
    else:
        # 交互式UI模式
        try:
            interactive_mode()
        except KeyboardInterrupt:
            print("\n\n已取消操作")
            sys.exit(0)
        except Exception as e:
            print_error(f"程序发生未预期的错误: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
