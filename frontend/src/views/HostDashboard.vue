<template>
  <div>
    <!-- NAV -->
    <nav class="navbar">
      <div class="nav-logo">Host Dashboard</div>
      <ul class="nav-menu">
        <li class="nav-item dropdown">
          <span>Events ▾</span>
          <ul class="dropdown-menu">
            <li @click="switchSection('create')">Create Event</li>
            <li @click="switchSection('myEvents')">My Events</li>
            <li @click="switchSection('allEvents')">All Events</li>
          </ul>
        </li>
        <li class="nav-item cursor-pointer" @click="switchSection('venues')">
          <span>Venues 🏢</span>
        </li>
        <li class="nav-item cursor-pointer" @click="switchSection('inbox')">
          <span>Inbox 📥 <span v-if="inbox.length > 0" class="inbox-badge">{{ inbox.length }}</span></span>
        </li>
        <li class="nav-item dropdown">
          <span>👤 {{ user?.first_name || user?.username }} ▾</span>
          <ul class="dropdown-menu">
            <li @click="showProfileModal = true">My Profile</li>
            <li @click="logout">Logout</li>
          </ul>
        </li>
      </ul>
    </nav>

    <!-- ✨ AESTHETIC UPGRADE: Centered Container Wrapper -->
    <main class="container centered-layout">
      
      <!-- ================= CREATE EVENT ================= -->
      <section v-if="activeSection === 'create'" class="card">
        <h3 class="section-title">Create New Event</h3>
        <div class="form-container">
          <div class="form-group">
            <label>Event Title</label>
            <input v-model="form.title" placeholder="e.g. Computer Science Seminar" />
          </div>
          <div class="form-group">
            <label>Date</label>
            <input type="date" v-model="form.date" />
          </div>
          <div class="form-row">
            <div class="form-group half">
              <label>Start Time</label>
              <input type="time" v-model="form.start_time" />
            </div>
            <div class="form-group half">
              <label>End Time</label>
              <input type="time" v-model="form.end_time" />
            </div>
          </div>
          <div class="form-group">
            <label>Venue / Location</label>
            <select v-model="form.venue_id">
              <option disabled value="">-- Select Venue --</option>
              <option v-for="v in venues" :key="v.id" :value="v.id">{{ v.name }} ({{ v.location }} | Cap: {{ v.capacity }})</option>
            </select>
          </div>
          <div class="form-group">
            <label>Maximum Capacity</label>
            <input type="number" v-model="form.max_capacity" placeholder="Leave blank for unlimited RSVP" />
          </div>
          <button class="btn-primary full-width-btn" @click="handleCreateEvent">Create Event</button>
        </div>
      </section>

      <!-- ================= INBOX ================= -->
      <section v-if="activeSection === 'inbox'" class="card">
        <h3 class="section-title">Venue Swap Requests</h3>
        <div v-if="inbox.length === 0" class="empty-state">No pending requests at the moment.</div>
        <div class="request-grid" v-else>
          <div class="request-card" v-for="req in inbox" :key="req.request_id">
            <h4>🔄 Swap Request</h4>
            <p><strong>{{ req.req_first }} {{ req.req_last }}</strong> wants to use your room!</p>
            <hr>
            <p>They requested the room for: <strong>{{ req.req_title }}</strong></p>
            <p>This conflicts with: <strong>{{ req.tgt_title }}</strong></p>
            <p>📅 <strong>{{ req.req_date }}</strong> | ⏰ <strong>{{ req.req_start }} - {{ req.req_end }}</strong></p>
            <div class="action-buttons mt-2">
              <button class="btn-success" @click="handleRespond(req.request_id, 'approve')">✅ Approve</button>
              <button class="btn-danger" @click="handleRespond(req.request_id, 'reject')">❌ Reject</button>
            </div>
          </div>
        </div>
      </section>

      <!-- ================= MY EVENTS ================= -->
      <section v-if="activeSection === 'myEvents'" class="card">
        <h3 class="section-title">My Events</h3>
        <div class="controls-section">
          <input type="text" v-model="searchQuery" placeholder="🔍 Search Title or Venue..." class="search-input"/>
          <div class="filter-tabs">
            <button v-for="tab in eventTabs" :key="tab" :class="['tab-btn', { active: activeEventTab === tab }]" @click="activeEventTab = tab">{{ tab }}</button>
          </div>
        </div>
        <div v-if="filteredMyEvents.length === 0" class="empty-state">No events found.</div>
        <table v-else class="table centered-table">
          <thead><tr><th>Title</th><th>Date & Time</th><th>Venue</th><th>RSVPs</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="e in filteredMyEvents" :key="e.id" :class="{'row-warning': e.status === 'needs_rescheduling'}">
              <td><strong>{{ e.title }}</strong></td>
              <td>{{ e.date }} <br><small>{{ e.start_time }} - {{ e.end_time }}</small></td>
              <td><span class="clickable-venue" @click="openVenueSchedule(e.venue)">{{ e.venue }} <small>↗</small></span></td>
              <td><strong>{{ e.rsvp_count }}</strong> / {{ e.max_capacity || '∞' }}</td>
              <td><span :class="['badge', getStatusClass(e)]">{{ formatStatus(e) }}</span></td>
              <td class="action-buttons">
                <button class="btn-sm btn-info" @click="viewEvent(e)">View</button>
                <button v-if="e.status !== 'cancelled' && e.status !== 'pending_request'" class="btn-sm btn-edit" @click="editEvent(e)">
                  {{ e.status === 'needs_rescheduling' ? 'Reschedule' : 'Edit' }}
                </button>
                <button v-if="e.status !== 'cancelled'" class="btn-sm btn-danger" @click="handleCancel(e)">Cancel</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- ================= ALL EVENTS ================= -->
      <section v-if="activeSection === 'allEvents'" class="card">
        <h3 class="section-title">All Campus Events</h3>
        <div class="controls-section">
          <input type="text" v-model="searchQuery" placeholder="🔍 Search Title, Venue, or Host..." class="search-input"/>
          <div class="filter-tabs">
            <button v-for="tab in eventTabs" :key="tab" :class="['tab-btn', { active: activeEventTab === tab }]" @click="activeEventTab = tab">{{ tab }}</button>
          </div>
        </div>
        <div v-if="filteredAllEvents.length === 0" class="empty-state">No events found.</div>
        <table v-else class="table centered-table">
          <thead><tr><th>Date & Time</th><th>Title</th><th>Host</th><th>Venue</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="e in filteredAllEvents" :key="e.id">
              <td><strong>{{ e.date }}</strong> <br><small>{{ e.start_time }} - {{ e.end_time }}</small></td>
              <td><strong>{{ e.title }}</strong></td>
              <td>{{ e.first_name }} {{ e.last_name }}</td>
              <td><span class="clickable-venue" @click="openVenueSchedule(e.venue)">{{ e.venue }} <small>↗</small></span></td>
              <td><span :class="['badge', getStatusClass(e)]">{{ formatStatus(e) }}</span></td>
              <td class="action-buttons">
                <button class="btn-sm btn-info" @click="viewEvent(e)">View</button>
                <button v-if="e.host === user.username && e.status !== 'cancelled' && e.status !== 'pending_request'" class="btn-sm btn-edit" @click="editEvent(e)">Edit</button>
                <button v-if="e.host === user.username && e.status !== 'cancelled'" class="btn-sm btn-danger" @click="handleCancel(e)">Cancel</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- ================= VENUES (GROUPED BY LOCATION) ================= -->
      <section v-if="activeSection === 'venues'" class="card">
        <h3 class="section-title">Campus Facilities Directory</h3>
        <div v-if="Object.keys(venuesByLocation).length === 0" class="empty-state">No venues available.</div>
        
        <!-- ✨ AESTHETIC UPGRADE: Grouped by Location -->
        <div v-for="(roomList, locName) in venuesByLocation" :key="locName" class="location-group">
          <div class="location-header">
            <h4>🏢 {{ locName }}</h4>
          </div>
          <table class="table centered-table location-table">
            <thead>
              <tr><th>Venue Name</th><th>Physical Capacity</th></tr>
            </thead>
            <tbody>
              <tr v-for="v in roomList" :key="v.id">
                <td><span class="clickable-venue" @click="openVenueSchedule(v.name)">{{ v.name }} <small>↗</small></span></td>
                <td>{{ v.capacity }} Seats</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <!-- EVENT MODAL -->
    <div v-if="selectedEvent" class="modal" @click.self="closeModal">
      <div class="modal-content">
        <h3>{{ editMode ? 'Edit Event' : 'Event Details' }}</h3>
        <div v-if="!editMode" class="modal-body">
          <p><strong>Title:</strong> {{ selectedEvent.title }}</p>
          <p><strong>Host:</strong> {{ selectedEvent.first_name }} {{ selectedEvent.last_name }}</p>
          <p><strong>Date & Time:</strong> {{ selectedEvent.date }} | {{ selectedEvent.start_time }} - {{ selectedEvent.end_time }}</p>
          <p><strong>Venue:</strong> {{ selectedEvent.venue }} ({{ selectedEvent.location }})</p>
          <p><strong>RSVPs:</strong> {{ selectedEvent.rsvp_count }} / {{ selectedEvent.max_capacity || 'Unlimited' }}</p>
          
          <div v-if="selectedEvent.host === user.username || user.role === 'admin'">
            <hr style="margin: 15px 0; border: 1px solid #ecf0f1;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h4 style="margin: 0;">👥 Enrolled Students ({{ attendees.length }})</h4>
              <button v-if="attendees.length > 0" class="btn-sm btn-primary" @click="printAttendees">🖨️ Print List</button>
            </div>
            <div class="attendees-box mt-2">
              <ul v-if="attendees.length > 0" class="attendee-list">
                <li v-for="a in attendees" :key="a.email">
                  <strong>{{ a.first_name }} {{ a.last_name }}</strong> <br>
                  <a :href="'mailto:' + a.email" style="color: #3498db; text-decoration: none; font-size: 0.85rem;">{{ a.email }}</a>
                </li>
              </ul>
              <p v-else class="empty-state-small">No one has RSVP'd yet.</p>
            </div>
          </div>
          <div class="modal-actions mt-2">
            <button v-if="selectedEvent.host === user.username && selectedEvent.status !== 'cancelled' && selectedEvent.status !== 'pending_request'" class="btn-edit" @click="editMode = true">Edit</button>
            <button class="btn-secondary" @click="closeModal">Close</button>
          </div>
        </div>

        <div v-else class="modal-body form-group">
          <div v-if="selectedEvent.status === 'needs_rescheduling'" class="alert-box">
            ⚠️ You gave up your room! Please pick a new Venue and Time.
          </div>
          <input v-model="selectedEvent.title" placeholder="Title" />
          <input type="date" v-model="selectedEvent.date" />
          <div class="form-row"><input type="time" v-model="selectedEvent.start_time" /><input type="time" v-model="selectedEvent.end_time" /></div>
          <select v-model="selectedEvent.venue_id">
            <option v-for="v in venues" :key="v.id" :value="v.id">{{ v.name }} ({{ v.location }})</option>
          </select>
          <input type="number" v-model="selectedEvent.max_capacity" placeholder="Max Capacity" />
          <div class="modal-actions">
            <button class="btn-primary" @click="updateEventHandler">Save Changes</button>
            <button class="btn-secondary" @click="closeModal">Cancel</button>
          </div>
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
              <div class="vs-date"><strong>{{ e.date }}</strong><br><span :class="['badge-sm', getStatusClass(e)]">{{ formatStatus(e) }}</span></div>
              <div class="vs-details"><div class="vs-title">{{ e.title }}</div><div class="vs-time">⏰ {{ e.start_time }} - {{ e.end_time }}</div></div>
            </li>
          </ul>
          <div v-else class="empty-state-small">No upcoming events scheduled.</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import api from "../services/api";
