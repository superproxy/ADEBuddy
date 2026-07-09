"""agentctl 测试套件。

迁移自 tests/test_init_env.py 和 tests/test_plugin_manager.py，
改为导入 scripts/lib/ 下的模块（替代直接导入旧脚本）。

测试覆盖：
- FlattenEnvConfigTests: llm.flatten_env_config 行为（迁移自 test_init_env）
- SkillsFilterTests: skills.copy_skills_safe 白名单过滤（新增）
"""
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

# 将 scripts/ 加入 sys.path 以导入 lib 包
SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from lib import llm, skills, plugins
from lib import provider_catalog


class FlattenEnvConfigTests(unittest.TestCase):
    """迁移自 test_init_env.py，验证 llm.flatten_env_config 行为不变。"""

    def test_vision_flat_provider_exports_default_model(self):
        env_config = {
            "vision": {
                "volcengine": {
                    "base_url": "https://example.invalid/api",
                    "api_key": "test-key",
                    "models": {
                        "doubao-seedance-2-0-fast-260128": {
                            "name": "Seedance fast"
                        }
                    },
                }
            }
        }

        flat = llm.flatten_env_config(env_config, "", [])

        self.assertEqual(
            flat["VISION_VOLCENGINE_MODEL"],
            "doubao-seedance-2-0-fast-260128",
        )


class SkillsFilterTests(unittest.TestCase):
    """新增：验证 skills.copy_skills_safe 的白名单过滤。"""

    def test_include_skills_filters_copy(self):
        with tempfile.TemporaryDirectory() as td:
            src = pathlib.Path(td) / "src"
            src.mkdir()
            (src / "keep").mkdir()
            (src / "keep" / "SKILL.md").write_text("x")
            (src / "skip").mkdir()
            (src / "skip" / "SKILL.md").write_text("y")
            dst = pathlib.Path(td) / "dst"

            skills.copy_skills_safe(src, dst, "test", True, include_skills={"keep"})

            self.assertTrue((dst / "keep").exists())
            self.assertFalse((dst / "skip").exists())

    def test_include_skills_none_copies_all(self):
        with tempfile.TemporaryDirectory() as td:
            src = pathlib.Path(td) / "src"
            src.mkdir()
            (src / "a").mkdir()
            (src / "a" / "SKILL.md").write_text("a")
            (src / "b").mkdir()
            (src / "b" / "SKILL.md").write_text("b")
            dst = pathlib.Path(td) / "dst"

            skills.copy_skills_safe(src, dst, "test", True, include_skills=None)

            self.assertTrue((dst / "a").exists())
            self.assertTrue((dst / "b").exists())


