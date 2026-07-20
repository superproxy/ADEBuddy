<script setup lang="ts">
import { onMounted, ref, nextTick } from 'vue'
import { useKeysStore } from '../stores/keys'
import { useUiStore } from '../stores/ui'

const ui = useUiStore()
const keys = useKeysStore() as any
const { keysData, keysPath, keyEntries, keyCount, listQuery, selectedKey, selectedEntry, draft, isAdding } = keys

const newValueInput = ref<HTMLInputElement | null>(null)
const newKeyInput = ref<HTMLInputElement | null>(null)

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
    newValueInput.value?.focus()
  }
}

function handleCancelAdd() {
  keys.cancelAdd()
}

function handleSaveAll() {
  keys.saveKeys()
}

function handleDelete(key: string) {
  keys.deleteKey(key)
}

function onValueInput(key: string, e: Event) {
  keys.updateValue(key, (e.target as HTMLInputElement).value)
}

function onDescriptionInput(key: string, e: Event) {
  keys.updateDescription(key, (e.target as HTMLTextAreaElement).value)
}

function onRowClick(key: string) {
  keys.selectKey(key)
}

function reveal(e: Event) {
  const input = e.target as HTMLInputElement
  input.type = input.type === 'password' ? 'text' : 'password'
}

function revealById(id: string) {
  const el = document.getElementById(id) as HTMLInputElement | null
  if (el) el.type = el.type === 'password' ? 'text' : 'password'
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
    newValueInput.value?.focus()
  } else if (e.key === 'Escape') {
    handleCancelAdd()
  }
}