import { useNotification } from "../services/notificationService";

const router = useRouter();
const { showNotification } = useNotification();
const user = JSON.parse(localStorage.getItem("user"));

const activeSection = ref("myEvents"); 
const venues = ref([]);
const allEvents = ref([]); 
const myEvents = ref([]);
const inbox = ref([]); 

const form = ref({ title: "", date: "", start_time: "", end_time: "", venue_id: "", max_capacity: "" });
const selectedEvent = ref(null);
const editMode = ref(false);
const attendees = ref([]); 
const searchQuery = ref("");
const activeEventTab = ref("All");
const eventTabs =["All", "Upcoming", "Ongoing", "Completed", "Needs Rescheduling", "Pending", "Cancelled"];
const showVenueModal = ref(false);
const selectedVenue = ref("");

const showProfileModal = ref(false);
const profileForm = ref({ first_name: user?.first_name || "", last_name: user?.last_name || "", email: user?.email || "", username: user?.username || "", new_password: "" });

const loadData = async () => {
  venues.value = (await api.get("/venues")).data;
  allEvents.value = (await api.get("/events")).data;
  myEvents.value = allEvents.value.filter(e => e.host === user.username);
  inbox.value = (await api.get("/inbox")).data; 
};

const switchSection = async (section) => {
  activeSection.value = section;
  searchQuery.value = "";
  activeEventTab.value = "All";
  await loadData();
};