class ProviderCatalogTests(unittest.TestCase):
    """Provider Catalog / Detect / Apply 管道。"""

    @classmethod
    def setUpClass(cls):
        root = pathlib.Path(__file__).resolve().parents[1]
        cls.example = root / "template" / "llm" / "llm-env-example.yaml"
        cls.catalog = provider_catalog.load_provider_catalog(cls.example)

    def test_catalog_loads_known_providers(self):
        names = {c["provider"] for c in self.catalog}
        self.assertIn("bigmodel", names)
        self.assertIn("bigmodelCoding", names)
        self.assertIn("openrouter", names)
        self.assertIn("anthropic", names)
        big = next(c for c in self.catalog if c["provider"] == "bigmodel")
        self.assertIn("openai", big["protocols"])
        self.assertTrue(big["protocols"]["openai"]["base_url"])

    def test_detect_sk_ant_unique(self):
        hits = provider_catalog.detect_providers("sk-ant-xxx", catalog=self.catalog)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["provider"], "anthropic")
        self.assertEqual(hits[0]["suggested_protocol"], "anthropic")

    def test_detect_sk_or_unique(self):
        hits = provider_catalog.detect_providers("sk-or-v1-xxx", catalog=self.catalog)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["provider"], "openrouter")

    def test_detect_bigmodel_coding_url(self):
        hits = provider_catalog.detect_providers(
            "sk-xxx",
            "https://open.bigmodel.cn/api/coding/paas/v4",
            catalog=self.catalog,
        )
        self.assertEqual(hits[0]["provider"], "bigmodelCoding")

    def test_detect_volcengine_exact_endpoint(self):
        """精确匹配 catalog 端点时直接锁定，不再展开家族。"""
        hits = provider_catalog.detect_providers(
            "sk-xxx",
            "https://ark.cn-beijing.volces.com/api/v3",
            catalog=self.catalog,
        )
        self.assertEqual(hits[0]["provider"], "volcengine")
        self.assertEqual(hits[0]["detected_protocol"], "openai")
        self.assertEqual(len(hits), 1)

    def test_detect_volcengine_family_ambiguous(self):
        """URL 仅命中域名、未精确到 catalog 端点时展开家族。"""
        hits = provider_catalog.detect_providers(
            "sk-xxx",
            "https://ark.cn-beijing.volces.com/",
            catalog=self.catalog,
        )
        names = [h["provider"] for h in hits]
        self.assertIn("volcengine", names)
        self.assertGreaterEqual(len(hits), 2)

    def test_detect_generic_sk_needs_choice(self):
        hits = provider_catalog.detect_providers("sk-generic-key", catalog=self.catalog)
        self.assertGreater(len(hits), 1)

    def test_apply_writes_key_and_active(self):
        env = {"llm": {}}
        cand = next(c for c in self.catalog if c["provider"] == "deepseek")
        cand = {**cand, "score": 100, "reason": "test", "detected_protocol": "openai"}
        applied = provider_catalog.apply_provider_to_env(env, cand, "sk-test")
        self.assertEqual(applied["provider"], "deepseek")
        self.assertEqual(env["llm"]["_active_provider"], "deepseek")
        self.assertEqual(env["llm"]["_active_protocol"], "openai")
        self.assertEqual(env["llm"]["deepseek"]["openai"]["api_key"], "sk-test")
        self.assertTrue(env["llm"]["deepseek"]["openai"]["base_url"])

    def test_detect_protocol_from_anthropic_url(self):
        hits = provider_catalog.detect_providers(
            "sk-xxx",
            "https://open.bigmodel.cn/api/anthropic",
            catalog=self.catalog,
        )
        self.assertEqual(hits[0]["provider"], "bigmodel")
        self.assertEqual(hits[0]["detected_protocol"], "anthropic")
        self.assertEqual(hits[0]["active_protocol"], "anthropic")

    def test_detect_protocol_from_sk_ant(self):
        hits = provider_catalog.detect_providers("sk-ant-xxx", catalog=self.catalog)
        self.assertEqual(hits[0]["detected_protocol"], "anthropic")

    def test_detect_protocol_from_openai_path(self):
        hits = provider_catalog.detect_providers(
            "sk-xxx",
            "https://open.bigmodel.cn/api/paas/v4",
            catalog=self.catalog,
        )
        self.assertEqual(hits[0]["provider"], "bigmodel")
        self.assertEqual(hits[0]["detected_protocol"], "openai")

    def test_detect_endpoint_exact_match(self):
        hits = provider_catalog.detect_providers(
            "sk-xxx",
            "https://api.z.ai/api/coding/paas/v4",
            catalog=self.catalog,
        )
        self.assertEqual(hits[0]["provider"], "zaiCoding")
        self.assertEqual(hits[0]["detected_protocol"], "openai")

    def test_infer_protocol_openrouter_anthropic_path(self):
        proto, _ = provider_catalog.infer_protocol(
            "sk-or-xxx",
            "https://openrouter.ai/api",
            {"openai": {}, "anthropic": {}},
        )
        self.assertEqual(proto, "anthropic")

    def test_key_only_auto_fills_base_url(self):
        """只输 Key 时，候选应带上 catalog 默认 Base URL。"""
        hits = provider_catalog.detect_providers("sk-ant-xxx", catalog=self.catalog)
        self.assertEqual(hits[0]["provider"], "anthropic")
        url = hits[0]["protocols"]["anthropic"]["base_url"]
        self.assertTrue(url, "catalog 应提供默认 base_url")
        env = {"llm": {}}
        applied = provider_catalog.apply_provider_to_env(env, hits[0], "sk-ant-xxx")
        self.assertEqual(applied["base_url"], url)
        self.assertEqual(env["llm"]["anthropic"]["anthropic"]["base_url"], url)

    def test_apply_without_override_keeps_catalog_url(self):
        env = {"llm": {}}
        cand = next(c for c in self.catalog if c["provider"] == "openrouter")
        cand = {**cand, "detected_protocol": "openai", "score": 100, "reason": "test"}
        catalog_url = cand["protocols"]["openai"]["base_url"]
        applied = provider_catalog.apply_provider_to_env(
            env, cand, "sk-or-test", base_url_override="",
        )
        self.assertEqual(applied["base_url"], catalog_url)
        self.assertEqual(env["llm"]["openrouter"]["openai"]["base_url"], catalog_url)


if __name__ == "__main__":
    unittest.main()
