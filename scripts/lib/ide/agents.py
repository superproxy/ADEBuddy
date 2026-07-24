""".agent 公共 IDE 规范目录分发器。

定位：把全部配置（rules/mcp/skills/subagents/AGENTS.md）同步到 .agent/ 目录，
作为公共 IDE 规范源，默认不在 UI 显示（hidden=True）。
各 IDE 可共享读取此目录，用软链接避免重复占用磁盘。
"""
import shutil
from pathlib import Path

from lib.logging import COLOR_GREEN, COLOR_RED, COLOR_RESET
from lib.mcp import copy_file_safe, copy_dir_safe
from lib.skills import copy_skills_safe, write_skills_index
from .base import IdeTarget


class AgentsTarget(IdeTarget):
    name = "Agents"
    # .agent/ 目录作为公共 IDE 规范，默认不显示
    # hidden 标记在 install.py 的 IDE_INFO 中已设为 True

    @property
    def agent_dir(self) -> Path:
        """公共 .agent/ 目录。"""
        return self.root / ".agent"

    def init_rules(self, source_rules):
        """同步 rules 到 .agent/rules/（支持多源合并，前者优先）。

        source_rules 可为 Path 或 list[Path]（如 [config/rules, template/rules]），
        多源时按顺序合并，同名条目前者优先，后者跳过。
        """
        srcs = source_rules if isinstance(source_rules, list) else [source_rules]
        srcs = [Path(s) for s in srcs if s and Path(s).exists()]
        if not srcs:
            return
        dst = self.agent_dir / "rules"
        dst.mkdir(parents=True, exist_ok=True)
        seen = set()
        copied = 0
        for src_dir in srcs:
            for item in sorted(src_dir.iterdir()):
                if item.name in seen:
                    continue
                target = dst / item.name
                if target.exists() or target.is_symlink():
                    if not self.force:
                        seen.add(item.name)
                        continue
                    try:
                        if target.is_dir() and not target.is_symlink():
                            shutil.rmtree(str(target), ignore_errors=True)
                        else:
                            target.unlink(missing_ok=True)
                    except Exception:
                        seen.add(item.name)
                        continue
                try:
                    if item.is_dir():
                        shutil.copytree(str(item), str(target),
                                        ignore=shutil.ignore_patterns('.git'))
                    else:
                        shutil.copy2(str(item), str(target))
                    seen.add(item.name)
                    copied += 1
                except Exception as e:
                    print(f"{COLOR_RED}[!] Failed to copy rule {item.name}: {e}{COLOR_RESET}")
        if copied:
            print(f"{COLOR_GREEN}[OK] .agent/rules/: {copied} files copied{COLOR_RESET}")

    def init_mcp(self, source_mcp_file: Path):
        """同步 mcp 配置到 .agent/mcp/。"""
        if not source_mcp_file or not Path(source_mcp_file).exists():
            return
        dst_dir = self.agent_dir / "mcp"
        dst_dir.mkdir(parents=True, exist_ok=True)
        copy_file_safe(source_mcp_file, dst_dir / Path(source_mcp_file).name,
                       f".agent/mcp/{Path(source_mcp_file).name}", self.force)

    def init_skills(self, source_skills_dir: Path):
        """同步 skills 到 .agent/skills/（软链接方式）。"""
        agents_skills_dir = self.agent_dir / "skills"
        copy_skills_safe(source_skills_dir, agents_skills_dir, ".agent/skills/",
                         self.force, self.include_skills, link=self.link_skills)
        write_skills_index(source_skills_dir, agents_skills_dir / "README.md",
                           "Agents", self.force, self.include_skills)

        if isinstance(source_skills_dir, list):
            srcs = [s for s in source_skills_dir if s.exists()]
        else:
            srcs = [source_skills_dir] if source_skills_dir.exists() else []
        if srcs:
            seen = set()
            skill_count = 0
            for s in srcs:
                for d in s.iterdir():
                    if d.is_dir() and d.name not in seen:
                        seen.add(d.name)
                        skill_count += 1
            print(f"{COLOR_GREEN}[OK] {skill_count} skills available in .agent/skills/{COLOR_RESET}")

    def init_manifest(self, source_agents_md: Path):
        """同步 AGENTS.md 到 .agent/AGENTS.md。"""
        if not source_agents_md or not Path(source_agents_md).exists():
            return
        copy_file_safe(source_agents_md, self.agent_dir / "AGENTS.md",
                       ".agent/AGENTS.md", self.force)

    def init_llm(self, source_rules_dir: Path):
        """同步 subagents 到 .agent/subagents/。"""
        subagents_src = self.root / "config" / "subagents"
        if subagents_src.exists():
            dst = self.agent_dir / "subagents"
            copy_dir_safe(subagents_src, dst, ".agent/subagents/", self.force)

    def run(self, source_rules: Path, source_mcp_file: Path,
            source_skills_dir: Path, source_agents_md: Path) -> str:
        """Agents 始终同步全部内容到 .agent/，不受 scope 限制。"""
        from lib.logging import COLOR_MAGENTA, COLOR_RESET
        print(f"\n{COLOR_MAGENTA}--- {self.name} (.agent/) ---{COLOR_RESET}")
        self.init_rules(source_rules)
        self.init_mcp(source_mcp_file)
        self.init_skills(source_skills_dir)
        self.init_llm(source_rules)
        self.init_manifest(source_agents_md)
        return self.name
