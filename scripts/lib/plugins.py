"""插件解析与安装。

迁移自 scripts/plugin-manager.py：
- load_plugin_config / validate_plugin_config / update_env_file / update_mcp_template
- run_plugin_scripts / install_skills / install_plugin / list_plugins
- load_skills_mapping / generate_plugin_from_csv / list_skills_from_csv

依赖：
- lib.config_io: load_env_config_file / save_env_config_file
- lib.skills: install_skill
- lib.logging: 颜色常量

parse_shorthand / build_install_command / install_skill 已迁移到 lib/skills.py，
本模块通过 from lib.skills import install_skill 复用。
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

from lib.logging import (
    COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, COLOR_RED, COLOR_DARKGRAY,
    COLOR_MAGENTA, COLOR_WHITE, COLOR_RESET,
)
from lib.config_io import load_env_config_file, save_env_config_file
from lib.skills import install_skill


# ============================================================
# 插件配置解析
# ============================================================

def load_plugin_config(plugin_path: Path) -> dict:
    """加载插件配置文件"""
    if not plugin_path.exists():
        print(f"{COLOR_RED}[!] 插件文件不存在: {plugin_path}{COLOR_RESET}", file=sys.stderr)
        sys.exit(1)

    with open(plugin_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_plugin_config(config: dict) -> bool:
    """验证插件配置格式"""
    required_fields = ["name", "version"]
    for field in required_fields:
        if field not in config:
            print(f"{COLOR_RED}[!] 缺少必需字段: {field}{COLOR_RESET}", file=sys.stderr)
            return False
    return True


def update_env_file(env_path: Path, plugin_config: dict) -> None:
    """更新环境变量文件"""
    if "envVars" not in plugin_config:
        return

    if not env_path.exists():
        print(f"{COLOR_YELLOW}[!] 环境变量文件不存在，创建新文件: {env_path}{COLOR_RESET}")
        env_config = {}
    else:
        env_config = load_env_config_file(env_path)

    # 更新环境变量
    updated = False
    for var_name, var_info in plugin_config["envVars"].items():
        if var_name not in env_config:
            default_value = var_info.get("default", "")
            env_config[var_name] = default_value
            print(f"{COLOR_YELLOW}[~] 添加环境变量: {var_name} = {default_value}{COLOR_RESET}")
            print(f"    描述: {var_info.get('description', '')}")
            updated = True
        else:
            print(f"{COLOR_DARKGRAY}[~] 环境变量已存在: {var_name}{COLOR_RESET}")

    if updated:
        env_path.parent.mkdir(parents=True, exist_ok=True)
        save_env_config_file(env_path, env_config)
        print(f"{COLOR_GREEN}[OK] 环境变量文件已更新: {env_path}{COLOR_RESET}")


def update_mcp_template(mcp_template_path: Path, plugin_config: dict) -> None:
    """更新 MCP 配置（mcp.yaml，统一存放 mcpServers + mcp 密钥）。
    mcp_template_path 现指 mcp.yaml；保留 mcp 密钥段，仅合并 mcpServers。"""
    if "mcpServers" not in plugin_config:
        return

    if not mcp_template_path.exists():
        print(f"{COLOR_YELLOW}[!] MCP配置文件不存在，创建新文件: {mcp_template_path}{COLOR_RESET}")
        mcp_config = {"mcpServers": {}, "mcp": {}}
    else:
        mcp_config = load_env_config_file(mcp_template_path)
        if not isinstance(mcp_config, dict):
            mcp_config = {}

    # 确保有 mcpServers 字段
    if "mcpServers" not in mcp_config or not isinstance(mcp_config.get("mcpServers"), dict):
        mcp_config["mcpServers"] = {}

    # 更新 MCP 服务器配置
    updated = False
    for server_name, server_config in plugin_config["mcpServers"].items():
        if server_name not in mcp_config["mcpServers"]:
            mcp_config["mcpServers"][server_name] = server_config
            print(f"{COLOR_GREEN}[+] 添加MCP服务器: {server_name}{COLOR_RESET}")
            updated = True
        else:
            print(f"{COLOR_DARKGRAY}[~] MCP服务器已存在: {server_name}{COLOR_RESET}")

    if updated:
        mcp_template_path.parent.mkdir(parents=True, exist_ok=True)
        save_env_config_file(mcp_template_path, mcp_config)
        print(f"{COLOR_GREEN}[OK] MCP配置已更新: {mcp_template_path}{COLOR_RESET}")


# ============================================================
# 插件安装编排
# ============================================================

def run_plugin_scripts(plugin_config: dict) -> None:
    """执行插件脚本

    注意：install 脚本失败或超时不阻塞后续 skill 安装，只告警。
    原因：scripts.install 常含 npm i -g / browser setup 等可能交互或耗时的命令，
    卡住或失败不应导致 skill 安装（步骤 4）无法执行。
    """
    if "scripts" not in plugin_config:
        return

    scripts = plugin_config["scripts"]

    # 执行 install 脚本
    if "install" in scripts:
        install_cmd = scripts["install"]
        print(f"{COLOR_MAGENTA}[~] 执行插件安装脚本: {install_cmd}{COLOR_RESET}")
        try:
            # 不 capture_output，让用户看到实时进度（避免交互式命令卡死时无任何输出）
            # 设置 timeout 防止交互式命令无限阻塞后续 skill 安装
            result = subprocess.run(
                install_cmd,
                shell=True,
                timeout=300,  # 5 分钟超时，避免 browser setup 卡死
                capture_output=False,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                print(f"{COLOR_GREEN}[OK] 脚本执行成功{COLOR_RESET}")
            else:
                # 失败不阻塞，继续安装 skill
                print(f"{COLOR_YELLOW}[!] 脚本执行失败 (exit={result.returncode})，继续安装 skill{COLOR_RESET}")
        except subprocess.TimeoutExpired:
            print(f"{COLOR_YELLOW}[!] 脚本执行超时 (>300s)，可能为交互式命令，继续安装 skill{COLOR_RESET}")
        except Exception as e:
            print(f"{COLOR_YELLOW}[!] 脚本执行错误: {e}，继续安装 skill{COLOR_RESET}")


def install_skills(plugin_config: dict, source_dir: Path, use_symlink: bool = False) -> None:
    """安装插件所需技能"""
    if "skills" not in plugin_config:
        return

    skills = plugin_config["skills"]

    for skill in skills:
        install_skill(skill, source_dir, use_symlink=use_symlink)


def install_plugin(
    plugin_path: Path,
    env_path: Path,
    mcp_template_path: Path,
    source_dir: Path,
    dry_run: bool = False,
    use_symlink: bool = False
) -> None:
    """安装插件"""
    print(f"{COLOR_CYAN}{'=' * 40}{COLOR_RESET}")
    print(f"{COLOR_CYAN}  插件安装{COLOR_RESET}")
    print(f"{COLOR_CYAN}{'=' * 40}{COLOR_RESET}")

    # 加载和验证插件配置
    plugin_config = load_plugin_config(plugin_path)
    if not validate_plugin_config(plugin_config):
        sys.exit(1)

    # 显示插件信息
    print(f"\n{COLOR_WHITE}插件名称: {plugin_config.get('name', '')}{COLOR_RESET}")
    print(f"{COLOR_WHITE}版本: {plugin_config.get('version', '')}{COLOR_RESET}")
    print(f"{COLOR_WHITE}描述: {plugin_config.get('description', '')}{COLOR_RESET}")
    print(f"{COLOR_WHITE}作者: {plugin_config.get('author', '')}{COLOR_RESET}")

    if dry_run:
        print(f"\n{COLOR_YELLOW}[!] 这是模拟运行，不进行实际修改{COLOR_RESET}")
        return

    # 执行安装步骤
    print(f"\n{COLOR_MAGENTA}步骤 1/4: 更新环境变量{COLOR_RESET}")
    update_env_file(env_path, plugin_config)

    print(f"\n{COLOR_MAGENTA}步骤 2/4: 更新MCP配置{COLOR_RESET}")
    update_mcp_template(mcp_template_path, plugin_config)

    print(f"\n{COLOR_MAGENTA}步骤 3/4: 执行插件脚本{COLOR_RESET}")
    run_plugin_scripts(plugin_config)

    print(f"\n{COLOR_MAGENTA}步骤 4/4: 安装技能{COLOR_RESET}")
    install_skills(plugin_config, source_dir, use_symlink=use_symlink)

    print(f"\n{COLOR_GREEN}{'=' * 40}{COLOR_RESET}")
    print(f"{COLOR_GREEN}  插件安装完成！{COLOR_RESET}")
    print(f"{COLOR_GREEN}{'=' * 40}{COLOR_RESET}")
    print(f"\n{COLOR_YELLOW}下一步: {COLOR_RESET}")
    print(f"  {COLOR_WHITE}1. 运行 agentctl sync 更新运行时配置{COLOR_RESET}")
    print(f"  {COLOR_WHITE}2. 运行 agentctl ide 同步到IDE{COLOR_RESET}")


def list_plugins(plugins_dir: Path) -> None:
    """列出可用的插件"""
    print(f"{COLOR_CYAN}{'=' * 40}{COLOR_RESET}")
    print(f"{COLOR_CYAN}  可用插件列表{COLOR_RESET}")
    print(f"{COLOR_CYAN}{'=' * 40}{COLOR_RESET}")

    if not plugins_dir.exists():
        print(f"{COLOR_YELLOW}[!] 插件目录不存在: {plugins_dir}{COLOR_RESET}")
        return

    # 查找插件文件
    plugin_files = []
    for file in plugins_dir.iterdir():
        if file.is_file() and file.suffix == ".json":
            try:
                with open(file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    if "name" in config and "version" in config:
                        plugin_files.append((file, config))
            except Exception:
                continue

    if not plugin_files:
        print(f"{COLOR_YELLOW}[!] 没有找到有效的插件{COLOR_RESET}")
        return

    print(f"\n找到 {len(plugin_files)} 个插件:\n")
    for i, (file, config) in enumerate(plugin_files, 1):
        print(f"{COLOR_WHITE}{i}. {config.get('name', file.stem)}{COLOR_RESET}")
        print(f"   {COLOR_DARKGRAY}版本: {config.get('version', 'unknown')}{COLOR_RESET}")
        print(f"   {COLOR_DARKGRAY}描述: {config.get('description', '')}{COLOR_RESET}")
        print(f"   {COLOR_DARKGRAY}文件: {file}{COLOR_RESET}")
        print()


# ============================================================
# CSV 相关（list-skills / generate-plugin）
# ============================================================

def load_skills_mapping(csv_path: Path) -> list:
    """从 skills-mapping.csv 加载技能映射"""
    skills = []
    if not csv_path.exists():
        print(f"{COLOR_YELLOW}[!] 技能映射文件不存在: {csv_path}{COLOR_RESET}")
        return skills

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            skills.append(row)

    return skills


def generate_plugin_from_csv(
    csv_path: Path,
    output_path: Path,
    plugin_name: str,
    plugin_description: str,
    category_filter: str = None
) -> None:
    """根据 skills-mapping.csv 生成插件配置"""
    skills = load_skills_mapping(csv_path)
    if not skills:
        print(f"{COLOR_RED}[!] 没有找到技能数据{COLOR_RESET}")
        return

    plugin_skills = []
    for skill in skills:
        # 如果指定了分类过滤
        if category_filter and skill.get("category") != category_filter:
            continue

        skill_name = skill.get("skill_name")
        source_type = skill.get("source_type", "local")
        source = skill.get("source", skill_name)
        description = skill.get("description", "")

        if source_type == "local":
            plugin_skills.append({
                "name": skill_name,
                "type": "local",
                "source": source,
                "description": description
            })
        else:
            # 构建完整的远程安装命令
            plugin_skills.append(f"npx skills add {source} --skill {skill_name} -y")

    plugin_config = {
        "name": plugin_name,
        "version": "1.0.0",
        "description": plugin_description,
        "author": "MyAgentPlugin",
        "mcpServers": {},
        "skills": plugin_skills
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(plugin_config, f, indent=2, ensure_ascii=False)

    print(f"{COLOR_GREEN}[OK] 插件已生成: {output_path}{COLOR_RESET}")
    print(f"   包含 {len(plugin_skills)} 个技能")


def list_skills_from_csv(csv_path: Path) -> None:
    """从 skills-mapping.csv 列出所有技能"""
    skills = load_skills_mapping(csv_path)
    if not skills:
        return

    print(f"{COLOR_CYAN}{'=' * 40}{COLOR_RESET}")
    print(f"{COLOR_CYAN}  技能列表{COLOR_RESET}")
    print(f"{COLOR_CYAN}{'=' * 40}{COLOR_RESET}")

    # 按分类分组
    categories = {}
    for skill in skills:
        category = skill.get("category", "未分类")
        if category not in categories:
            categories[category] = []
        categories[category].append(skill)

    for category in sorted(categories.keys()):
        print(f"\n{COLOR_WHITE}## {category}{COLOR_RESET}")
        for skill in categories[category]:
            source_type = skill.get("source_type", "local")
            print(f"   - {skill.get('skill_name')} [{source_type}]")
            print(f"     {skill.get('description', '')}")
