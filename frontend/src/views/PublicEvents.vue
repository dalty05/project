<template>
  <div>
    <!-- PUBLIC NAVBAR -->
    <nav class="navbar">
      <div class="nav-logo">Campus Events</div>
      <div class="nav-links">
        <div v-if="user" class="nav-item dropdown">
          <span class="user-greeting">👤 {{ user.first_name || user.username }} ▾</span>
          <ul class="dropdown-menu">
            <li @click="showProfileModal = true">My Profile</li>
            <li @click="openMyRSVPs">My RSVPs (Events)</li>
            <li v-if="user.role === 'admin'" @click="router.push('/admin')">Admin Dashboard</li>
            <li v-if="user.role === 'host'" @click="router.push('/host')">Host Dashboard</li>
            <li @click="logout">Logout</li>
          </ul>
        </div>
        <router-link v-else to="/login" class="login-btn">Log In / Sign Up</router-link>
      </div>
    </nav>

    <main class="container">
      <header class="header">
        <h1>Campus Event Explorer</h1>
        <p>Discover and secure your spot for upcoming events.</p>
      </header>

      <!-- CONTROLS SECTION -->
      <div class="controls-section">
        <div class="search-box">
          <input type="text" v-model="searchQuery" placeholder="🔍 Search by Title, Venue, or Host..." />
        </div>
        
        <!-- ✨ NEW: VIEW TOGGLE (Grid vs Calendar) -->
        <div class="view-toggle">
          <button :class="['toggle-btn', { active: viewMode === 'grid' }]" @click="viewMode = 'grid'">📇 Card View</button>
          <button :class="['toggle-btn', { active: viewMode === 'calendar' }]" @click="viewMode = 'calendar'">📅 Calendar View</button>
        </div>

        <div class="filter-tabs">
          <button v-for="tab in tabs" :key="tab" :class="['tab-btn', { active: activeTab === tab }]" @click="activeTab = tab">
            {{ tab }}
          </button>
        </div>
      </div>

      <div v-if="isLoading" class="loading">Loading events...</div>
      <div v-else-if="filteredEvents.length === 0" class="empty-state">No events match your current filters.</div>

      <!-- ================= 📇 GRID VIEW ================= -->
      <div v-else-if="viewMode === 'grid'" class="event-grid">
        <div class="event-card" v-for="event in filteredEvents" :key="event.id">
          <div class="event-header">
            <h3>{{ event.title }}</h3>
            <span :class="['badge', getStatusClass(event)]">{{ getStatus(event) }}</span>
          </div>
          <div class="event-body">
            <p><strong>📅 Date:</strong> {{ event.date }}</p>
            <p><strong>⏰ Time:</strong> {{ event.start_time }} - {{ event.end_time }}</p>
            <p><strong>📍 Venue:</strong> <span class="clickable-venue" @click="openVenueSchedule(event.venue)">{{ event.venue }} <small>↗</small></span></p>
            <p><strong>👤 Host:</strong> {{ event.first_name }} {{ event.last_name }}</p>
            <p class="capacity-tracker">
              🎟️ {{ event.rsvp_count }} / {{ event.max_capacity || '∞' }} Registered
              <span v-if="event.max_capacity && event.rsvp_count >= event.max_capacity" class="sold-out-text">(Sold Out)</span>
            </p>
          </div>
          <div class="event-footer" v-if="getStatus(event) === 'Upcoming'">
            <button v-if="user?.role === 'student'" class="btn-primary rsvp-btn" :disabled="event.max_capacity && event.rsvp_count >= event.max_capacity" @click="handleRSVP(event.id)">
              {{ event.max_capacity && event.rsvp_count >= event.max_capacity ? "Sold Out" : "RSVP Now" }}
            </button>
            <p v-else-if="!user" class="login-prompt"><router-link to="/login">Log in to RSVP</router-link></p>
          </div>
        </div>
      </div>

      <!-- ================= 📅 CALENDAR VIEW ================= -->
      <div v-else-if="viewMode === 'calendar'" class="calendar-container card">
        <FullCalendar :options="calendarOptions" />
      </div>
    </main>

    <!-- ✨ NEW: SINGLE EVENT DETAILS MODAL (Triggers when clicking a calendar event) -->
    <div v-if="showSingleEventModal" class="modal" @click.self="showSingleEventModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h2>📅 {{ selectedCalendarEvent.title }}</h2>
          <button class="close-btn" @click="showSingleEventModal = false">✖</button>
        </div>
        <div class="modal-body">
          <p><strong>Date:</strong> {{ selectedCalendarEvent.date }}</p>
          <p><strong>Time:</strong> {{ selectedCalendarEvent.start_time }} - {{ selectedCalendarEvent.end_time }}</p>
          <p><strong>Venue:</strong> {{ selectedCalendarEvent.venue }} ({{ selectedCalendarEvent.location }})</p>
          <p><strong>Host:</strong> {{ selectedCalendarEvent.first_name }} {{ selectedCalendarEvent.last_name }}</p>
          
          <div class="capacity-tracker mt-2" style="text-align: center;">
            🎟️ {{ selectedCalendarEvent.rsvp_count }} / {{ selectedCalendarEvent.max_capacity || '∞' }} Registered
            <span v-if="selectedCalendarEvent.max_capacity && selectedCalendarEvent.rsvp_count >= selectedCalendarEvent.max_capacity" class="sold-out-text">(Sold Out)</span>
          </div>

          <div class="modal-actions" style="margin-top: 1.5rem; text-align: center;">
            <button 
              v-if="user?.role === 'student' && getStatus(selectedCalendarEvent) === 'Upcoming'" 
              class="btn-primary rsvp-btn" 
              :disabled="selectedCalendarEvent.max_capacity && selectedCalendarEvent.rsvp_count >= selectedCalendarEvent.max_capacity"
              @click="handleRSVP(selectedCalendarEvent.id); showSingleEventModal = false;"
            >
              {{ selectedCalendarEvent.max_capacity && selectedCalendarEvent.rsvp_count >= selectedCalendarEvent.max_capacity ? "Sold Out" : "RSVP For Event" }}
            </button>
            <p v-else-if="!user && getStatus(selectedCalendarEvent) === 'Upcoming'" class="login-prompt">
              <router-link to="/login">Log in to RSVP</router-link>
            </p>
            <button class="btn-secondary" style="width: 100%; margin-top: 10px;" @click="showSingleEventModal = false">Close Window</button>
          </div>
        </div>
      </div>
    </div>

    <!-- MY RSVPs MODAL -->
    <div v-if="showRsvpModal" class="modal" @click.self="showRsvpModal = false">
      <div class="modal-content venue-modal-content">
        <div class="modal-header"><h2>🎟️ My RSVPs</h2><button class="close-btn" @click="showRsvpModal = false">✖</button></div>
        <div class="modal-body">
          <div style="display: flex; gap: 10px; margin-bottom: 15px;">
            <button :class="['btn-tab', rsvpTab === 'Enrolled' ? 'btn-active' : 'btn-inactive']" @click="rsvpTab = 'Enrolled'">🟢 Enrolled (Upcoming)</button>
            <button :class="['btn-tab', rsvpTab === 'Attended' ? 'btn-active' : 'btn-inactive']" @click="rsvpTab = 'Attended'">🎓 Attended (Completed)</button>
          </div>
          <div v-if="filteredRsvps.length === 0" class="empty-state-small">No events in this category.</div>
          <ul v-else class="venue-schedule-list">
            <li v-for="e in filteredRsvps" :key="e.id">
              <div class="vs-date"><strong>{{ e.date }}</strong><br><span :class="['badge-sm', getStatusClass(e)]">{{ getStatus(e) }}</span></div>
              <div class="vs-details"><div class="vs-title">{{ e.title }}</div><div class="vs-time">⏰ {{ e.start_time }} - {{ e.end_time }}</div><div class="vs-host">📍 {{ e.venue }} ({{ e.location }})</div></div>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- MY PROFILE MODAL -->
    <div v-if="showProfileModal" class="modal" @click.self="showProfileModal = false">
      <div class="modal-content">
        <div class="modal-header"><h2>👤 My Profile</h2><button class="close-btn" @click="showProfileModal = false">✖</button></div>
        <div class="modal-body form-group">
          <div class="form-row"><div class="form-group half"><label>First Name</label><input v-model="profileForm.first_name" /></div><div class="form-group half"><label>Last Name</label><input v-model="profileForm.last_name" /></div></div>
          <label>Email</label><input v-model="profileForm.email" type="email" />
          <label>Username</label><input v-model="profileForm.username" />
          <hr style="margin: 15px 0; border: 1px solid #ecf0f1;">
          <label>Change Password (Leave blank to keep current)</label>
          <input v-model="profileForm.new_password" type="password" placeholder="Enter new password" />
          <div class="modal-actions" style="display: flex; justify-content: space-between; margin-top: 1.5rem;">
            <div><button class="btn-primary" @click="updateProfile" style="margin-right: 10px;">Save Changes</button><button class="btn-secondary" @click="showProfileModal = false">Cancel</button></div>
            <button class="btn-danger" @click="logout">Logout</button>
          </div>
        </div>
      </div>
    </div>

    <!-- VENUE SCHEDULE MODAL -->
    <div v-if="showVenueModal" class="modal" @click.self="closeVenueModal">
      <div class="modal-content venue-modal-content">
        <div class="modal-header"><h2>📍 {{ selectedVenue }}</h2><button class="close-btn" @click="closeVenueModal">✖</button></div>
        <div class="modal-body">
          <ul v-if="venueSchedule.length > 0" class="venue-schedule-list">
            <li v-for="e in venueSchedule" :key="e.id">
              <div class="vs-date"><strong>{{ e.date }}</strong><br><span :class="['badge-sm', getStatusClass(e)]">{{ getStatus(e) }}</span></div>
              <div class="vs-details"><div class="vs-title">{{ e.title }}</div><div class="vs-time">⏰ {{ e.start_time }} - {{ e.end_time }}</div><div class="vs-host">👤 By: {{ e.first_name }} {{ e.last_name }}</div></div>
            </li>
          </ul>
          <div v-else class="empty-state-small">No upcoming events scheduled.</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import api from "../services/api";
