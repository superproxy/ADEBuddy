<script setup lang="ts">
import { onMounted, ref, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useKeysStore } from '../stores/keys'
import { useUiStore } from '../stores/ui'

const ui = useUiStore()
const keys = useKeysStore() as any
// 响应式 state 必须用 storeToRefs 解构，否则丢失响应式
const { keysPath, keyEntries, keyCount, listQuery, draft, isAdding, usages } = storeToRefs(keys)

const newKeyInput = ref<HTMLInputElement | null>(null)
const newValueInput = ref<HTMLInputElement | null>(null)
const newDescInput = ref<HTMLInputElement | null>(null)
// 行内可见性状态：key -> boolean（局部 UI 状态，不入 store）
const revealedRows = ref<{ [k: string]: boolean }>({})

onMounted(() => {
  keys.loadKeys()
})

async function handleAdd() {
  keys.startAdd()
  await nextTick()
  newKeyInput.value?.focus()
}

async function handleCommitAdd() {
  const ok = await keys.commitAdd()
  if (ok) {
    // 添加成功后自动展开下一个 + 行，方便连续添加
    keys.startAdd()
    await nextTick()
    newKeyInput.value?.focus()
  }
}

function handleCancelAdd() {
  keys.cancelAdd()
}

function handleDelete(key: string) {
  keys.deleteKey(key)
}

function onValueInput(key: string, e: Event) {
  keys.updateValue(key, (e.target as HTMLInputElement).value)
}

function onDescriptionInput(key: string, e: Event) {
  keys.updateDescription(key, (e.target as HTMLInputElement).value)
}

function toggleReveal(key: string) {
  revealedRows.value[key] = !revealedRows.value[key]
}

function copyValue(value: string) {
  if (!value) return
  navigator.clipboard?.writeText(value).then(() => {
    ui.toast('已复制到剪贴板')
  })
}

function onNewKeyEnter(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    // 变量名已输入 → 直接创建（值/描述留空，可在行内继续编辑）
    if (draft.value.key.trim()) {
      handleCommitAdd()
    } else {
      newValueInput.value?.focus()
    }
  } else if (e.key === 'Escape') {
    handleCancelAdd()
  }
}

// 变量名失焦：若为空则取消，否则保留草稿（不自动提交，用户可继续填值/描述）
function onNewKeyBlur() {
  setTimeout(() => {
    // 检查焦点是否已转到其他新建输入框
    const active = document.activeElement
    if (
      active !== newKeyInput.value &&
      active !== newValueInput.value &&
      active !== newDescInput.value
    ) {
      // 焦点离开了新建行：若变量名为空则取消，否则尝试提交
      if (!draft.value.key.trim()) {
        handleCancelAdd()
      }
    }
  }, 100)
}

function onNewValueEnter(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    newDescInput.value?.focus()
  } else if (e.key === 'Escape') {
    handleCancelAdd()
  }
}

function onNewDescEnter(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    handleCommitAdd()
  } else if (e.key === 'Escape') {
    handleCancelAdd()
  }
}

/** 获取变量引用出处列表 */
function getUsages(key: string): Array<{source: string; scope: string; field: string; kind: string}> {
  return usages.value[key] || []
}

/** 出处摘要：拼接为 "mcp.yaml: Redis, Tavily" 格式 */
function usagesSummary(key: string): string {
  const list = getUsages(key)
  if (!list.length) return ''
  // 按 source 分组，scope 去重
  const bySource: { [k: string]: Set<string> } = {}
  list.forEach((u) => {
    if (!bySource[u.source]) bySource[u.source] = new Set()
    bySource[u.source].add(u.scope)
  })
  return Object.entries(bySource)
    .map(([src, scopes]) => `${src}: ${[...scopes].join(', ')}`)
    .join(' | ')
}
</script>