const handleCreateEvent = async () => {
  if (!form.value.title || !form.value.date || !form.value.start_time || !form.value.end_time || !form.value.venue_id) {
    return showNotification("All fields are required", "error");
  }
  const payload = { ...form.value, max_capacity: form.value.max_capacity ? parseInt(form.value.max_capacity) : null };
  try {
    const res = await api.post("/create_event", payload);
    showNotification(res.data.message, "success");
    form.value = { title: "", date: "", start_time: "", end_time: "", venue_id: "", max_capacity: "" };
    switchSection("myEvents");
  } catch (err) {
    if (err.response?.status === 400 && err.response?.data?.blocking_event_id) {
      if (confirm(`${err.response.data.message}\n\nWould you like to send a Swap Request?`)) {
        try {
          payload.blocking_event_id = err.response.data.blocking_event_id;
          const swapRes = await api.post("/request_swap", payload);
          showNotification(swapRes.data.message, "success");
          form.value = { title: "", date: "", start_time: "", end_time: "", venue_id: "", max_capacity: "" };
          switchSection("myEvents");
        } catch (swapErr) { showNotification("Failed to send request", "error"); }
      }
    } else { showNotification(err.response?.data?.message || "Server error", "error"); }
  }
};

const handleRespond = async (requestId, action) => {
  if (!confirm(`Are you sure you want to ${action} this request?`)) return;
  try {
    const res = await api.post(`/respond_swap/${requestId}`, { action });
    showNotification(res.data.message, "success");
    await loadData();
  } catch (err) { showNotification("Error responding", "error"); }
};