import { useNotification } from "../services/notificationService";

// ✨ FULLCALENDAR IMPORTS
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'

const router = useRouter();
const { showNotification } = useNotification();
const userStr = localStorage.getItem("user");
const user = userStr && userStr !== "undefined" ? JSON.parse(userStr) : null;

const events = ref([]);
const isLoading = ref(true);

const searchQuery = ref("");
const activeTab = ref("Upcoming");
const tabs = ["All", "Upcoming", "Ongoing", "Completed", "Cancelled"];

// ✨ NEW: Toggle State
const viewMode = ref("grid"); // 'grid' or 'calendar'

// Modal States
const showVenueModal = ref(false);
const selectedVenue = ref("");
const showProfileModal = ref(false);
const showRsvpModal = ref(false);
const myRsvps = ref([]);
const rsvpTab = ref("Enrolled");

// ✨ NEW: Calendar Event Modal States
const showSingleEventModal = ref(false);
const selectedCalendarEvent = ref({});

const profileForm = ref({ first_name: user?.first_name || "", last_name: user?.last_name || "", email: user?.email || "", username: user?.username || "", new_password: "" });

const loadEvents = async () => {
  try { events.value = (await api.get("/events")).data; } 
  catch (error) { console.error(error); } finally { isLoading.value = false; }
};