function onNewValueEnter(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    handleCommitAdd()
  } else if (e.key === 'Escape') {
    handleCancelAdd()
  }
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
      <div class="actions">
        <button type="button" class="btn btn-soft" @click="handleAdd" :disabled="isAdding">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
          快速添加
        </button>
        <button type="button" class="btn btn-primary" @click="handleSaveAll">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/></svg>
          全量保存
        </button>
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
    </div>

    <div class="split-layout">
      <!-- 左侧：表格列表 -->
      <section class="keys-list-pane">
        <!-- 内联新建行（顶部插入） -->
        <div v-if="isAdding" class="key-row draft-row">
          <input
            ref="newKeyInput"
            v-model="draft.key"
            type="text"
            class="key-name-input"
            placeholder="变量名（如 TAVILY_API_KEY）"
            @keydown="onNewKeyEnter"
          />
          <input
            ref="newValueInput"
            v-model="draft.value"
            type="password"
            class="value-input"
            placeholder="值（如 sk-xxx）"
            @keydown="onNewValueEnter"
          />
          <button type="button" class="btn btn-primary btn-sm" @click="handleCommitAdd">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
            确认
          </button>
          <button type="button" class="btn btn-ghost btn-sm" @click="handleCancelAdd">取消</button>
        </div>
        <div v-if="isAdding && draft.error" class="draft-error">{{ draft.error }}</div>

        <!-- 已有变量列表 -->
        <div class="keys-list">
          <div
            v-for="entry in keyEntries"
            :key="entry.key"
            class="key-row"
            :class="{ selected: selectedKey === entry.key }"
            @click="onRowClick(entry.key)"
          >
            <code class="key-name" :title="entry.key">{{ entry.key }}</code>
            <input
              :value="entry.value"
              @input="onValueInput(entry.key, $event)"
              @click.stop
              type="password"
              class="value-input"
              placeholder="请输入值（如 sk-xxx）"
            />
            <span class="desc-preview" :title="entry.description">{{ entry.description || '—' }}</span>
            <div class="row-actions" @click.stop>
              <button
                type="button"
                class="btn btn-icon btn-ghost btn-sm"
                aria-label="显示/隐藏"
                title="显示/隐藏"
                @click="reveal"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>
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
                @click="handleDelete(entry.key)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>
              </button>
            </div>
          </div>
          <div v-if="!keyCount && !isAdding" class="m-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3"/></svg>
            <p>暂无变量，点击右上方「快速添加」开始。</p>
          </div>
        </div>
      </section>

      <!-- 右侧：详情侧栏 -->
      <aside class="detail-pane">
        <div v-if="selectedEntry" class="detail-card">
          <header class="detail-head">
            <code class="detail-title">{{ selectedEntry.key }}</code>
            <span v-if="!selectedEntry.value" class="badge badge-warn">未设值</span>
            <span v-else class="badge badge-ok">已设值</span>
          </header>

          <div class="detail-field">
            <label class="field-label">描述</label>
            <textarea
              :value="selectedEntry.description"
              @input="onDescriptionInput(selectedEntry.key, $event)"
              class="desc-textarea"
              rows="3"
              placeholder="该变量的用途、获取方式、注意事项…"
            ></textarea>
          </div>

          <div class="detail-field">
            <label class="field-label">值</label>
            <div class="value-row">
              <input
                :id="'detail-value-' + selectedEntry.key"
                :value="selectedEntry.value"
                @input="onValueInput(selectedEntry.key, $event)"
                type="password"
                class="value-input"
                placeholder="请输入值"
              />
              <button
                type="button"
                class="btn btn-icon btn-ghost btn-sm"
                aria-label="显示/隐藏"
                title="显示/隐藏"
                @click="revealById('detail-value-' + selectedEntry.key)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>
              </button>
              <button
                type="button"
                class="btn btn-icon btn-ghost btn-sm"
                aria-label="复制值"
                title="复制值"
                @click="copyValue(selectedEntry.value)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </button>
            </div>
            <p class="hint">变更会自动保存到 <code>{{ keysPath || 'keys.yaml' }}</code></p>
          </div>

          <div class="detail-meta">
            <div class="meta-row"><span>变量名</span><code>{{ selectedEntry.key }}</code></div>
            <div class="meta-row"><span>引用方式</span><code>{{ '${' + selectedEntry.key + '}' }}</code></div>
            <div class="meta-row"><span>带默认值</span><code>{{ '${' + selectedEntry.key + ':-default}' }}</code></div>
          </div>

          <div class="detail-danger">
            <button type="button" class="btn btn-danger btn-sm" @click="handleDelete(selectedEntry.key)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>
              删除此变量
            </button>
          </div>
        </div>

        <div v-else class="detail-empty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 5v14M5 12h14"/></svg>
          <p>点击左侧任意变量查看详情</p>
          <p class="hint">可在右侧编辑描述、复制值、查看引用方式</p>
        </div>
      </aside>
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
.actions {
  display: flex;
  gap: 8px;
}
.actions svg {
  width: 14px;
  height: 14px;
}
.actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.split-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}
@media (max-width: 960px) {
  .split-layout {
    grid-template-columns: 1fr;
  }
}