<template>
  <div class="keys-page">
    <header class="page-head">
      <div class="head-text">
        <h1>密钥 / 环境变量</h1>
        <p class="text-xs mt-1 mb-0">
          集中管理 MCP / LLM 配置中引用的密钥与环境变量。生成 mcp.json / IDE 配置时，作为
          <code v-pre>${KEY}</code> 占位符的 fallback。
          <span class="text-ink-400">优先取 OS 环境变量，其次取此处，最后用 <code v-pre>${VAR:-default}</code> 默认值。</span>
        </p>
      </div>
    </header>

    <div class="kpi-row">
      <div class="kpi">
        <b>{{ keyCount }}</b>
        <span>变量总数</span>
        <em>{{ keysPath || 'config/mcp/keys.yaml' }}</em>
      </div>
    </div>

    <div class="toolbar">
      <input
        v-model="listQuery"
        type="search"
        class="search-input"
        placeholder="搜索变量名 / 值 / 描述…"
        aria-label="搜索"
      />
      <code v-if="keysPath" class="path-hint">{{ keysPath }}</code>
      <span class="auto-save-hint">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
        自动保存
      </span>
    </div>

    <!-- Excel 风格表格：变量名 / 值 / 描述 / 出处 / 操作 -->
    <div class="table-wrap">
      <table class="keys-table">
        <colgroup>
          <col class="col-name" />
          <col class="col-value" />
          <col class="col-desc" />
          <col class="col-usage" />
          <col class="col-actions" />
        </colgroup>
        <thead>
          <tr>
            <th>变量名</th>
            <th>值</th>
            <th>描述</th>
            <th>出处</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in keyEntries" :key="entry.key" class="data-row">
            <td class="cell-name">
              <code class="key-name" :title="entry.key">{{ entry.key }}</code>
              <span v-if="!entry.value" class="badge badge-warn">未设值</span>
            </td>
            <td class="cell-value">
              <input
                :value="entry.value"
                @input="onValueInput(entry.key, $event)"
                :type="revealedRows[entry.key] ? 'text' : 'password'"
                class="value-input"
                placeholder="请输入值（如 sk-xxx）"
              />
            </td>
            <td class="cell-desc">
              <input
                :value="entry.description"
                @input="onDescriptionInput(entry.key, $event)"
                type="text"
                class="desc-input"
                placeholder="该变量的用途、获取方式…"
              />
            </td>
            <td class="cell-usage">
              <span v-if="getUsages(entry.key).length" class="usage-list" :title="usagesSummary(entry.key)">
                <span
                  v-for="(u, idx) in getUsages(entry.key).slice(0, 3)"
                  :key="idx"
                  class="usage-chip"
                  :class="'kind-' + u.kind"
                >
                  <span class="usage-source">{{ u.source === 'mcp.yaml' ? 'MCP' : 'LLM' }}</span>
                  <span class="usage-scope">{{ u.scope }}</span>
                </span>
                <span v-if="getUsages(entry.key).length > 3" class="usage-more">+{{ getUsages(entry.key).length - 3 }}</span>
              </span>
              <span v-else class="usage-empty" title="未被任何配置引用">未使用</span>
            </td>
            <td class="cell-actions">
              <button
                type="button"
                class="btn btn-icon btn-ghost btn-sm"
                :aria-label="(revealedRows[entry.key] ? '隐藏' : '显示') + '值'"
                :title="(revealedRows[entry.key] ? '隐藏' : '显示') + '值'"
                @click="toggleReveal(entry.key)"
              >
                <svg v-if="revealedRows[entry.key]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-10-8-10-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 10 8 10 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>
              </button>
              <button
                type="button"
                class="btn btn-icon btn-ghost btn-sm"
                aria-label="复制值"
                title="复制值"
                @click="copyValue(entry.value)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </button>
              <button
                type="button"
                class="btn btn-danger btn-icon btn-sm"
                :aria-label="'删除 ' + entry.key"
                :title="'删除 ' + entry.key"
                @click="handleDelete(entry.key)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>
              </button>
            </td>
          </tr>

          <!-- 永久 + 行：点击进入新建模式 -->
          <tr v-if="!isAdding" class="add-row" @click="handleAdd" tabindex="0" @keydown.enter.prevent="handleAdd">
            <td colspan="5" class="add-placeholder">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
              <span>添加变量…</span>
            </td>
          </tr>

          <!-- 新建行（底部 + 行点击后展开） -->
          <tr v-if="isAdding" class="draft-row">
            <td class="cell-name">
              <input
                ref="newKeyInput"
                v-model="draft.key"
                type="text"
                class="key-name-input"
                placeholder="变量名（如 TAVILY_API_KEY）"
                @keydown="onNewKeyEnter"
                @blur="onNewKeyBlur"
              />
            </td>
            <td class="cell-value">
              <input
                ref="newValueInput"
                v-model="draft.value"
                type="password"
                class="value-input"
                placeholder="值（如 sk-xxx）"
                @keydown="onNewValueEnter"
              />
            </td>
            <td class="cell-desc">
              <input
                ref="newDescInput"
                v-model="draft.description"
                type="text"
                class="desc-input"
                placeholder="描述（可选）"
                @keydown="onNewDescEnter"
              />
            </td>
            <td class="cell-usage">
              <span class="usage-empty">新变量</span>
            </td>
            <td class="cell-actions">
              <span class="draft-hint">Enter 创建 · Esc 取消</span>
            </td>
          </tr>
          <tr v-if="isAdding && draft.error">
            <td colspan="5" class="draft-error">{{ draft.error }}</td>
          </tr>

          <tr v-if="!keyCount && !isAdding">
            <td colspan="5" class="m-empty">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3"/></svg>
              <p>暂无变量，点击上方「+ 添加变量…」开始。</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.keys-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}