const handleRSVP = async (eventId) => {
  try {
    const res = await api.post(`/rsvp/${eventId}`);
    showNotification(res.data.message, "success");
    await loadEvents(); 
  } catch (err) { showNotification(err.response?.data?.message || "Error RSVPing", "error"); }
};

const openMyRSVPs = async () => {
  try {
    myRsvps.value = (await api.get("/my_rsvps")).data;
    rsvpTab.value = "Enrolled";
    showRsvpModal.value = true;
  } catch (err) { showNotification("Failed to load your RSVPs", "error"); }
};

const updateProfile = async () => {
  try {
    const res = await api.put("/update_profile", profileForm.value);
    showNotification(res.data.message, "success");
    localStorage.setItem("user", JSON.stringify(res.data.user));
    window.location.reload(); 
  } catch (err) { showNotification(err.response?.data?.message || "Failed to update profile", "error"); }
};

const getStatus = (event) => {
  if (event.status === "cancelled") return "Cancelled";
  const now = new Date(), start = new Date(`${event.date}T${event.start_time}`), end = new Date(`${event.date}T${event.end_time}`);
  if (now < start) return "Upcoming";
  if (now <= end) return "Ongoing";
  return "Completed";
};

const filteredEvents = computed(() => {
  const today = new Date().toISOString().split('T')[0];
  let result = events.value.filter(e => e.date >= today); // Hide past events in grid view
  if (activeTab.value !== "All") result = result.filter(e => getStatus(e) === activeTab.value);
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim();
    result = result.filter(e => e.title.toLowerCase().includes(query) || e.venue.toLowerCase().includes(query));
  }
  return result.sort((a, b) => new Date(`${a.date}T${a.start_time}`) - new Date(`${b.date}T${b.start_time}`));
});

const filteredRsvps = computed(() => {
  if (rsvpTab.value === "Enrolled") return myRsvps.value.filter(e => getStatus(e) === "Upcoming" || getStatus(e) === "Ongoing");
  else return myRsvps.value.filter(e => getStatus(e) === "Completed" || getStatus(e) === "Cancelled");
});

