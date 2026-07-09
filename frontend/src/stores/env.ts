import { defineStore } from 'pinia'
import { reactive, computed, ref } from 'vue'
import { api } from '../api/client'
import { runSse } from '../api/sse'
import { useUiStore } from './ui'

export interface ProviderCandidate {
  provider: string
  label?: string
  family?: string
  score?: number
  reason?: string
  protocols?: Record<string, { base_url?: string; models?: Record<string, { name?: string }> }>
  detected_protocol?: string
  protocol_reason?: string
  suggested_protocol?: string
  active_protocol?: string
}

export const useEnvStore = defineStore('env', () => {
  const ui = useUiStore()
  const envData = reactive<any>({ llm: {}, proxy: {} })
  const envDataText = reactive<Record<string, string>>({})
  const openedProviders = reactive(new Set<string>())
  const smartPicker = reactive({
    visible: false,
    candidates: [] as ProviderCandidate[],
    selected: '',
    apiKey: '',
    baseUrl: '',
    applying: false,
  })
  const smartBusy = ref(false)

  const providerNames = computed(() =>
    Object.keys(envData.llm || {}).filter(
      (k) => !k.startsWith('_') && envData.llm[k] && typeof envData.llm[k] === 'object',
    ),
  )
  const proxyEnabled = computed(() => envData.proxy && envData.proxy.enable)

  function replaceEnvData(data: any) {
    Object.keys(envData).forEach((k) => delete (envData as any)[k])
    Object.assign(envData, data || { llm: {}, proxy: {} })
    if (!envData.llm) envData.llm = {}
    if (!envData.proxy) envData.proxy = {}
    ;['embedding', 'tts', 'asr', 'vision', 'misc'].forEach((sec) => {
      envDataText[sec] = JSON.stringify((envData as any)[sec] || {}, null, 2)
    })
  }

  async function loadEnv() {
    const r = await api<{ ok: boolean; data?: any; error?: string }>('/api/llm')
    if (!r.ok) { ui.toast('加载 llm.yaml 失败: ' + r.error, 'err'); return }
    replaceEnvData(r.data)
  }
  function toggleProvider(name: string) {
    if (openedProviders.has(name)) openedProviders.delete(name)
    else openedProviders.add(name)
  }
  function updateEnvDataSection(sec: string) {
    try { (envData as any)[sec] = JSON.parse(envDataText[sec] || '{}') } catch { /* ignore */ }
  }
  function addProvider() {
    const name = prompt('请输入 Provider 名称')
    if (!name || !name.trim()) return
    const t = name.trim()
    if (envData.llm[t]) { ui.toast('Provider 已存在', 'warn'); return }
    envData.llm[t] = { openai: { base_url: '', api_key: '', models: {} } }
    if (!envData.llm._active_provider) envData.llm._active_provider = t
    ui.toast('已添加 Provider: ' + t)
  }
  function deleteProvider(name: string) {
    if (!confirm('删除 Provider "' + name + '"？')) return
    delete envData.llm[name]
    if (envData.llm._active_provider === name) envData.llm._active_provider = providerNames.value[0] || ''
    ui.toast('已删除')
  }
  function setActiveProvider(name: string) {
    envData.llm._active_provider = name
    ui.toast('Active 设为: ' + name)
  }
  function addProtocol(pn: string) {
    const proto = prompt('协议名称（如 openai/anthropic）')
    if (!proto || !proto.trim()) return
    const t = proto.trim().toLowerCase()
    if (envData.llm[pn][t]) { ui.toast('协议已存在', 'warn'); return }
    envData.llm[pn][t] = { base_url: '', api_key: '', models: {} }
  }
  function deleteProtocol(pn: string, proto: string) {
    if (confirm('删除协议 "' + proto + '"？')) delete envData.llm[pn][proto]
  }
  function addModel(pn: string, proto: string) {
    envData.llm[pn][proto].models = envData.llm[pn][proto].models || {}
    const k = 'new-model-' + Date.now()
    envData.llm[pn][proto].models[k] = { name: k }
  }
  function deleteModel(pn: string, proto: string, mk: string) {
    delete envData.llm[pn][proto].models[mk]
  }
  function renameModel(pn: string, proto: string, oldKey: string, newKey: string) {
    if (oldKey === newKey) return
    const m = envData.llm[pn][proto].models
    m[newKey] = m[oldKey]
    delete m[oldKey]
  }
  async function saveEnv(silent = false) {
    const r = await api<{ ok: boolean; error?: string }>('/api/llm', {
      method: 'POST', body: JSON.stringify({ data: envData }),
    })
    if (!silent) r.ok ? ui.toast('llm.yaml 已保存') : ui.toast('保存失败: ' + r.error, 'err')
    return r.ok
  }
  async function generateProxyConfig() {
    const sr = await api<{ ok: boolean }>('/api/llm', { method: 'POST', body: JSON.stringify({ data: envData }) })
    if (!sr.ok) { ui.toast('llm.yaml 保存失败', 'err'); return }
    const r = await api<{ ok: boolean; stdout?: string; stderr?: string }>('/api/init-env', { method: 'POST' })
    if (r.ok) {
      ui.toast('proxy/config.yaml 已生成')
      if (r.stdout) ui.showModal('init-env 输出', r.stdout + (r.stderr ? '\n--- stderr ---\n' + r.stderr : ''))
    } else { ui.toast('生成失败', 'err') }
  }
  async function startProxyServer() {
    if (!proxyEnabled.value) { ui.toast('请先开启 proxy', 'warn'); return }
    const cmd = envData.proxy.start_cmd || 'litellm --config proxy/config.yaml --port 4000'
    ui.clearLog()
    await runSse('/api/proxy/start?cmd=' + encodeURIComponent(cmd), (line) => ui.appendLog(line))
  }

  async function verifyLlm(pn: string, proto: string, silent = false) {
    const cfg = envData.llm[pn]?.[proto]
    if (!cfg || !cfg.base_url || !cfg.api_key) {
      if (!silent) ui.toast('请先填 base_url 和 api_key', 'warn')
      return false
    }
    if (!silent) ui.toast('验证中...', 'ok')
    const r = await api<{ ok: boolean; models?: string[]; error?: string }>('/api/llm/verify', {
      method: 'POST', body: JSON.stringify({ base_url: cfg.base_url, api_key: cfg.api_key, protocol: proto }),
    })
    if (r.ok) {
      if (!silent) ui.toast(`验证成功，${r.models?.length || 0} 个模型可用`)
      if (r.models && r.models.length) {
        const newModels: any = {}
        for (const m of r.models) newModels[m] = { name: m }
        cfg.models = newModels
      }
      return true
    }
    if (!silent) ui.toast('验证失败: ' + r.error, 'err')
    return false
  }

  async function applyAndVerify(candidate: ProviderCandidate, apiKey: string, baseUrl = '') {
    const detectedProto = candidate.detected_protocol || candidate.suggested_protocol || ''
    // 未显式传入 URL 时，用 catalog 预设端点（管道自动配置 Base URL）
    const catalogUrl =
      candidate.protocols?.[detectedProto]?.base_url
      || candidate.protocols?.openai?.base_url
      || candidate.protocols?.anthropic?.base_url
      || Object.values(candidate.protocols || {})[0]?.base_url
      || ''
    const effectiveUrl = (baseUrl || catalogUrl || '').trim()

    const r = await api<{
      ok: boolean
      applied?: {
        provider: string
        protocols: string[]
        detected_protocol?: string
        suggested_protocol?: string
        active_protocol?: string
        protocol_reason?: string
        existed?: boolean
      }
      data?: any
      error?: string
    }>('/api/llm/apply', {
      method: 'POST',
      body: JSON.stringify({
        api_key: apiKey,
        provider: candidate.provider,
        protocol: detectedProto || undefined,
        // 仅当用户显式提供 URL 时才覆盖；否则后端用 catalog 默认
        base_url: baseUrl.trim() || undefined,
        set_active: true,
        candidate,
      }),
    })
    if (!r.ok || !r.data) {
      ui.toast('写入失败: ' + (r.error || 'unknown'), 'err')
      return false
    }
    replaceEnvData(r.data)
    const pn = r.applied?.provider || candidate.provider
    const activeProto = r.applied?.detected_protocol || r.applied?.active_protocol || detectedProto
    const appliedUrl = envData.llm?.[pn]?.[activeProto]?.base_url || effectiveUrl
    openedProviders.add(pn)
    ui.toast(`管道：${pn} · ${activeProto} · ${appliedUrl || '(无 URL)'}，验证中…`)

    const allProtos = r.applied?.protocols?.length
      ? r.applied.protocols
      : Object.keys(envData.llm[pn] || {}).filter((k) => typeof envData.llm[pn][k] === 'object')
    const ordered = activeProto
      ? [activeProto, ...allProtos.filter((p) => p !== activeProto)]
      : allProtos

    let okCount = 0
    let verifiedProto = ''
    for (const proto of ordered) {
      const ok = await verifyLlm(pn, proto, true)
      if (ok) {
        okCount++
        if (!verifiedProto) verifiedProto = proto
        if (activeProto && proto === activeProto) break
      }
    }
    if (okCount > 0) {
      if (verifiedProto) {
        envData.llm._active_provider = pn
        envData.llm._active_protocol = verifiedProto
      }
      await saveEnv(true)
      const modelCount = Object.keys(envData.llm[pn]?.[verifiedProto || activeProto]?.models || {}).length
      ui.toast(`完成：${pn} / ${verifiedProto || activeProto} 已激活，${modelCount} 个模型`)
    } else {
      ui.toast('已写入厂商与 Base URL，但验证未通过（请检查 Key 是否有效）', 'warn')
    }
    return true
  }

  function cancelSmartPicker() {
    smartPicker.visible = false
    smartPicker.candidates = []
    smartPicker.selected = ''
    smartPicker.apiKey = ''
    smartPicker.baseUrl = ''
    smartPicker.applying = false
  }

  async function confirmSmartPicker() {
    const selected = smartPicker.candidates.find((c) => c.provider === smartPicker.selected)
    if (!selected) { ui.toast('请选择一个 Provider', 'warn'); return }
    smartPicker.applying = true
    try {
      // 选择厂商后，Base URL 一律用 catalog 预设，不再要用户填
      await applyAndVerify(selected, smartPicker.apiKey, '')
      cancelSmartPicker()
    } finally {
      smartPicker.applying = false
    }
  }

  /** 智能添加管道：只输 Key → Detect →（必要时选厂商）→ 自动填 URL → Verify → 激活 */
  async function addSmartProvider() {
    if (smartBusy.value) return
    const apiKey = prompt('请输入 API Key\n（自动识别厂商 / 协议 / Base URL / 模型）')
    if (!apiKey || !apiKey.trim()) return
    smartBusy.value = true
    try {
      const r = await api<{
        ok: boolean
        candidates?: ProviderCandidate[]
        needs_choice?: boolean
        error?: string
      }>('/api/llm/detect', {
        method: 'POST',
        body: JSON.stringify({ api_key: apiKey.trim() }),
      })
      if (!r.ok || !r.candidates?.length) {
        ui.toast('未能识别厂商: ' + (r.error || '无候选'), 'err')
        return
      }

      const top = r.candidates[0]
      const isCustom = top.provider === 'custom' || top.provider === 'openai-compatible'
      const hasCatalogUrl = Object.values(top.protocols || {}).some((p) => !!(p?.base_url))

      // 无法匹配已知厂商且无预设 URL → 才追问一次 Base URL
      let overrideUrl = ''
      if (isCustom && !hasCatalogUrl) {
        overrideUrl = (prompt(
          '未能匹配已知厂商，请补充 Base URL\n（例如 https://api.example.com/v1）',
        ) || '').trim()
        if (!overrideUrl) {
          ui.toast('已取消：自定义端点需要 Base URL', 'warn')
          return
        }
        const proto = top.detected_protocol || top.suggested_protocol || 'openai'
        top.protocols = {
          [proto]: { base_url: overrideUrl, models: {} },
        }
      }

      if ((r.needs_choice || r.candidates.length > 1) && !overrideUrl) {
        smartPicker.apiKey = apiKey.trim()
        smartPicker.baseUrl = ''
        smartPicker.candidates = r.candidates
        smartPicker.selected = r.candidates[0].provider
        smartPicker.visible = true
        return
      }
      await applyAndVerify(top, apiKey.trim(), overrideUrl)
    } finally {
      smartBusy.value = false
    }
  }

  return {
    envData, envDataText, openedProviders, providerNames, proxyEnabled,
    smartPicker, smartBusy,
    loadEnv, toggleProvider, updateEnvDataSection, addProvider, deleteProvider, setActiveProvider,
    addProtocol, deleteProtocol, addModel, deleteModel, renameModel, saveEnv,
    generateProxyConfig, startProxyServer, verifyLlm, addSmartProvider,
    cancelSmartPicker, confirmSmartPicker,
  }
})
