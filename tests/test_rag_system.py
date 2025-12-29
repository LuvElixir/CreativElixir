"""
RAG 知识库系统测试
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from src.rag_system import RAGSystem, Script, ScriptMetadata


@pytest.fixture
def temp_dirs():
    """创建临时测试目录"""
    temp_dir = tempfile.mkdtemp()
    vector_db_path = Path(temp_dir) / "vector_db"
    scripts_path = Path(temp_dir) / "scripts"
    
    yield vector_db_path, scripts_path
    
    # 清理
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def rag_system(temp_dirs):
    """创建 RAG 系统实例"""
    vector_db_path, scripts_path = temp_dirs
    return RAGSystem(str(vector_db_path), str(scripts_path))


class TestRAGSystemBasic:
    """基础功能测试"""
    
    def test_init(self, rag_system):
        """测试初始化"""
        assert rag_system is not None
        assert rag_system.get_script_count() == 0
    
    def test_add_script(self, rag_system):
        """测试添加脚本"""
        doc_id = rag_system.add_script(
            content="测试脚本内容",
            category="SLG",
            metadata={"game_name": "测试游戏"}
        )
        
        assert doc_id is not None
        assert len(doc_id) > 0
        assert rag_system.get_script_count() == 1
    
    def test_get_script(self, rag_system):
        """测试获取脚本"""
        content = "测试脚本内容"
        doc_id = rag_system.add_script(
            content=content,
            category="SLG",
            metadata={"game_name": "测试游戏"}
        )
        
        script = rag_system.get_script("SLG", doc_id)
        
        assert script is not None
        assert script.content == content
        assert script.category == "SLG"
        assert script.metadata.game_name == "测试游戏"
    
    def test_get_scripts_by_category(self, rag_system):
        """测试按品类获取脚本"""
        rag_system.add_script("SLG脚本1", "SLG")
        rag_system.add_script("SLG脚本2", "SLG")
        rag_system.add_script("MMO脚本1", "MMO")
        
        slg_scripts = rag_system.get_scripts_by_category("SLG")
        mmo_scripts = rag_system.get_scripts_by_category("MMO")
        
        assert len(slg_scripts) == 2
        assert len(mmo_scripts) == 1
    
    def test_search(self, rag_system):
        """测试搜索功能"""
        rag_system.add_script("战略游戏广告脚本", "SLG")
        rag_system.add_script("休闲游戏广告脚本", "休闲")
        
        results = rag_system.search("战略", "SLG", top_k=5)
        
        assert len(results) >= 1
        assert "战略" in results[0].content
    
    def test_delete_script(self, rag_system):
        """测试删除脚本"""
        doc_id = rag_system.add_script("测试脚本", "SLG")
        
        assert rag_system.get_script_count() == 1
        
        result = rag_system.delete_script(doc_id)
        
        assert result is True
        assert rag_system.get_script_count() == 0
    
    def test_get_categories(self, rag_system):
        """测试获取品类列表"""
        categories = rag_system.get_categories()
        
        # 应该包含默认品类
        assert "SLG" in categories
        assert "MMO" in categories
        assert "休闲" in categories


class TestRAGSystemExportImport:
    """导入导出功能测试"""
    
    def test_export_knowledge_base(self, rag_system, temp_dirs):
        """测试导出知识库"""
        # 添加一些测试数据
        rag_system.add_script("SLG脚本1", "SLG", {"game_name": "游戏1"})
        rag_system.add_script("MMO脚本1", "MMO", {"game_name": "游戏2"})
        
        # 导出
        vector_db_path, scripts_path = temp_dirs
        export_path = str(Path(scripts_path).parent / "export_test")
        
        success, result = rag_system.export_knowledge_base(export_path)
        
        assert success is True
        assert Path(result).exists()
        assert result.endswith(".zip")
    
    def test_import_knowledge_base(self, temp_dirs):
        """测试导入知识库"""
        vector_db_path, scripts_path = temp_dirs
        
        # 创建第一个 RAG 系统并添加数据
        rag1 = RAGSystem(str(vector_db_path), str(scripts_path))
        rag1.add_script("SLG脚本1", "SLG", {"game_name": "游戏1"})
        rag1.add_script("MMO脚本1", "MMO", {"game_name": "游戏2"})
        
        original_count = rag1.get_script_count()
        
        # 导出
        export_path = str(Path(scripts_path).parent / "export_test")
        success, zip_path = rag1.export_knowledge_base(export_path)
        assert success is True
        
        # 创建第二个 RAG 系统（空的）
        vector_db_path2 = Path(scripts_path).parent / "vector_db2"
        scripts_path2 = Path(scripts_path).parent / "scripts2"
        rag2 = RAGSystem(str(vector_db_path2), str(scripts_path2))
        
        assert rag2.get_script_count() == 0
        
        # 导入
        success, message = rag2.import_knowledge_base(zip_path)
        
        assert success is True
        assert rag2.get_script_count() == original_count
    
    def test_import_invalid_file(self, rag_system, temp_dirs):
        """测试导入无效文件"""
        vector_db_path, scripts_path = temp_dirs
        
        # 创建一个无效的文件
        invalid_file = Path(scripts_path).parent / "invalid.zip"
        invalid_file.write_text("not a zip file")
        
        success, message = rag_system.import_knowledge_base(str(invalid_file))
        
        assert success is False
        assert "格式不正确" in message
    
    def test_import_nonexistent_file(self, rag_system):
        """测试导入不存在的文件"""
        success, message = rag_system.import_knowledge_base("/nonexistent/path.zip")
        
        assert success is False
        assert "不存在" in message
    
    def test_clear_knowledge_base(self, rag_system):
        """测试清空知识库"""
        # 添加数据
        rag_system.add_script("测试脚本1", "SLG")
        rag_system.add_script("测试脚本2", "MMO")
        
        assert rag_system.get_script_count() == 2
        
        # 清空
        success, message = rag_system.clear_knowledge_base()
        
        assert success is True
        assert rag_system.get_script_count() == 0


class TestScriptDataClass:
    """Script 数据类测试"""
    
    def test_script_to_dict(self):
        """测试脚本转字典"""
        script = Script(
            id="test-id",
            content="测试内容",
            category="SLG",
            metadata=ScriptMetadata(game_name="测试游戏")
        )
        
        data = script.to_dict()
        
        assert data["id"] == "test-id"
        assert data["content"] == "测试内容"
        assert data["category"] == "SLG"
        assert data["metadata"]["game_name"] == "测试游戏"
    
    def test_script_from_dict(self):
        """测试从字典创建脚本"""
        data = {
            "id": "test-id",
            "content": "测试内容",
            "category": "SLG",
            "metadata": {
                "game_name": "测试游戏",
                "performance": "爆款"
            }
        }
        
        script = Script.from_dict(data)
        
        assert script.id == "test-id"
        assert script.content == "测试内容"
        assert script.category == "SLG"
        assert script.metadata.game_name == "测试游戏"
        assert script.metadata.performance == "爆款"
    
    def test_script_roundtrip(self):
        """测试脚本序列化往返"""
        original = Script(
            id="test-id",
            content="测试内容",
            category="SLG",
            metadata=ScriptMetadata(
                game_name="测试游戏",
                performance="爆款",
                source="user_archive"
            )
        )
        
        # 转换为字典再转回来
        data = original.to_dict()
        restored = Script.from_dict(data)
        
        assert restored.id == original.id
        assert restored.content == original.content
        assert restored.category == original.category
        assert restored.metadata.game_name == original.metadata.game_name
        assert restored.metadata.performance == original.metadata.performance
        assert restored.metadata.source == original.metadata.source
