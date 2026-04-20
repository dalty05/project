<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>
        {{ isLoginMode ? 'Welcome Back' : 
           isRegisterMode ? 'Create Student Account' : 
           isForgotPasswordMode ? 'Reset Password' : 'Set New Password' }}
      </h2>
      
      <p v-if="isLoginMode">Sign in to manage your events</p>
      <p v-if="isRegisterMode">Join to discover and RSVP for campus events</p>
      <p v-if="isForgotPasswordMode">Enter your email to receive a temporary password</p>
      <!-- ✨ NEW WARNING MESSAGE -->
      <div v-if="isForceChangeMode" class="alert-warning">
        ⚠️ For your security, you must change your temporary password before continuing.
      </div>

      <!-- LOGIN FORM -->
      <form v-if="isLoginMode" @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label>Username</label>
          <input type="text" v-model="form.username" required placeholder="Enter username" />
        </div>
        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="form.password" required placeholder="Enter password" />
        </div>
        <button type="submit" class="btn-primary" :disabled="isLoading">
          {{ isLoading ? "Logging in..." : "Login" }}
        </button>
        <p class="toggle-link" @click="setMode('forgot')">Forgot Password?</p>
      </form>

      <!-- ✨ FORCE CHANGE PASSWORD FORM -->
      <form v-if="isForceChangeMode" @submit.prevent="handleForceChangePassword" class="auth-form">
        <div class="form-group">
          <label>New Password</label>
          <input type="password" v-model="form.new_password" required placeholder="Create a strong password" />
        </div>
        <button type="submit" class="btn-primary" :disabled="isLoading">
          {{ isLoading ? "Updating..." : "Update Password & Login" }}
        </button>
      </form>

      <!-- REGISTER FORM (STUDENTS) -->
      <form v-if="isRegisterMode" @submit.prevent="handleRegister" class="auth-form">
        <div class="form-row">
          <div class="form-group half"><label>First Name</label><input type="text" v-model="form.first_name" required /></div>
          <div class="form-group half"><label>Last Name</label><input type="text" v-model="form.last_name" required /></div>
        </div>
        <div class="form-group"><label>Email</label><input type="email" v-model="form.email" required /></div>
        <div class="form-group"><label>Username</label><input type="text" v-model="form.username" required /></div>
        <div class="form-group"><label>Password</label><input type="password" v-model="form.password" required /></div>
        <button type="submit" class="btn-primary" :disabled="isLoading">{{ isLoading ? "Registering..." : "Sign Up" }}</button>
      </form>

      <!-- FORGOT PASSWORD FORM -->
      <form v-if="isForgotPasswordMode" @submit.prevent="handleForgotPassword" class="auth-form">
        <div class="form-group">
          <label>Email Address</label>
          <input type="email" v-model="form.email" required placeholder="Enter your registered email" />
        </div>
        <button type="submit" class="btn-primary" :disabled="isLoading">{{ isLoading ? "Sending..." : "Send Reset Link" }}</button>
      </form>

      <!-- NAVIGATION LINKS -->
      <div class="auth-footer" v-if="!isForceChangeMode">
        <p v-if="isLoginMode">Don't have an account? <span class="toggle-link bold" @click="setMode('register')">Sign Up</span></p>
        <p v-if="isRegisterMode || isForgotPasswordMode">Remembered your password? <span class="toggle-link bold" @click="setMode('login')">Back to Login</span></p>
        <div class="guest-link"><router-link to="/">← Continue as Guest</router-link></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import api from "../services/api";
import { useNotification } from "../services/notificationService";

const router = useRouter();
const { showNotification } = useNotification();

const currentMode = ref("login");
const isLoginMode = computed(() => currentMode.value === "login");
const isRegisterMode = computed(() => currentMode.value === "register");
const isForgotPasswordMode = computed(() => currentMode.value === "forgot");
const isForceChangeMode = computed(() => currentMode.value === "forceChange"); // ✨ NEW MODE

const isLoading = ref(false);
const form = ref({ first_name: "", last_name: "", email: "", username: "", password: "", new_password: "" });

const setMode = (mode) => {
  currentMode.value = mode;
  form.value = { first_name: "", last_name: "", email: "", username: "", password: "", new_password: "" };
};