const handleCancel = async (event) => {
  if (!confirm("Are you sure you want to cancel this event?")) return;
  try { await api.put(`/cancel_event/${event.id}`); await loadData(); } 
  catch (err) { showNotification("Failed to cancel event", "error"); }
};

const updateProfile = async () => {
  try {
    const res = await api.put("/update_profile", profileForm.value);
    showNotification(res.data.message, "success");
    localStorage.setItem("user", JSON.stringify(res.data.user));
    window.location.reload(); 
  } catch (err) { showNotification(err.response?.data?.message || "Failed to update profile", "error"); }
};

const viewEvent = async (e) => { 
  selectedEvent.value = { ...e }; 
  editMode.value = false; 
  if (e.host === user.username || user.role === 'admin') {
    try { attendees.value = (await api.get(`/event_attendees/${e.id}`)).data; } 
    catch (err) { attendees.value =[]; }
  }
};
const editEvent = (e) => { selectedEvent.value = { ...e }; editMode.value = true; };
const closeModal = () => { selectedEvent.value = null; editMode.value = false; attendees.value =[]; };

const updateEventHandler = async () => {
  try {
    const payload = { ...selectedEvent.value, max_capacity: selectedEvent.value.max_capacity ? parseInt(selectedEvent.value.max_capacity) : null };
    await api.put(`/update_event/${selectedEvent.value.id}`, payload);
    showNotification("Event updated successfully", "success");
    closeModal();
    await loadData();
  } catch (err) { showNotification(err.response?.data?.message || "Update failed", "error"); }
};

