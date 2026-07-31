<template>
  <div>
    <el-alert v-if="systemError" class="system-error" type="error" :closable="false" show-icon>
      <template #title>服务请求失败</template>
      {{ systemError.message }}
      <span v-if="systemError.requestId">（请求ID: {{ systemError.requestId }}）</span>
      <el-button size="small" @click="retry">重新加载</el-button>
    </el-alert>
    <router-view v-slot="{ Component }">
      <transition name="fade-slide" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const systemError = ref(null)
const onError = (event) => { systemError.value = event.detail }

onMounted(() => {
  window.addEventListener('edumgmt:api-error', onError)
})
onBeforeUnmount(() => {
  window.removeEventListener('edumgmt:api-error', onError)
})
function retry() { window.location.reload() }
</script>

<style scoped>
.system-error {
  position: fixed;
  z-index: 5000;
  top: 12px;
  left: 50%;
  width: min(680px, calc(100vw - 24px));
  transform: translateX(-50%);
  box-shadow: var(--shadow-lg);
}
</style>
