<template>
  <div v-if="notification.show" :class="['toast', notification.type]">
    {{ notification.message }}
  </div>
</template>

<script setup>
import { useNotification } from "../services/notificationService"

const { notification } = useNotification()
</script>

<style scoped>
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 6px;
  color: white;
  font-weight: bold;
  z-index: 1000;
}

/* Success */
.toast.success {
  background-color: #28a745;
}

/* Error */
.toast.error {
  background-color: #dc3545;
}
</style>