const printAttendees = () => {
  const printWindow = window.open('', '', 'height=600,width=800');
  printWindow.document.write('<html><head><title>Print Attendees</title><style>body{font-family: Arial, sans-serif; padding: 20px;} table{width: 100%; border-collapse: collapse; margin-top: 20px;} th, td{border: 1px solid #ccc; padding: 10px; text-align: left;} th{background-color: #f8f9fa;}</style></head><body>');
  printWindow.document.write(`<h2>📋 Enrolled Students</h2><h3>Event: ${selectedEvent.value.title}</h3><p><strong>Date & Time:</strong> ${selectedEvent.value.date} | ${selectedEvent.value.start_time} - ${selectedEvent.value.end_time}</p>`);
  printWindow.document.write('<table><thead><tr><th>Name</th><th>Email</th></tr></thead><tbody>');
  attendees.value.forEach(a => printWindow.document.write(`<tr><td>${a.first_name} ${a.last_name}</td><td>${a.email}</td></tr>`));
  printWindow.document.write('</tbody></table></body></html>');
  printWindow.document.close();
  printWindow.focus();
  setTimeout(() => { printWindow.print(); printWindow.close(); }, 250);
};

const getDynamicStatus = (e) => {
  if (e.status === "cancelled" || e.status === "pending_request" || e.status === "needs_rescheduling") return e.status;
  const now = new Date(), start = new Date(`${e.date}T${e.start_time}`), end = new Date(`${e.date}T${e.end_time}`);
  if (now < start) return "Upcoming";
  if (now <= end) return "Ongoing";
  return "Completed";
};

const formatStatus = (e) => {
  const s = getDynamicStatus(e);
  if (s === "pending_request") return "Pending Approval";
  if (s === "needs_rescheduling") return "Needs Rescheduling";
  return s.charAt(0).toUpperCase() + s.slice(1);
};

const getStatusClass = (e) => {
  const s = getDynamicStatus(e);
  return { "Upcoming": "badge-upcoming", "Ongoing": "badge-ongoing", "Completed": "badge-completed", "cancelled": "badge-cancelled", "needs_rescheduling": "badge-warning", "pending_request": "badge-purple" }[s] || "badge-upcoming";
};

const applyFilters = (eventList) => {
  let result = eventList;
  if (activeEventTab.value !== "All") {
    result = result.filter(e => {
      const s = getDynamicStatus(e);
      if (activeEventTab.value === "Pending") return s === "pending_request";
      if (activeEventTab.value === "Needs Rescheduling") return s === "needs_rescheduling";
      if (activeEventTab.value === "Cancelled") return s === "cancelled";
      return s === activeEventTab.value;
    });
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    result = result.filter(e => e.title.toLowerCase().includes(q) || e.venue.toLowerCase().includes(q) || (e.first_name && e.first_name.toLowerCase().includes(q)));
  }
  return result.sort((a, b) => new Date(`${a.date}T${a.start_time}`) - new Date(`${b.date}T${b.start_time}`));
};

const filteredMyEvents = computed(() => applyFilters(myEvents.value));
const filteredAllEvents = computed(() => applyFilters(allEvents.value));

// ✨ COMPUTED: Groups Venues by Location Dynamically!
const venuesByLocation = computed(() => {
  const grouped = {};
  venues.value.forEach(v => {
    if (!grouped[v.location]) grouped[v.location] =[];
    grouped[v.location].push(v);
  });
  return grouped;
});