// --- ✨ FULLCALENDAR CONFIGURATION ---
// We dynamically map our database events into the exact format FullCalendar needs!
const calendarEventsMap = computed(() => {
  return filteredEvents.value.map(e => {
    let bgColor = "#3498db"; // Default Blue (Upcoming)
    if (getStatus(e) === "Ongoing") bgColor = "#f1c40f"; // Yellow
    if (getStatus(e) === "Completed") bgColor = "#95a5a6"; // Gray
    if (getStatus(e) === "Cancelled") bgColor = "#e74c3c"; // Red

    return {
      id: e.id,
      title: `${e.title} @ ${e.venue}`,
      start: `${e.date}T${e.start_time}`,
      end: `${e.date}T${e.end_time}`,
      backgroundColor: bgColor,
      borderColor: bgColor,
      extendedProps: { ...e } // Store all original database info here
    };
  });
});

// When a user clicks a block on the calendar, we open our new Event Modal!
const handleCalendarEventClick = (info) => {
  selectedCalendarEvent.value = info.event.extendedProps;
  showSingleEventModal.value = true;
};

const calendarOptions = computed(() => ({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay'
  },
  events: calendarEventsMap.value,
  eventClick: handleCalendarEventClick,
  height: 'auto', // Prevents scrollbars
  eventTimeFormat: { hour: 'numeric', minute: '2-digit', meridiem: 'short' }
}));
// ----------------------------------------

const venueSchedule = computed(() => {
  if (!selectedVenue.value) return[];
  return events.value.filter(e => e.venue === selectedVenue.value && e.status !== "cancelled").filter(e => getStatus(e) === "Upcoming" || getStatus(e) === "Ongoing").sort((a, b) => new Date(`${a.date}T${a.start_time}`) - new Date(`${b.date}T${b.start_time}`));
});

const openVenueSchedule = (venueName) => { selectedVenue.value = venueName; showVenueModal.value = true; };
const closeVenueModal = () => { showVenueModal.value = false; selectedVenue.value = ""; };

const getStatusClass = (event) => {
  const status = getStatus(event);
  return { "Upcoming": "badge-upcoming", "Ongoing": "badge-ongoing", "Completed": "badge-completed", "Cancelled": "badge-cancelled" }[status];
};

const logout = () => { localStorage.clear(); window.location.href = "/login"; };
onMounted(() => { loadEvents(); });
</script>

