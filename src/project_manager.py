"""
项目归档管理模块
负责以客户/项目维度管理工作内容，独立存储和追溯每个项目的历史数据。
"""

import json
import os
import shutil
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class ScriptRecord:
    """脚本历史记录数据类"""
    id: str
    content: str
    created_at: str
    version: int
    is_archived: bool = False
    parsed_output: Optional[dict] = None
    
    @classmethod
    def create(cls, content: str, version: int = 1, is_archived: bool = False, 
               parsed_output: Optional[dict] = None) -> "ScriptRecord":
        """创建新的脚本记录"""
        return cls(
            id=str(uuid.uuid4()),
            content=content,
            created_at=datetime.now().isoformat(),
            version=version,
            is_archived=is_archived,
            parsed_output=parsed_output
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ScriptRecord":
        """从字典创建实例"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            version=data.get("version", 1),
            is_archived=data.get("is_archived", False),
            parsed_output=data.get("parsed_output")
        )


@dataclass
class Project:
    """项目数据类"""
    client_name: str
    project_name: str
    game_intro: str = ""
    usp: str = ""
    target_audience: str = ""
    category: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    scripts_history: list[ScriptRecord] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典（不包含脚本历史，脚本单独存储）"""
        return {
            "client_name": self.client_name,
            "project_name": self.project_name,
            "game_intro": self.game_intro,
            "usp": self.usp,
            "target_audience": self.target_audience,
            "category": self.category,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict, scripts_history: list[ScriptRecord] = None) -> "Project":
        """从字典创建实例"""
        return cls(
            client_name=data.get("client_name", ""),
            project_name=data.get("project_name", ""),
            game_intro=data.get("game_intro", ""),
            usp=data.get("usp", ""),
            target_audience=data.get("target_audience", ""),
            category=data.get("category", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            scripts_history=scripts_history or []
        )
    
    def update_timestamp(self):
        """更新修改时间"""
        self.updated_at = datetime.now().isoformat()


class ProjectManager:
    """项目管理器，负责项目的创建、加载、更新、删除和脚本历史管理"""
    
    def __init__(self, projects_path: str = "./data/projects"):
        """初始化项目管理器"""
        self.projects_path = projects_path
        os.makedirs(projects_path, exist_ok=True)
    
    def _get_project_dir(self, client_name: str, project_name: str) -> str:
        """获取项目目录路径"""
        return os.path.join(self.projects_path, client_name, project_name)
    
    def _get_project_file(self, client_name: str, project_name: str) -> str:
        """获取项目配置文件路径"""
        return os.path.join(self._get_project_dir(client_name, project_name), "project.json")
    
    def _get_scripts_dir(self, client_name: str, project_name: str) -> str:
        """获取脚本历史目录路径"""
        return os.path.join(self._get_project_dir(client_name, project_name), "scripts")
    
    def _sanitize_name(self, name: str) -> str:
        """清理名称中的非法字符"""
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        result = name
        for char in invalid_chars:
            result = result.replace(char, '_')
        return result.strip()
    
    def create_project(self, client_name: str, project_name: str) -> Project:
        """创建新项目"""
        client_name = self._sanitize_name(client_name)
        project_name = self._sanitize_name(project_name)
        
        project_dir = self._get_project_dir(client_name, project_name)
        
        if os.path.exists(project_dir):
            raise ValueError(f"项目已存在: {client_name}/{project_name}")
        
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(self._get_scripts_dir(client_name, project_name), exist_ok=True)
        
        project = Project(client_name=client_name, project_name=project_name)
        
        with open(self._get_project_file(client_name, project_name), 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
        
        return project

    
    def get_project(self, client_name: str, project_name: str) -> Optional[Project]:
        """获取项目"""
        client_name = self._sanitize_name(client_name)
        project_name = self._sanitize_name(project_name)
        
        project_file = self._get_project_file(client_name, project_name)
        
        if not os.path.exists(project_file):
            return None
        
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            scripts_history = self._load_scripts_history(client_name, project_name)
            return Project.from_dict(data, scripts_history)
        except (json.JSONDecodeError, IOError):
            return None
    
    def _load_scripts_history(self, client_name: str, project_name: str) -> list[ScriptRecord]:
        """加载项目的脚本历史"""
        scripts_dir = self._get_scripts_dir(client_name, project_name)
        scripts = []
        
        if not os.path.exists(scripts_dir):
            return scripts
        
        for filename in os.listdir(scripts_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(scripts_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    scripts.append(ScriptRecord.from_dict(data))
                except (json.JSONDecodeError, IOError):
                    continue
        
        scripts.sort(key=lambda x: x.created_at)
        return scripts
    
    def list_projects(self) -> list[Project]:
        """列出所有项目"""
        projects = []
        
        if not os.path.exists(self.projects_path):
            return projects
        
        for client_name in os.listdir(self.projects_path):
            client_dir = os.path.join(self.projects_path, client_name)
            if not os.path.isdir(client_dir):
                continue
            
            for project_name in os.listdir(client_dir):
                project = self.get_project(client_name, project_name)
                if project:
                    projects.append(project)
        
        return projects
    
    def list_clients(self) -> list[str]:
        """列出所有客户"""
        clients = []
        
        if not os.path.exists(self.projects_path):
            return clients
        
        for name in os.listdir(self.projects_path):
            if os.path.isdir(os.path.join(self.projects_path, name)):
                clients.append(name)
        
        return sorted(clients)

    
    def update_project(self, project: Project) -> bool:
        """更新项目信息"""
        client_name = self._sanitize_name(project.client_name)
        project_name = self._sanitize_name(project.project_name)
        
        project_file = self._get_project_file(client_name, project_name)
        
        if not os.path.exists(project_file):
            return False
        
        try:
            project.update_timestamp()
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False
    
    def add_script_to_history(self, client_name: str, project_name: str, 
                              script: str, parsed_output: Optional[dict] = None) -> Optional[ScriptRecord]:
        """添加脚本到项目历史"""
        client_name = self._sanitize_name(client_name)
        project_name = self._sanitize_name(project_name)
        
        scripts_dir = self._get_scripts_dir(client_name, project_name)
        
        if not os.path.exists(scripts_dir):
            return None
        
        existing_scripts = self._load_scripts_history(client_name, project_name)
        version = len(existing_scripts) + 1
        
        record = ScriptRecord.create(
            content=script,
            version=version,
            parsed_output=parsed_output
        )
        
        script_file = os.path.join(scripts_dir, f"{record.id}.json")
        try:
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
            
            project = self.get_project(client_name, project_name)
            if project:
                self.update_project(project)
            
            return record
        except IOError:
            return None
    
    def delete_project(self, client_name: str, project_name: str) -> bool:
        """删除项目"""
        client_name = self._sanitize_name(client_name)
        project_name = self._sanitize_name(project_name)
        
        project_dir = self._get_project_dir(client_name, project_name)
        
        if not os.path.exists(project_dir):
            return False
        
        try:
            shutil.rmtree(project_dir)
            
            client_dir = os.path.join(self.projects_path, client_name)
            if os.path.exists(client_dir) and not os.listdir(client_dir):
                os.rmdir(client_dir)
            
            return True
        except (IOError, OSError):
            return False
    
    def get_projects_by_client(self, client_name: str) -> list[Project]:
        """获取指定客户的所有项目"""
        client_name = self._sanitize_name(client_name)
        projects = []
        
        client_dir = os.path.join(self.projects_path, client_name)
        if not os.path.exists(client_dir):
            return projects
        
        for project_name in os.listdir(client_dir):
            project = self.get_project(client_name, project_name)
            if project:
                projects.append(project)
        
        return projects
