import { defineStore } from 'pinia'
import { reactive, computed, ref } from 'vue'
import { api } from '../api/client'
import { useUiStore } from './ui'

export const useKeysStore = defineStore('keys', () => {
  const ui = useUiStore()
  const keysData = reactive<any>({ mcp: {} })
  const keysPath = ref<string>('')
  const loaded = ref(false)
  const listQuery = ref('')
  const selectedKey = ref<string>('')
  // 变量引用出处：{KEY: [{source, scope, field, kind}, ...]}
  const usages = ref<{ [k: string]: Array<{ source: string; scope: string; field: string; kind: string }> }>({})
  // 新建行草稿（不进 keysData.mcp，直到提交）
  const draft = reactive<{ key: string; value: string; description: string; error: string }>({
    key: '',
    value: '',
    description: '',
    error: '',
  })
  const isAdding = ref(false)

  // 规范化为 {value, description} 形式
  function normalizeEntry(v: any): { value: string; description: string } {
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      return {
        value: typeof v.value === 'string' ? v.value : '',
        description: typeof v.description === 'string' ? v.description : '',
      }
    }
    // 旧格式：字符串
    return { value: typeof v === 'string' ? v : '', description: '' }
  }

  const keyEntries = computed(() => {
    const mcp = keysData.mcp || {}
    const q = listQuery.value.trim().toLowerCase()
    const entries = Object.entries(mcp).map(([k, v]: [string, any]) => ({
      key: k,
      ...normalizeEntry(v),
    }))
    if (!q) return entries
    return entries.filter(
      (e) =>
        e.key.toLowerCase().includes(q) ||
        e.value.toLowerCase().includes(q) ||
        e.description.toLowerCase().includes(q),
    )
  })

  const keyCount = computed(() => Object.keys(keysData.mcp || {}).length)

  const selectedEntry = computed(() => {
    if (!selectedKey.value) return null
    const v = keysData.mcp?.[selectedKey.value]
    if (v === undefined) return null
    return { key: selectedKey.value, ...normalizeEntry(v) }
  })

  async function loadKeys() {
    const r = await api('/api/keys')
    if (r.ok) {
      // 清空再赋值（保持响应式）
      Object.keys(keysData.mcp).forEach((k) => delete keysData.mcp[k])
      const data = r.data?.mcp || {}
      Object.keys(data).forEach((k) => {
        keysData.mcp[k] = normalizeEntry(data[k])
      })
      usages.value = r.usages || {}
      keysPath.value = r.path || ''
      loaded.value = true
    } else {
      ui.toast('加载密钥失败: ' + r.error, 'err')
    }
  }

  async function saveKeys() {
    const r = await api('/api/keys', { method: 'POST', body: JSON.stringify({ data: keysData }) })
    r.ok ? ui.toast('keys.yaml 已保存') : ui.toast('保存失败: ' + r.error, 'err')
  }

  /** 开始新建行（不弹窗，前端直接展示一行可编辑） */
  function startAdd() {
    draft.key = ''
    draft.value = ''
    draft.description = ''
    draft.error = ''
    isAdding.value = true
  }

  function cancelAdd() {
    isAdding.value = false
    draft.key = ''
    draft.value = ''
    draft.description = ''
    draft.error = ''
  }

  /** 提交新建行 → 调用后端 API 创建 */
  async function commitAdd() {
    const key = draft.key.trim()
    if (!key) {
      draft.error = '变量名不能为空'
      return false
    }
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(key)) {
      draft.error = '仅支持字母、数字、下划线，且不能以数字开头'
      return false
    }
    if (keysData.mcp[key]) {
      draft.error = '变量已存在'
      return false
    }
    const r = await api('/api/keys/key', {
      method: 'POST',
      body: JSON.stringify({
        key,
        value: draft.value,
        description: draft.description,
      }),
    })
    if (!r.ok) {
      draft.error = r.error || '创建失败'
      return false
    }
    keysData.mcp[key] = { value: draft.value, description: draft.description }
    selectedKey.value = key
    isAdding.value = false
    draft.key = ''
    draft.value = ''
    draft.description = ''
    draft.error = ''
    ui.toast('已添加: ' + key)
    return true
  }

  async function deleteKey(key: string) {
    const ok = await ui.askConfirm({
      title: '删除密钥？',
      message: '删除后不可恢复。',
      detail: key,
      confirmText: '确认删除',
      tone: 'danger',
    })
    if (!ok) return
    const r = await api('/api/keys/key/' + encodeURIComponent(key), { method: 'DELETE' })
    if (r.ok) {
      delete keysData.mcp[key]
      if (selectedKey.value === key) selectedKey.value = ''
      ui.toast('已删除')
    } else {
      ui.toast('删除失败: ' + r.error, 'err')
    }
  }

  /** 更新单条 value/description（PATCH 到后端） */
  async function patchEntry(key: string, patch: { value?: string; description?: string }) {
    if (!keysData.mcp[key]) return
    // 本地立即更新（保持响应式）
    const cur = normalizeEntry(keysData.mcp[key])
    const next = { ...cur, ...patch }
    keysData.mcp[key] = next
    // 后台异步持久化
    const r = await api('/api/keys/key/' + encodeURIComponent(key), {
      method: 'PATCH',
      body: JSON.stringify(patch),
    })
    if (!r.ok) ui.toast('保存失败: ' + r.error, 'err')
  }

  async function updateValue(key: string, value: string) {
    return patchEntry(key, { value })
  }

  async function updateDescription(key: string, description: string) {
    return patchEntry(key, { description })
  }

  function selectKey(key: string) {
    selectedKey.value = key
  }

  return {
    keysData,
    keysPath,
    loaded,
    listQuery,
    selectedKey,
    selectedEntry,
    draft,
    isAdding,
    usages,
    keyEntries,
    keyCount,
    loadKeys,
    saveKeys,
    startAdd,
    cancelAdd,
    commitAdd,
    addKey: startAdd, // 向后兼容
    deleteKey,
    updateValue,
    updateDescription,
    patchEntry,
    selectKey,
  }
})