<style scoped>
/* NAVBAR & DROPDOWN */
.navbar { display: flex; justify-content: space-between; align-items: center; background: #2c3e50; padding: 1rem 2rem; color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
.nav-logo { font-size: 1.2rem; font-weight: bold; }
.nav-links { display: flex; align-items: center; gap: 15px; }
.nav-item { position: relative; cursor: pointer; padding: 0.5rem; }
.user-greeting { font-weight: bold; color: white; }
.dropdown-menu { display: none; position: absolute; background: #34495e; list-style: none; padding: 0.5rem 0; top: 100%; right: 0; min-width: 180px; border-radius: 4px; z-index: 1000; box-shadow: 0 4px 6px rgba(0,0,0,0.2);}
.nav-item:hover .dropdown-menu { display: block; }
.dropdown-menu li { padding: 0.75rem 1rem; color: #fff; cursor: pointer; font-size: 0.9rem; border-bottom: 1px solid #2c3e50;}
.dropdown-menu li:hover { background: #1a252f; }

.login-btn { background: #3498db; color: white; padding: 0.6rem 1.2rem; border-radius: 5px; text-decoration: none; font-weight: bold; transition: background 0.3s; border: none; cursor: pointer;}
.login-btn:hover { background: #2980b9; }
.btn-danger { background: #e74c3c; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold;}
.btn-primary { background: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; transition: background 0.3s;}
.btn-primary:hover { background: #2980b9; }
.btn-secondary { background: #95a5a6; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; }

/* RSVP TABS */
.btn-tab { flex: 1; padding: 0.75rem; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: 0.3s;}
.btn-active { background: #3498db; color: white; }
.btn-inactive { background: #ecf0f1; color: #7f8c8d; }

.container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
.header { text-align: center; margin-bottom: 2rem; }
.header h1 { color: #2c3e50; margin-bottom: 0.5rem; }
.header p { color: #7f8c8d; }

/* CONTROLS & TOGGLES */
.controls-section { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem; background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 2rem; }
.search-box input { width: 100%; min-width: 250px; padding: 0.75rem 1rem; border: 1px solid #bdc3c7; border-radius: 20px; outline: none; font-size: 1rem; }
.filter-tabs { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.tab-btn { padding: 0.5rem 1rem; border: 1px solid #ecf0f1; background: #f8f9fa; color: #7f8c8d; border-radius: 20px; cursor: pointer; font-weight: bold; }
.tab-btn.active { background: #3498db; color: white; border-color: #3498db; }

/* ✨ VIEW TOGGLE CSS */
.view-toggle { display: flex; border: 1px solid #bdc3c7; border-radius: 20px; overflow: hidden; }
.toggle-btn { padding: 0.5rem 1rem; background: white; border: none; color: #7f8c8d; font-weight: bold; cursor: pointer; transition: 0.3s; }
.toggle-btn:hover { background: #ecf0f1; }
.toggle-btn.active { background: #2c3e50; color: white; }

/* FULLCALENDAR CONTAINER */
.calendar-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }

.loading, .empty-state { text-align: center; padding: 2rem; font-size: 1.2rem; color: #7f8c8d; }
.event-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.5rem; }
.event-card { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #ecf0f1; display: flex; flex-direction: column; justify-content: space-between; }
.event-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; border-bottom: 1px solid #ecf0f1; padding-bottom: 1rem; }
.event-header h3 { margin: 0; color: #2c3e50; font-size: 1.1rem; }
.event-body p { margin: 0.5rem 0; color: #34495e; font-size: 0.95rem; }
.capacity-tracker { background: #f8f9fa; padding: 0.5rem; border-radius: 5px; font-weight: bold; margin-top: 10px !important; color: #2c3e50;}
.sold-out-text { color: #e74c3c; margin-left: 5px; }
.event-footer { margin-top: 1.5rem; text-align: center; }
.rsvp-btn { width: 100%; padding: 0.8rem; background: #27ae60; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 1rem; }
.rsvp-btn:hover:not(:disabled) { background: #2ecc71; }
.rsvp-btn:disabled { background: #95a5a6; cursor: not-allowed; }
.login-prompt a { color: #3498db; font-weight: bold; text-decoration: none; }

.badge { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; color: white; }
.badge-upcoming { background-color: #3498db; }
.badge-ongoing { background-color: #f1c40f; color: #333; }
.badge-completed { background-color: #95a5a6; }
.badge-cancelled { background-color: #e74c3c; }
.clickable-venue { color: #3498db; font-weight: bold; cursor: pointer; border-bottom: 1px dashed #3498db; transition: color 0.2s; }
.clickable-venue:hover { color: #2980b9; border-bottom: 1px solid #2980b9; }

/* MODALS */
.modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); display: flex; justify-content: center; align-items: center; z-index: 2000; padding: 1rem; }
.modal-content { background: white; border-radius: 10px; width: 100%; max-width: 500px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
.venue-modal-content { padding: 0; max-height: 80vh; }
.modal-header { background: #2c3e50; color: white; padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center; }
.modal-header h2 { margin: 0; font-size: 1.3rem; }
.close-btn { background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer; transition: color 0.2s; }
.close-btn:hover { color: #e74c3c; }
.modal-body { padding: 1.5rem; overflow-y: auto; background: #f8f9fa; }
.modal-body input { width: 100%; padding: 0.75rem; border: 1px solid #bdc3c7; border-radius: 5px; margin-bottom: 1rem; outline: none; box-sizing: border-box;}
.modal-body input:focus { border-color: #3498db; }
.modal-body label { font-weight: bold; font-size: 0.9rem; color: #2c3e50; margin-bottom: 5px; display: block;}
.form-row { display: flex; gap: 10px; }
.half { flex: 1; }
.empty-state-small { text-align: center; color: #95a5a6; padding: 2rem 0; font-style: italic; }
.venue-schedule-list { list-style: none; padding: 0; margin: 0; }
.venue-schedule-list li { background: white; border: 1px solid #ecf0f1; border-radius: 8px; margin-bottom: 1rem; display: flex; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.vs-date { background: #ecf0f1; padding: 1rem; text-align: center; border-right: 1px solid #bdc3c7; border-radius: 8px 0 0 8px; min-width: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.vs-date strong { color: #2c3e50; font-size: 0.9rem; }
.vs-details { padding: 1rem; display: flex; flex-direction: column; justify-content: center; }
.vs-title { font-weight: bold; color: #34495e; margin-bottom: 0.3rem; font-size: 1.05rem; }
.vs-time, .vs-host { color: #7f8c8d; font-size: 0.85rem; }
.badge-sm { padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.7rem; color: white; margin-top: 5px; display: inline-block; }
</style>