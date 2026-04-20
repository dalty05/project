<template>
  <div id="app">
    <!-- Vue Router will inject the current page here -->
    <router-view />
    
    <!-- We will keep the Notification globally accessible -->
    <Notification />
  </div>
</template>

<script setup>
import Notification from './components/Notification.vue'
</script>

<style>
/* Global CSS reset */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  font-family: Arial, sans-serif;
}
body {
  background-color: #f4f6f8;
}
</style>




<!-- <script setup>
import { ref } from "vue"
import Login from "./views/Login.vue"
import Dashboard from "./views/Dashboard.vue"
import Notification from "./components/Notification.vue"

const user = ref(JSON.parse(localStorage.getItem("user")))


</script>

<template>
  <Notification />



<div>

<Login v-if="!user" />
<Dashboard v-else />

</div>

</template> -->