.keys-list-pane {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.draft-row {
  background: rgba(59, 130, 246, 0.06) !important;
  border-color: var(--brand-500, #3b82f6) !important;
  border-style: dashed;
}
.draft-error {
  color: #ef4444;
  font-size: 12px;
  margin-top: -4px;
  padding-left: 12px;
}

.keys-list {
  display: grid;
  gap: 6px;
}
.key-row {
  display: grid;
  grid-template-columns: minmax(140px, 200px) minmax(0, 1fr) minmax(0, 0.8fr) auto;
  gap: 8px;
  align-items: center;
  background: var(--bg-elevated);
  border: 1px solid var(--border-base);
  border-radius: 10px;
  padding: 8px 12px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.key-row:hover {
  border-color: var(--brand-500, #3b82f6);
}
.key-row.selected {
  border-color: var(--brand-500, #3b82f6);
  background: rgba(59, 130, 246, 0.06);
  box-shadow: 0 0 0 1px var(--brand-500, #3b82f6) inset;
}
.key-name {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 12px;
  color: var(--brand-600, #2563eb);
  background: rgba(59, 130, 246, 0.08);
  padding: 4px 8px;
  border-radius: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.key-name-input {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  background: var(--bg-base);
  border: 1px solid var(--brand-500, #3b82f6);
  color: var(--brand-600, #2563eb);
}
.key-name-input:focus {
  outline: none;
}
.value-input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid var(--border-base);
  border-radius: 6px;
  font-size: 13px;
  font-family: 'SF Mono', 'Consolas', monospace;
  background: var(--bg-base);
  color: var(--text-primary);
}
.value-input:focus {
  outline: none;
  border-color: var(--brand-500, #3b82f6);
}
.desc-preview {
  font-size: 12px;
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 0 4px;
}
.row-actions {
  display: flex;
  gap: 2px;
}

.m-empty {
  text-align: center;
  padding: 48px 16px;
  color: var(--text-tertiary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  background: var(--bg-elevated);
  border: 1px dashed var(--border-base);
  border-radius: 10px;
}
.m-empty svg {
  width: 36px;
  height: 36px;
  opacity: 0.5;
}
.m-empty p {
  font-size: 13px;
  margin: 0;
}

/* === 详情侧栏 === */
.detail-pane {
  position: sticky;
  top: 0;
}
.detail-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-base);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.detail-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--border-base);
  padding-bottom: 12px;
}
.detail-title {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 14px;
  font-weight: 600;
  color: var(--brand-600, #2563eb);
  background: rgba(59, 130, 246, 0.08);
  padding: 4px 10px;
  border-radius: 6px;
  word-break: break-all;
}
.badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}
.badge-ok {
  background: rgba(34, 197, 94, 0.12);
  color: #16a34a;
}
.badge-warn {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.detail-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}
.desc-textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border-base);
  border-radius: 6px;
  font-size: 13px;
  background: var(--bg-base);
  color: var(--text-primary);
  resize: vertical;
  font-family: inherit;
  min-height: 60px;
}
.desc-textarea:focus {
  outline: none;
  border-color: var(--brand-500, #3b82f6);
}
.value-row {
  display: flex;
  gap: 4px;
  align-items: center;
}
.value-row .value-input {
  flex: 1;
}
.hint {
  font-size: 11px;
  color: var(--text-tertiary);
  margin: 0;
}
.hint code {
  background: var(--bg-base);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 10px;
}

.detail-meta {
  background: var(--bg-base);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border: 1px solid var(--border-base);
}
.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}
.meta-row span {
  color: var(--text-tertiary);
}
.meta-row code {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 11px;
  color: var(--brand-600, #2563eb);
  background: rgba(59, 130, 246, 0.08);
  padding: 2px 6px;
  border-radius: 3px;
}

.detail-danger {
  border-top: 1px solid var(--border-base);
  padding-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.detail-empty {
  text-align: center;
  padding: 48px 16px;
  color: var(--text-tertiary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  background: var(--bg-elevated);
  border: 1px dashed var(--border-base);
  border-radius: 12px;
}
.detail-empty svg {
  width: 32px;
  height: 32px;
  opacity: 0.4;
}
.detail-empty p {
  font-size: 13px;
  margin: 0;
}
.detail-empty .hint {
  font-size: 11px;
}

/* === 按钮 === */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s;
  white-space: nowrap;
}
.btn-sm {
  padding: 4px 8px;
  font-size: 11px;
}
.btn-icon {
  padding: 4px;
}
.btn-icon svg {
  width: 14px;
  height: 14px;
}
.btn-primary {
  background: var(--brand-500, #3b82f6);
  color: white;
}
.btn-primary:hover {
  background: var(--brand-600, #2563eb);
}
.btn-soft {
  background: var(--bg-elevated);
  border-color: var(--border-base);
  color: var(--text-primary);
}
.btn-soft:hover {
  background: var(--bg-hover, #f3f4f6);
}
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}
.btn-ghost:hover {
  background: var(--bg-hover, #f3f4f6);
}
.btn-danger {
  background: transparent;
  color: #ef4444;
  border-color: transparent;
}
.btn-danger:hover {
  background: rgba(239, 68, 68, 0.1);
}
</style>
