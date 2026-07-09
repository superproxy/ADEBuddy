<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useEnvStore } from '../stores/env'

const env = useEnvStore()
const { smartPicker } = storeToRefs(env)

function protocolBadge(c: { detected_protocol?: string; suggested_protocol?: string; active_protocol?: string }) {
  return c.detected_protocol || c.suggested_protocol || c.active_protocol || '?'
}
</script>

<template>
  <div
    v-if="smartPicker.visible"
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    @click.self="env.cancelSmartPicker()"
  >
    <div class="bg-white rounded-xl shadow-xl w-[92%] max-w-[560px] max-h-[80vh] overflow-hidden flex flex-col">
      <div class="px-5 py-4 border-b border-gray-100">
        <h3 class="text-sm font-semibold text-ink-900">选择模型厂商</h3>
        <p class="text-[11px] text-ink-500 mt-1">Base URL / 协议 / 模型将由管道自动配置，只需选择厂商</p>
      </div>
      <div class="px-5 py-3 overflow-auto space-y-2 flex-1">
        <button
          v-for="c in smartPicker.candidates"
          :key="c.provider"
          type="button"
          class="w-full text-left border border-ink-300 rounded-lg px-3 py-2.5 hover:border-brand-500 hover:bg-brand-50/40 transition"
          :class="smartPicker.selected === c.provider ? 'border-brand-500 bg-brand-50/60 ring-1 ring-brand-500' : ''"
          @click="smartPicker.selected = c.provider"
        >
          <div class="flex items-center justify-between gap-2">
            <div>
              <div class="text-sm font-medium text-ink-900">{{ c.label || c.provider }}</div>
              <div class="text-[11px] text-ink-500 mt-0.5 font-mono">{{ c.provider }}</div>
            </div>
            <span
              class="px-2 py-0.5 text-[10px] font-semibold rounded shrink-0"
              :class="protocolBadge(c) === 'anthropic' ? 'bg-orange-50 text-orange-700' : 'bg-emerald-50 text-emerald-700'"
            >{{ protocolBadge(c) }}</span>
          </div>
          <div class="mt-1.5 space-y-0.5">
            <div
              v-for="(pc, proto) in (c.protocols || {})"
              :key="proto"
              class="text-[10px] font-mono truncate"
              :class="proto === protocolBadge(c) ? 'text-brand-600 font-medium' : 'text-ink-500'"
            >
              {{ proto === protocolBadge(c) ? '▸ ' : '  ' }}{{ proto }}: {{ pc.base_url || '(空)' }}
            </div>
          </div>
          <div v-if="c.protocol_reason" class="text-[10px] text-brand-600 mt-1">协议：{{ c.protocol_reason }}</div>
          <div v-else-if="c.reason" class="text-[10px] text-ink-500 mt-1">{{ c.reason }}</div>
        </button>
      </div>
      <div class="px-5 py-3 border-t border-gray-100 flex justify-end gap-2">
        <button
          type="button"
          class="px-3 py-1.5 text-xs bg-ink-100 rounded-md hover:bg-ink-300"
          @click="env.cancelSmartPicker()"
        >
          取消
        </button>
        <button
          type="button"
          class="px-3 py-1.5 text-xs bg-brand-500 text-white rounded-md hover:bg-brand-600 font-medium disabled:opacity-50"
          :disabled="!smartPicker.selected || smartPicker.applying"
          @click="env.confirmSmartPicker()"
        >
          {{ smartPicker.applying ? '写入中…' : '确认并验证' }}
        </button>
      </div>
    </div>
  </div>
</template>
