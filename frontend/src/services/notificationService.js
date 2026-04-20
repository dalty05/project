import { ref } from "vue"

const notification = ref({
  show: false,
  message: "",
  type: "" // success | error
})

export const useNotification = () => {
  const showNotification = (message, type = "success") => {
    notification.value = {
      show: true,
      message,
      type
    }

    // auto hide after 3 seconds
    setTimeout(() => {
      notification.value.show = false
    }, 3000)
  }

  return {
    notification,
    showNotification
  }
}