// Route User Based on Role Helper
const routeUser = (role) => {
  if (role === "admin") router.push("/admin");
  else if (role === "host") router.push("/host");
  else router.push("/");
};

const handleLogin = async () => {
  isLoading.value = true;
  try {
    const response = await api.post("/login", { username: form.value.username, password: form.value.password });
    
    // Save tokens and user details
    localStorage.setItem("token", response.data.access_token);
    localStorage.setItem("user", JSON.stringify(response.data.user));
    
    // ✨ NEW: INTERCEPT IF PASSWORD IS TEMPORARY
    if (response.data.user.must_change_password === 1) {
      showNotification("Temporary password detected. Please set a new one.", "warning");
      currentMode.value = "forceChange";
      return; // Stop here! Don't route them yet.
    }

    showNotification(response.data.message, "success");
    routeUser(response.data.user.role);
    
  } catch (error) {
    showNotification(error.response?.data?.message || "Login failed", "error");
  } finally {
    isLoading.value = false;
  }
};

// ✨ NEW: Handle the forced password change
const handleForceChangePassword = async () => {
  isLoading.value = true;
  try {
    const res = await api.put("/change_password", { new_password: form.value.new_password });
    showNotification(res.data.message, "success");

    // Update local storage so the system knows the password was changed
    const user = JSON.parse(localStorage.getItem("user"));
    user.must_change_password = 0;
    localStorage.setItem("user", JSON.stringify(user));

    // Proceed to their dashboard!
    routeUser(user.role);

  } catch (error) {
    showNotification(error.response?.data?.message || "Failed to update password", "error");
  } finally {
    isLoading.value = false;
  }
};

// Registration and Forgot Password Handlers
const handleRegister = async () => { /* ... */ try { const res = await api.post("/register", form.value); showNotification(res.data.message, "success"); setMode("login"); } catch (error) { showNotification(error.response?.data?.message || "Registration failed", "error"); } };
const handleForgotPassword = async () => { /* ... */ try { const res = await api.post("/reset_password", { email: form.value.email }); showNotification(res.data.message, "success"); setMode("login"); } catch (error) { showNotification(error.response?.data?.message || "Reset failed", "error"); } };
</script>

<style scoped>
/* Keeping your existing clean styles, adding the new Warning Alert */
.auth-container { display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: #f4f6f8; padding: 2rem; }
.auth-card { background: white; padding: 2.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); width: 100%; max-width: 450px; text-align: center; }
h2 { margin-bottom: 0.5rem; color: #2c3e50; }
p { color: #7f8c8d; margin-bottom: 1.5rem; }
.auth-form { text-align: left; }
.form-group { margin-bottom: 1.2rem; }
.form-row { display: flex; gap: 10px; }
.half { flex: 1; }
label { display: block; margin-bottom: 0.4rem; font-weight: bold; color: #34495e; font-size: 0.9rem; }
input { width: 100%; padding: 0.75rem; border: 1px solid #bdc3c7; border-radius: 5px; font-size: 1rem; outline: none; transition: border-color 0.3s; }
input:focus { border-color: #3498db; }

/* ✨ NEW ALERT BOX */
.alert-warning { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; padding: 15px; border-radius: 5px; font-weight: bold; margin-bottom: 20px; text-align: left; font-size: 0.9rem; }

.btn-primary { width: 100%; padding: 0.8rem; background-color: #3498db; color: white; border: none; border-radius: 5px; font-size: 1rem; font-weight: bold; cursor: pointer; transition: background 0.3s; margin-top: 0.5rem; }
.btn-primary:hover:not(:disabled) { background-color: #2980b9; }
.btn-primary:disabled { background-color: #95a5a6; cursor: not-allowed; }
.toggle-link { color: #3498db; cursor: pointer; font-size: 0.9rem; text-align: right; display: block; margin-top: 0.5rem; }
.toggle-link:hover { text-decoration: underline; }
.bold { font-weight: bold; display: inline; text-align: left; margin: 0; }
.auth-footer { margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #ecf0f1; }
.guest-link a { color: #7f8c8d; text-decoration: none; font-size: 0.9rem; font-weight: bold; }
.guest-link a:hover { color: #34495e; text-decoration: underline; }
</style>