.head-text h1 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.head-text p {
  color: var(--text-secondary);
  line-height: 1.5;
}
.head-text code {
  background: var(--bg-elevated);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--brand-600, #2563eb);
  border: 1px solid var(--border-base);
}

.kpi-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.kpi {
  background: var(--bg-elevated);
  border-radius: 10px;
  padding: 12px 16px;
  border: 1px solid var(--border-base);
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 200px;
}
.kpi b {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
}
.kpi span {
  font-size: 12px;
  color: var(--text-secondary);
}
.kpi em {
  font-size: 10px;
  color: var(--text-tertiary);
  font-style: normal;
  margin-top: 4px;
  word-break: break-all;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.search-input {
  flex: 1;
  min-width: 200px;
  max-width: 400px;
  padding: 6px 12px;
  border: 1px solid var(--border-base);
  border-radius: 8px;
  font-size: 13px;
  background: var(--bg-elevated);
  color: var(--text-primary);
}
.search-input:focus {
  outline: none;
  border-color: var(--brand-500, #3b82f6);
}
.path-hint {
  font-size: 11px;
  color: var(--text-tertiary);
  background: var(--bg-elevated);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid var(--border-base);
}
.auto-save-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-tertiary);
  margin-left: auto;
}
.auto-save-hint svg {
  width: 12px;
  height: 12px;
  color: #10b981;
}

/* 表格容器 */
.table-wrap {
  background: var(--bg-elevated);
  border: 1px solid var(--border-base);
  border-radius: 10px;
  overflow: hidden;
}
.keys-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  table-layout: fixed;
}
.keys-table thead th {
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
  background: var(--bg-base);
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-base);
}
.col-name { width: 18%; }
.col-value { width: 28%; }
.col-desc { width: 24%; }
.col-usage { width: 20%; }
.col-actions { width: 10%; }

.keys-table tbody tr {
  border-bottom: 1px solid var(--border-base);
  transition: background 0.12s;
}
.keys-table tbody tr:last-child {
  border-bottom: none;
}
.keys-table tbody tr.data-row:hover {
  background: rgba(59, 130, 246, 0.04);
}

.keys-table td {
  padding: 6px 12px;
  vertical-align: middle;
}