const openVenueSchedule = (vName) => { selectedVenue.value = vName; showVenueModal.value = true; };
const closeVenueModal = () => { showVenueModal.value = false; selectedVenue.value = ""; };
const venueSchedule = computed(() => allEvents.value.filter(e => e.venue === selectedVenue.value && e.status === "scheduled").sort((a, b) => new Date(`${a.date}T${a.start_time}`) - new Date(`${b.date}T${b.start_time}`)));

const logout = () => { localStorage.clear(); router.push("/login"); };
onMounted(() => loadData());
</script>

<style scoped>
/* BASE STYLES */
.navbar { display: flex; justify-content: space-between; align-items: center; background: #2c3e50; padding: 1rem 2rem; color: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
.nav-logo { font-weight: bold; font-size: 1.2rem; }
.nav-menu { list-style: none; display: flex; margin: 0; padding: 0; gap: 10px; }
.nav-item { position: relative; margin-left: 1.5rem; cursor: pointer; padding: 0.5rem; }
.cursor-pointer { cursor: pointer; }
.dropdown-menu { display: none; position: absolute; background: #34495e; list-style: none; padding: 0.5rem 0; top: 100%; right:0; min-width: 150px; border-radius: 4px; z-index: 10;}
.nav-item:hover .dropdown-menu { display: block; }
.dropdown-menu li { padding: 0.5rem 1rem; color: #fff; cursor: pointer; border-bottom: 1px solid #2c3e50;}
.dropdown-menu li:hover { background: #1a252f; }
.inbox-badge { background: #e74c3c; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.75rem; font-weight: bold; margin-left: 5px;}

/* ✨ AESTHETIC UPGRADE: Centered Layout */
.centered-layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
}
.card { 
  width: 100%; 
  max-width: 1000px; 
  background: #fff; 
  padding: 2rem; 
  border-radius: 12px; 
  margin-bottom: 2rem; 
  box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
}
.section-title {
  text-align: center;
  color: #2c3e50;
  margin-top: 0;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 10px;
}

/* FORMS (Centered Content) */
.form-container {
  max-width: 600px;
  margin: 0 auto;
}
.form-group label { display: block; font-weight: bold; color: #34495e; margin-bottom: 5px; font-size: 0.95rem; }
.form-group input, .form-group select { display: block; margin-bottom: 1rem; padding: 0.75rem; width: 100%; border: 1px solid #ccc; border-radius: 6px; outline: none; box-sizing: border-box; }
.form-group input:focus, .form-group select:focus { border-color: #3498db; }
.form-row { display: flex; gap: 15px; width: 100%; margin-bottom: 1rem;}
.form-row input { margin-bottom: 0; width: 100%; }
.half { flex: 1; }
.time-group { display: flex; align-items: center; gap: 10px; width: 100%; margin-bottom: 1rem; }
.time-group input { margin-bottom: 0; }

.btn-primary { background: #3498db; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; font-weight: bold; transition: background 0.2s;}
.btn-primary:hover { background: #2980b9; }
.btn-secondary { background: #95a5a6; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; font-weight: bold; }
.btn-success { background: #27ae60; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; cursor: pointer; font-weight: bold; }
.btn-info { background: #3498db; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; }
.btn-danger { background: #e74c3c; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; }
.btn-edit { background: #f39c12; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; }
.btn-sm { margin-right: 5px; font-size: 0.8rem; }
.mt-2 { margin-top: 1rem; }
.full-width-btn { width: 100%; padding: 1rem; font-size: 1.1rem; margin-top: 10px;}

.controls-section { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 1rem; background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; border: 1px solid #ecf0f1; }
.search-input { flex-grow: 1; min-width: 250px; max-width: 400px; padding: 0.6rem 1rem; border: 1px solid #bdc3c7; border-radius: 20px; outline: none; }
.filter-tabs { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.tab-btn { padding: 0.4rem 0.8rem; border: 1px solid #bdc3c7; background: white; color: #7f8c8d; border-radius: 20px; cursor: pointer; font-weight: bold; font-size: 0.85rem; }
.tab-btn.active { background: #3498db; color: white; border-color: #3498db; }
.empty-state { text-align: center; color: #7f8c8d; padding: 2rem 0; font-style: italic; }

/* ✨ AESTHETIC UPGRADE: Centered Tables & Location Groups */
.centered-table { width: 100%; border-collapse: collapse; margin-top: 1rem; box-shadow: 0 0 10px rgba(0,0,0,0.02); }
.centered-table th, .centered-table td { border: 1px solid #ecf0f1; padding: 1.2rem; text-align: center; } /* Text centered */
.centered-table th { background: #f8f9fa; color: #2c3e50; font-weight: bold; text-align: center; }

.location-group { margin-bottom: 2.5rem; }
.location-header { background: #2c3e50; color: white; padding: 10px 15px; border-radius: 8px 8px 0 0; }
.location-header h4 { margin: 0; font-size: 1.2rem; letter-spacing: 0.5px; }
.location-table { margin-top: 0; border-top: none; }
.location-table th, .location-table td { border: 1px solid #ecf0f1; padding: 1rem; text-align: center; }

.row-warning { background-color: #fff4e5; }
.alert-box { background: #f39c12; color: white; padding: 1rem; border-radius: 5px; margin-bottom: 1rem; font-weight: bold; text-align: center; max-width: 500px;}

.request-grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); }
.request-card { background: #f8f9fa; border-left: 4px solid #f39c12; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.request-card h4 { margin-top: 0; color: #f39c12; }
.request-card hr { border: 0; border-top: 1px solid #ecf0f1; margin: 10px 0; }

.badge { padding: 0.35rem 0.75rem; border-radius: 15px; font-size: 0.85rem; font-weight: bold; color: white; }
.badge-upcoming { background-color: #3498db; }
.badge-ongoing { background-color: #f1c40f; color: #333; }
.badge-completed { background-color: #95a5a6; }
.badge-cancelled { background-color: #e74c3c; }
.badge-warning { background-color: #e67e22; }
.badge-purple { background-color: #9b59b6; }
.badge-sm { padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.7rem; color: white; margin-top: 5px; display: inline-block; }

.clickable-venue { color: #3498db; font-weight: bold; cursor: pointer; border-bottom: 1px dashed #3498db; }

/* MODALS */
.modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); display: flex; justify-content: center; align-items: center; z-index: 1000; padding: 1rem; }
.modal-content { background: white; padding: 2rem; border-radius: 12px; width: 100%; max-width: 550px; }
.venue-modal-content { padding: 0; max-height: 80vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
.modal-header { background: #2c3e50; color: white; padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center; }
.modal-header h2 { margin: 0; font-size: 1.3rem; }
.close-btn { background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer; }
.modal-body { padding: 1.5rem; overflow-y: auto; background: #f8f9fa; }
.modal-actions { margin-top: 1.5rem; display: flex; justify-content: center; gap: 15px;}
.modal-body label { font-weight: bold; font-size: 0.9rem; color: #2c3e50; margin-bottom: 5px; display: block;}

.attendees-box { background: white; padding: 1rem; border: 1px solid #ecf0f1; border-radius: 5px; max-height: 200px; overflow-y: auto;}
.attendee-list { list-style: none; padding: 0; margin: 0; }
.attendee-list li { padding: 10px; border-bottom: 1px solid #ecf0f1; }
.attendee-list li:last-child { border-bottom: none; }

.empty-state-small { text-align: center; color: #95a5a6; padding: 2rem 0; font-style: italic; }
.venue-schedule-list { list-style: none; padding: 0; margin: 0; }
.venue-schedule-list li { background: white; border: 1px solid #ecf0f1; border-radius: 8px; margin-bottom: 1rem; display: flex; }
.vs-date { background: #ecf0f1; padding: 1rem; text-align: center; border-right: 1px solid #bdc3c7; border-radius: 8px 0 0 8px; min-width: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.vs-details { padding: 1rem; display: flex; flex-direction: column; justify-content: center; }
.vs-title { font-weight: bold; color: #34495e; margin-bottom: 0.3rem; font-size: 1.05rem; }
</style>