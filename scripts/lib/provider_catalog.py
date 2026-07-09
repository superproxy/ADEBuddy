"""LLM Provider Catalog：从 llm-env-example.yaml 构建预设，并按 key/URL 推断厂商+协议。

对齐 OpenClaw 配置管道思路：
  Catalog（模板预设）→ Detect（厂商+协议）→ Apply → Verify
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from lib.config_io import load_env_config_file

# 厂商展示名 / 家族（同家族多端点时弹出候选）
PROVIDER_META: Dict[str, Dict[str, str]] = {
    "openicu": {"label": "OpenICU", "family": "openicu"},
    "bigmodel": {"label": "BigModel（资源包/余额）", "family": "bigmodel"},
    "bigmodelCoding": {"label": "BigModel Coding Plan", "family": "bigmodel"},
    "zai": {"label": "Z.ai（资源包/余额）", "family": "zai"},
    "zaiCoding": {"label": "Z.ai Coding Plan", "family": "zai"},
    "openrouter": {"label": "OpenRouter", "family": "openrouter"},
    "openai": {"label": "OpenAI", "family": "openai"},
    "anthropic": {"label": "Anthropic", "family": "anthropic"},
    "deepseek": {"label": "DeepSeek", "family": "deepseek"},
    "volcengine": {"label": "火山方舟（通用）", "family": "volcengine"},
    "volcengineCoding": {"label": "火山方舟 Coding", "family": "volcengine"},
    "volcengineAgent": {"label": "火山方舟 Agent/Plan", "family": "volcengine"},
    "moonshot": {"label": "Moonshot / Kimi", "family": "moonshot"},
    "qwen": {"label": "通义千问 / DashScope", "family": "qwen"},
    "openai-compatible": {"label": "OpenAI Compatible", "family": "custom"},
    "custom": {"label": "自定义 Provider", "family": "custom"},
}

# 检测规则：按顺序匹配，越靠前优先级越高。
DETECT_RULES: List[Dict[str, Any]] = [
    {
        "provider": "anthropic",
        "key_prefixes": ["sk-ant-"],
        "url_includes": ["api.anthropic.com", "anthropic.com"],
        "url_requires": [],
        "url_excludes": ["openrouter", "bigmodel", "z.ai", "volces", "deepseek"],
        "key_only": True,
        "protocol": "anthropic",
    },
    {
        "provider": "openrouter",
        "key_prefixes": ["sk-or-"],
        "url_includes": ["openrouter.ai", "openrouter"],
        "url_requires": [],
        "url_excludes": [],
        "key_only": True,
        "protocol": "openai",
    },
    {
        "provider": "bigmodelCoding",
        "key_prefixes": [],
        "url_includes": ["bigmodel.cn", "bigmodel"],
        "url_requires": ["/coding/"],
        "url_excludes": [],
        "key_only": False,
    },
    {
        "provider": "bigmodel",
        "key_prefixes": [],
        "url_includes": ["bigmodel.cn", "bigmodel"],
        "url_requires": [],
        "url_excludes": ["/coding/"],
        "key_only": False,
    },
    {
        "provider": "zaiCoding",
        "key_prefixes": [],
        "url_includes": ["api.z.ai", "z.ai"],
        "url_requires": ["/coding/"],
        "url_excludes": [],
        "key_only": False,
    },
    {
        "provider": "zai",
        "key_prefixes": [],
        "url_includes": ["api.z.ai", "z.ai"],
        "url_requires": [],
        "url_excludes": ["/coding/"],
        "key_only": False,
    },
    {
        "provider": "volcengineCoding",
        "key_prefixes": [],
        "url_includes": ["volces.com", "volcengine"],
        "url_requires": ["/coding"],
        "url_excludes": [],
        "key_only": False,
    },
    {
        "provider": "volcengineAgent",
        "key_prefixes": [],
        "url_includes": ["volces.com", "volcengine"],
        "url_requires": ["/plan"],
        "url_excludes": [],
        "key_only": False,
    },
    {
        "provider": "volcengine",
        "key_prefixes": [],
        "url_includes": ["volces.com", "volcengine", "ark.cn-beijing"],
        "url_requires": [],
        "url_excludes": ["/coding", "/plan"],
        "key_only": False,
    },
    {
        "provider": "deepseek",
        "key_prefixes": [],
        "url_includes": ["deepseek.com", "deepseek.cn", "api.deepseek"],
        "url_requires": [],
        "url_excludes": [],
        "key_only": False,
    },
    {
        "provider": "moonshot",
        "key_prefixes": [],
        "url_includes": ["moonshot", "kimi"],
        "url_requires": [],
        "url_excludes": [],
        "key_only": False,
    },
    {
        "provider": "qwen",
        "key_prefixes": [],
        "url_includes": ["dashscope", "aliyuncs"],
        "url_requires": [],
        "url_excludes": [],
        "key_only": False,
    },
    {
        "provider": "openicu",
        "key_prefixes": [],
        "url_includes": ["rehdasu"],
        "url_requires": [],
        "url_excludes": [],
        "key_only": False,
    },
    {
        "provider": "openai",
        "key_prefixes": [],
        "url_includes": ["api.openai.com", "openai.com"],
        "url_requires": [],
        "url_excludes": ["openrouter", "azure"],
        "key_only": False,
        "protocol": "openai",
    },
]

GENERIC_SK_CANDIDATES = [
    "openai",
    "openrouter",
    "deepseek",
    "bigmodel",
    "bigmodelCoding",
    "zai",
    "zaiCoding",
    "volcengine",
    "volcengineCoding",
    "volcengineAgent",
    "moonshot",
    "openicu",
]

FAMILY_EXPAND_ON_AMBIGUOUS = {
    "bigmodel": ["bigmodel", "bigmodelCoding"],
    "zai": ["zai", "zaiCoding"],
    "volcengine": ["volcengine", "volcengineCoding", "volcengineAgent"],
}


def _meta(provider: str) -> Dict[str, str]:
    return PROVIDER_META.get(provider, {"label": provider, "family": provider})


def _norm_url(url: str) -> str:
    return (url or "").strip().rstrip("/").lower()


def _url_parts(url: str) -> Tuple[str, str]:
    """返回 (host, path)，均小写、path 无尾斜杠。"""
    u = _norm_url(url)
    if not u:
        return "", ""
    if "://" not in u:
        u = "https://" + u
    try:
        p = urlparse(u)
        return (p.netloc or "", (p.path or "").rstrip("/"))
    except Exception:
        return "", ""


def infer_protocol(
    api_key: str = "",
    base_url: str = "",
    available: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """推断协议。返回 (protocol, reason)。

    优先级：
      1. key 前缀 sk-ant- → anthropic
      2. URL 路径特征（/anthropic、anthropic 域名）→ anthropic
      3. 与 catalog 各协议 base_url 精确/前缀匹配
      4. 默认 openai（若 available 含 openai，否则取第一个）
    """
    key = (api_key or "").strip().lower()
    url = _norm_url(base_url)
    avail = available or {}

    if key.startswith("sk-ant-"):
        if not avail or "anthropic" in avail:
            return "anthropic", "API Key 前缀 sk-ant-"

    if url:
        host, path = _url_parts(url)
        # 原生 Anthropic
        if "anthropic.com" in host and "openrouter" not in host:
            if not avail or "anthropic" in avail:
                return "anthropic", "URL 为 Anthropic 官方端点"
        # 路径含 /anthropic（bigmodel/zai/deepseek/volcengine/openrouter 等兼容端点）
        if "/anthropic" in path or path.endswith("anthropic"):
            if not avail or "anthropic" in avail:
                return "anthropic", "URL 路径含 /anthropic"
        # OpenRouter：/api/v1 → openai；/api（无 v1）常作 anthropic 兼容
        if "openrouter" in host or "openrouter" in url:
            if path.endswith("/api") or path.rstrip("/").endswith("/api"):
                if not avail or "anthropic" in avail:
                    return "anthropic", "OpenRouter Anthropic 兼容路径"
            if not avail or "openai" in avail:
                return "openai", "OpenRouter OpenAI 兼容路径"

        # 与 catalog 协议 base_url 比对
        if avail:
            best_proto, best_score = "", -1
            uh, up = host, path
            for proto, cfg in avail.items():
                if not isinstance(cfg, dict):
                    continue
                bh, bp = _url_parts(cfg.get("base_url") or "")
                if not bh:
                    continue
                score = 0
                if uh == bh and up == bp:
                    score = 100
                elif uh == bh and (up.startswith(bp) or bp.startswith(up)):
                    score = 90
                elif uh == bh:
                    score = 60
                if score > best_score:
                    best_score = score
                    best_proto = proto
            if best_proto and best_score >= 60:
                return best_proto, f"URL 匹配 {best_proto} 端点"

    if avail:
        if "openai" in avail:
            return "openai", "默认 OpenAI 兼容协议"
        return next(iter(avail.keys())), "取厂商首个可用协议"
    return "openai", "默认 OpenAI 兼容协议"


def load_provider_catalog(example_path: Path) -> List[Dict[str, Any]]:
    """从 llm-env-example.yaml 解析 provider 预设列表。"""
    if not example_path.exists():
        return []
    data = load_env_config_file(example_path) or {}
    llm = data.get("llm") or {}
    catalog: List[Dict[str, Any]] = []
    for name, block in llm.items():
        if name.startswith("_") or name == "proxy":
            continue
        if not isinstance(block, dict):
            continue
        protocols: Dict[str, Any] = {}
        for proto, cfg in block.items():
            if not isinstance(cfg, dict):
                continue
            if not any(k in cfg for k in ("base_url", "api_key", "models")):
                continue
            protocols[proto] = {
                "base_url": cfg.get("base_url") or "",
                "models": dict(cfg.get("models") or {}),
            }
        if not protocols:
            continue
        meta = _meta(name)
        catalog.append({
            "provider": name,
            "label": meta["label"],
            "family": meta["family"],
            "protocols": protocols,
            "suggested_protocol": _suggest_protocol(protocols),
            "active_protocol": "|".join(protocols.keys()),
        })
    return catalog


def catalog_as_map(catalog: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {c["provider"]: c for c in catalog}


def _suggest_protocol(protocols: Dict[str, Any]) -> str:
    if "openai" in protocols:
        return "openai"
    if "anthropic" in protocols:
        return "anthropic"
    return next(iter(protocols.keys()), "openai")


def _url_match(url: str, rule: Dict[str, Any]) -> bool:
    if not url:
        return False
    includes = rule.get("url_includes") or []
    if includes and not any(s in url for s in includes):
        return False
    requires = rule.get("url_requires") or []
    if requires and not all(s in url for s in requires):
        return False
    excludes = rule.get("url_excludes") or []
    if excludes and any(s in url for s in excludes):
        return False
    return bool(includes or requires)


def _key_match(key: str, rule: Dict[str, Any]) -> bool:
    prefixes = rule.get("key_prefixes") or []
    return bool(prefixes) and any(key.startswith(p) for p in prefixes)


def match_catalog_endpoints(
    base_url: str,
    catalog: List[Dict[str, Any]],
) -> List[Tuple[str, str, int]]:
    """用 URL 直接匹配 catalog 中各协议端点。

    返回 [(provider, protocol, score), ...] 按 score 降序。
    """
    url = _norm_url(base_url)
    if not url:
        return []
    uh, up = _url_parts(url)
    scored: List[Tuple[str, str, int]] = []
    for entry in catalog:
        for proto, cfg in (entry.get("protocols") or {}).items():
            bh, bp = _url_parts(cfg.get("base_url") or "")
            if not bh:
                continue
            score = 0
            if uh == bh and up == bp:
                score = 100
            elif uh == bh and bp and (up.startswith(bp) or bp.startswith(up)):
                score = 92
            elif uh == bh and bp and (bp in up or up in bp):
                score = 85
            elif uh == bh:
                score = 55
            if score >= 85:
                scored.append((entry["provider"], proto, score))
    scored.sort(key=lambda x: (-x[2], x[0], x[1]))
    return scored


def _candidate_from_catalog(
    entry: Dict[str, Any],
    *,
    score: int,
    reason: str,
    base_url_override: str = "",
    detected_protocol: str = "",
    protocol_reason: str = "",
    api_key: str = "",
) -> Dict[str, Any]:
    protocols = {}
    avail = entry.get("protocols") or {}
    if detected_protocol and detected_protocol in avail:
        suggested = detected_protocol
        p_reason = protocol_reason or f"识别为 {detected_protocol}"
    else:
        suggested, p_reason = infer_protocol(api_key, base_url_override, avail)

    for proto, cfg in avail.items():
        url = cfg.get("base_url") or ""
        if base_url_override and (proto == suggested or len(avail) == 1):
            url = base_url_override
        protocols[proto] = {
            "base_url": url,
            "models": dict(cfg.get("models") or {}),
        }

    # active：识别到明确协议时用单协议；否则保留厂商全部协议
    if detected_protocol and detected_protocol in protocols:
        active = detected_protocol
    elif suggested and (api_key.startswith("sk-ant-") or "/anthropic" in _norm_url(base_url_override)):
        active = suggested
    else:
        active = "|".join(protocols.keys()) if len(protocols) > 1 else suggested

    return {
        "provider": entry["provider"],
        "label": entry["label"],
        "family": entry["family"],
        "score": score,
        "reason": reason,
        "protocols": protocols,
        "detected_protocol": suggested,
        "protocol_reason": p_reason,
        "suggested_protocol": suggested,
        "active_protocol": active,
    }


def _fallback_custom(api_key: str, base_url: str) -> Dict[str, Any]:
    provider = "openai-compatible" if api_key.startswith("sk-") else "custom"
    meta = _meta(provider)
    proto, p_reason = infer_protocol(api_key, base_url)
    return {
        "provider": provider,
        "label": meta["label"],
        "family": meta["family"],
        "score": 10,
        "reason": "未匹配已知厂商，使用兼容预设",
        "protocols": {
            proto: {
                "base_url": base_url,
                "models": {},
            }
        },
        "detected_protocol": proto,
        "protocol_reason": p_reason,
        "suggested_protocol": proto,
        "active_protocol": proto,
    }


def detect_providers(
    api_key: str,
    base_url: str = "",
    catalog: Optional[List[Dict[str, Any]]] = None,
    example_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """根据 api_key / base_url 返回候选（含识别出的协议）。

    识别顺序：
      1. URL 精确匹配 catalog 协议端点 → 厂商+协议双确定
      2. URL/Key 规则匹配厂商，再推断协议
      3. 同家族模糊 → 多候选（各带协议推断）
      4. 通用 sk- → 多厂商候选
    """
    key = (api_key or "").strip()
    url = _norm_url(base_url)
    key_l = key.lower()
    user_url = (base_url or "").strip()

    if catalog is None:
        if example_path is None:
            raise ValueError("catalog 或 example_path 必须提供其一")
        catalog = load_provider_catalog(example_path)
    cmap = catalog_as_map(catalog)

    hits: List[Dict[str, Any]] = []
    seen = set()

    def add_provider(
        name: str,
        score: int,
        reason: str,
        *,
        override_url: Optional[str] = None,
        detected_protocol: str = "",
        protocol_reason: str = "",
    ) -> None:
        if name in seen:
            return
        entry = cmap.get(name)
        if not entry:
            return
        seen.add(name)
        hits.append(_candidate_from_catalog(
            entry,
            score=score,
            reason=reason,
            base_url_override="" if override_url is None else override_url,
            detected_protocol=detected_protocol,
            protocol_reason=protocol_reason,
            api_key=key_l,
        ))

    # 0) URL 精确匹配 catalog 端点（最强：同时锁定厂商+协议）
    if url:
        endpoint_hits = match_catalog_endpoints(user_url, catalog)
        if endpoint_hits and endpoint_hits[0][2] >= 92:
            top_score = endpoint_hits[0][2]
            exact = [h for h in endpoint_hits if h[2] >= 92 and h[2] >= top_score - 5]
            # 去重 provider，保留最高分协议
            best_by_provider: Dict[str, Tuple[str, int]] = {}
            for prov, proto, sc in exact:
                prev = best_by_provider.get(prov)
                if not prev or sc > prev[1]:
                    best_by_provider[prov] = (proto, sc)
            for prov, (proto, sc) in best_by_provider.items():
                add_provider(
                    prov, sc, f"端点匹配 {prov}/{proto}",
                    override_url=user_url,
                    detected_protocol=proto,
                    protocol_reason=f"URL 匹配 {proto} 端点",
                )
            if hits:
                hits.sort(key=lambda c: (-c["score"], c["provider"]))
                return hits

    # 1) URL 规则匹配厂商
    if url:
        for rule in DETECT_RULES:
            if _url_match(url, rule):
                rule_proto = rule.get("protocol") or ""
                if not rule_proto:
                    entry = cmap.get(rule["provider"])
                    rule_proto, p_reason = infer_protocol(
                        key_l, user_url, (entry or {}).get("protocols"),
                    )
                else:
                    p_reason = f"规则指定 {rule_proto}"
                add_provider(
                    rule["provider"], 100, f"URL 匹配 {rule['provider']}",
                    override_url=user_url,
                    detected_protocol=rule_proto,
                    protocol_reason=p_reason,
                )
                family = _meta(rule["provider"])["family"]
                requires = rule.get("url_requires") or []
                if not requires and family in FAMILY_EXPAND_ON_AMBIGUOUS:
                    for sib in FAMILY_EXPAND_ON_AMBIGUOUS[family]:
                        if sib == rule["provider"]:
                            continue
                        add_provider(
                            sib, 80, f"同家族候选（{family}）",
                            override_url=None,
                            detected_protocol=rule_proto,
                            protocol_reason=p_reason,
                        )
                break

    # 2) key 前缀
    if key_l:
        for rule in DETECT_RULES:
            if not _key_match(key_l, rule):
                continue
            if rule.get("key_only") or not url:
                rule_proto = rule.get("protocol") or ""
                entry = cmap.get(rule["provider"])
                if not rule_proto:
                    rule_proto, p_reason = infer_protocol(
                        key_l, user_url, (entry or {}).get("protocols"),
                    )
                else:
                    p_reason = f"规则指定 {rule_proto}"
                add_provider(
                    rule["provider"], 95, f"API Key 前缀匹配 {rule['provider']}",
                    override_url=user_url if user_url else None,
                    detected_protocol=rule_proto,
                    protocol_reason=p_reason,
                )

    # 3) 通用 sk-
    if not hits and key_l.startswith("sk-") and not key_l.startswith("sk-ant-") and not key_l.startswith("sk-or-"):
        for name in GENERIC_SK_CANDIDATES:
            add_provider(name, 50, "通用 sk- key，请选择厂商", override_url=None)

    if not hits:
        if key:
            hits.append(_fallback_custom(key_l, user_url))
        return hits

    hits.sort(key=lambda c: (-c["score"], c["provider"]))
    return hits


def apply_provider_to_env(
    env_data: Dict[str, Any],
    candidate: Dict[str, Any],
    api_key: str,
    *,
    set_active: bool = True,
    base_url_override: str = "",
    protocol: str = "",
) -> Dict[str, Any]:
    """将候选 preset 写入 env_data。

    protocol: 若指定则优先作为 _active_protocol / suggested；
    否则用 candidate.detected_protocol / suggested_protocol。
    """
    if "llm" not in env_data or not isinstance(env_data["llm"], dict):
        env_data["llm"] = {}
    llm = env_data["llm"]
    provider = candidate["provider"]
    existed = provider in llm and isinstance(llm.get(provider), dict)
    block = llm.get(provider) if existed else {}
    if not isinstance(block, dict):
        block = {}

    protocols = candidate.get("protocols") or {}
    detected = (
        protocol
        or candidate.get("detected_protocol")
        or candidate.get("suggested_protocol")
        or ""
    )
    applied_protos = []
    for proto, cfg in protocols.items():
        prev = block.get(proto) if isinstance(block.get(proto), dict) else {}
        use_override = bool(base_url_override) and (
            len(protocols) == 1 or proto == detected
        )
        base_url = (base_url_override if use_override else None) or cfg.get("base_url") or prev.get("base_url") or ""
        models = cfg.get("models") or prev.get("models") or {}
        block[proto] = {
            "base_url": base_url,
            "api_key": api_key,
            "models": dict(models) if isinstance(models, dict) else {},
        }
        applied_protos.append(proto)

    llm[provider] = block

    # 明确识别到协议 → active 用单协议；否则保留多协议
    if detected and detected in (protocols or block):
        active_protocol = detected
    else:
        active_protocol = candidate.get("active_protocol") or "|".join(applied_protos)

    if set_active:
        llm["_active_provider"] = provider
        llm["_active_protocol"] = active_protocol

    resolved_urls = {
        p: (block.get(p) or {}).get("base_url") or ""
        for p in applied_protos
    }
    return {
        "provider": provider,
        "protocols": applied_protos,
        "set_active": set_active,
        "existed": existed,
        "active_protocol": active_protocol,
        "detected_protocol": detected or (applied_protos[0] if applied_protos else "openai"),
        "suggested_protocol": detected or (applied_protos[0] if applied_protos else "openai"),
        "protocol_reason": candidate.get("protocol_reason") or "",
        "base_urls": resolved_urls,
        "base_url": resolved_urls.get(active_protocol)
            or resolved_urls.get(detected)
            or next(iter(resolved_urls.values()), ""),
    }