/* 变量名列 */
.cell-name {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.key-name {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 12px;
  color: var(--brand-600, #2563eb);
  background: rgba(59, 130, 246, 0.08);
  padding: 3px 8px;
  border-radius: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}
.key-name-input {
  width: 100%;
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 12px;
  padding: 5px 8px;
  border-radius: 4px;
  background: var(--bg-base);
  border: 1px solid var(--brand-500, #3b82f6);
  color: var(--brand-600, #2563eb);
}
.key-name-input:focus {
  outline: none;
}

/* 值列 */
.cell-value {
  padding: 4px 8px;
}
.value-input {
  width: 100%;
  padding: 5px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 13px;
  font-family: 'SF Mono', 'Consolas', monospace;
  background: transparent;
  color: var(--text-primary);
}
.value-input:hover {
  border-color: var(--border-base);
  background: var(--bg-base);
}
.value-input:focus {
  outline: none;
  border-color: var(--brand-500, #3b82f6);
  background: var(--bg-base);
}

/* 描述列 */
.cell-desc {
  padding: 4px 8px;
}
.desc-input {
  width: 100%;
  padding: 5px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 13px;
  background: transparent;
  color: var(--text-primary);
}
.desc-input:hover {
  border-color: var(--border-base);
  background: var(--bg-base);
}
.desc-input:focus {
  outline: none;
  border-color: var(--brand-500, #3b82f6);
  background: var(--bg-base);
}
.desc-input::placeholder {
  color: var(--text-tertiary);
  opacity: 0.7;
}

/* 操作列 */
.cell-actions {
  display: flex;
  gap: 2px;
  justify-content: flex-end;
  align-items: center;
}

/* 按钮基础样式（KeysView scoped，避免依赖其他 view 的 scoped 样式） */
.btn {
  height: 34px;
  padding: 0 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  white-space: nowrap;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background .18s ease, color .18s ease, border-color .18s ease;
  background: none;
  color: inherit;
  user-select: none;
}
.btn svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  stroke: currentColor;
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.btn:disabled {
  opacity: .45;
  cursor: not-allowed;
}
.btn-sm {
  height: 28px;
  padding: 0 10px;
  font-size: 11px;
  border-radius: 7px;
}
.btn-sm svg {
  width: 13px;
  height: 13px;
}
.btn-icon {
  width: 32px;
  padding: 0;
}
.btn-icon.btn-sm {
  width: 28px;
}
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}
.btn-ghost:hover:not(:disabled) {
  background: var(--bg-base);
  color: var(--text-primary);
}
.btn-danger {
  background: transparent;
  color: var(--text-tertiary);
}
.btn-danger:hover:not(:disabled),
.btn-danger:focus-visible {
  background: rgba(220, 38, 38, 0.08);
  color: #dc2626;
  border-color: rgba(220, 38, 38, 0.2);
}

/* 出处列 */
.cell-usage {
  padding: 4px 8px;
}
.usage-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
.usage-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  background: rgba(59, 130, 246, 0.08);
  color: var(--brand-600, #2563eb);
  border: 1px solid rgba(59, 130, 246, 0.2);
  max-width: 100%;
  overflow: hidden;
}
.usage-chip.kind-plaintext {
  background: rgba(16, 185, 129, 0.08);
  color: #059669;
  border-color: rgba(16, 185, 129, 0.2);
}
.usage-source {
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  opacity: 0.8;
}
.usage-scope {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100px;
}
.usage-more {
  font-size: 11px;
  color: var(--text-tertiary);
  padding: 2px 4px;
}
.usage-empty {
  font-size: 11px;
  color: var(--text-tertiary);
  font-style: italic;
  opacity: 0.7;
}

/* 徽章 */
.badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
}
.badge-warn {
  color: #d97706;
  background: rgba(245, 158, 11, 0.12);
}
.badge-ok {
  color: #059669;
  background: rgba(16, 185, 129, 0.12);
}

/* + 行 */
.add-row {
  cursor: pointer;
  outline: none;
}
.add-row:hover,
.add-row:focus-visible {
  background: rgba(59, 130, 246, 0.04);
}
.add-placeholder {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px !important;
  color: var(--text-tertiary);
  font-size: 13px;
  font-weight: 500;
}
.add-row:hover .add-placeholder,
.add-row:focus-visible .add-placeholder {
  color: var(--brand-600, #2563eb);
}
.add-placeholder svg {
  width: 14px;
  height: 14px;
}

/* 草稿行 */
.draft-row {
  background: rgba(59, 130, 246, 0.06) !important;
}
.draft-row td {
  border-top: 1px dashed var(--brand-500, #3b82f6);
  border-bottom: 1px dashed var(--brand-500, #3b82f6);
}
.draft-hint {
  font-size: 11px;
  color: var(--text-tertiary);
  white-space: nowrap;
}
.draft-error {
  color: #ef4444;
  font-size: 12px;
  padding: 6px 12px !important;
  background: rgba(239, 68, 68, 0.05);
}

/* 空状态 */
.m-empty {
  text-align: center;
  padding: 32px 12px !important;
  color: var(--text-tertiary);
}
.m-empty svg {
  width: 32px;
  height: 32px;
  margin: 0 auto 8px;
  display: block;
  opacity: 0.5;
}
.m-empty p {
  margin: 0;
  font-size: 13px;
}

/* 响应式：窄屏改为横向滚动 */
@media (max-width: 720px) {
  .table-wrap {
    overflow-x: auto;
  }
  .keys-table {
    min-width: 600px;
  }
}
</style>
