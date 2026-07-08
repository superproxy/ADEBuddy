<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useSyncStore } from '../stores/sync'
import { useUiStore } from '../stores/ui'
import { runSse } from '../api/sse'
const props = defineProps<{ tab: string }>()
const sync = useSyncStore()
const ui = useUiStore()
const { ideList, syncTargetIdes, autoSync, syncing, dragIdeKey, dragOverIdeKey } = storeToRefs(sync)
const { onIdeDragStart, onIdeDragOver, onIdeDrop, onIdeDragEnd } = sync
async function syncCurrentScope() {
  if (syncing.value || !syncTargetIdes.value.length) return
  const scopeMap: Record<string,string> = { env: 'llm', mcp: 'mcp', skill: 'skill' }
  const scope = scopeMap[props.tab]
  if (!scope) { ui.toast('当前页面不支持同步', 'warn'); return }
  syncing.value = true
  ui.clearLog()
  for (const ide of syncTargetIdes.value) {
    await runSse('/api/init-ide?ide=' + encodeURIComponent(ide) + '&scope=' + scope, (line) => ui.appendLog(line))
  }
  syncing.value = false
  ui.toast('同步完成')
}
</script>
<template>
  <div v-show="props.tab !== 'plugin-build' && props.tab !== 'ide'" class="bg-white/10 border-t border-white/10">
    <div class="max-w-[1600px] mx-auto px-6 py-1.5 flex items-center gap-3 text-xs flex-wrap">
      <label class="flex items-center gap-1 cursor-pointer select-none text-white/90">
        <input type="checkbox" v-model="autoSync" class="w-3 h-3"> 自动同步
      </label>
      <span class="text-white/60">|</span>
      <span class="text-white/80">同步到:</span>
      <label v-for="ide in ideList" :key="ide.key" draggable="true"
        @dragstart="onIdeDragStart($event, ide.key)" @dragover="onIdeDragOver($event, ide.key)"
        @drop="onIdeDrop($event, ide.key)" @dragend="onIdeDragEnd"
        :class="['flex items-center gap-1 cursor-grab select-none text-white/80 hover:text-white px-1.5 py-0.5 rounded transition', dragIdeKey === ide.key ? 'opacity-40' : '', dragOverIdeKey === ide.key && dragIdeKey ? 'bg-white/20 ring-1 ring-white/40' : '']"
        :title="ide.desc + ' (拖动排序)'">
        <input type="checkbox" :value="ide.key" v-model="syncTargetIdes" class="w-3 h-3"> {{ ide.label }}
      </label>
      <span class="text-white/40 text-[10px]">({{ syncTargetIdes.length }} 选中)</span>
      <button @click="syncCurrentScope" :disabled="syncing || !syncTargetIdes.length"
        class="ml-auto px-3 py-1 bg-brand-500 text-white rounded hover:bg-brand-600 disabled:opacity-40 font-medium">
        {{ syncing ? '同步中...' : '同步到 IDE' }}
      </button>
    </div>
  </div>
</template>
