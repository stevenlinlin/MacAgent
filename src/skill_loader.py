"""
Skills 加载器 — 扫描 skills/ 目录，加载 SKILL.md
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict

def discover_skills(skills_dir: str = "./skills") -> List[Dict]:
    """扫描 skills 目录，返回所有 Skill 元数据"""
    skills = []
    base = Path(skills_dir)
    if not base.exists():
        return skills
    
    for folder in base.iterdir():
        if folder.is_dir():
            md_file = folder / "SKILL.md"
            if md_file.exists():
                content = md_file.read_text(encoding="utf-8")
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        skills.append({
                            "name": frontmatter.get("name", folder.name),
                            "description": frontmatter.get("description", ""),
                            "body": parts[2].strip(),
                            "path": str(folder)
                        })
    return skills

def load_skill_body(skill_name: str, skills_dir: str = "./skills") -> str:
    """加载指定 Skill 的完整指令正文"""
    skills = discover_skills(skills_dir)
    for s in skills:
        if s["name"] == skill_name:
            return s["body"]
    return ""