<template>
  <div>
    <!-- NAVBAR (Hidden during printing) -->
    <nav class="navbar no-print">
      <div class="nav-logo">Admin Dashboard</div>

      <ul class="nav-menu">
        <li class="nav-item cursor-pointer" @click="activeSection = 'reports'">
          <span>Reports 📊</span>
        </li>

        <li class="nav-item dropdown">
          <span>Staff Management ▾</span>
          <ul class="dropdown-menu">
            <li @click="activeSection = 'createHost'">Create Account</li>
            <li @click="activeSection = 'viewHosts'">View Staff</li>
          </ul>
        </li>

        <li class="nav-item dropdown">
          <span>Facilities ▾</span>
          <ul class="dropdown-menu">
            <li @click="activeSection = 'locations'">Manage Locations</li>
            <li @click="activeSection = 'addVenue'">Add Venue</li>
            <li @click="activeSection = 'viewVenues'">View Venues</li>
          </ul>
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

    <!-- ✨ AESTHETIC UPGRADE: Centered Container -->
    <main class="container centered-layout">

      <!-- ================= REPORT SECTION ================= -->
      <section v-if="activeSection === 'reports'" class="card print-section">
        <div class="report-header">
          <h2 style="margin:0; color:#2c3e50;">System Event Report</h2>
          <button class="btn-primary no-print" @click="printReport">🖨️ Print Report</button>
        </div>

        <!-- FILTERS -->
        <div class="controls-section no-print">
          <div class="form-row" style="max-width: 100%;">
            <div class="form-group half">
              <label>Start Date</label>
              <input type="date" v-model="filters.startDate" />
            </div>
            <div class="form-group half">
              <label>End Date</label>
              <input type="date" v-model="filters.endDate" />
            </div>
            <div class="form-group half">
              <label>Event Status</label>
              <select v-model="filters.status">
                <option value="All">All Statuses</option>
                <option value="Upcoming">Upcoming</option>
                <option value="Ongoing">Ongoing</option>
                <option value="Completed">Completed</option>
                <option value="Cancelled">Cancelled</option>
              </select>
            </div>
          </div>
          <div style="text-align: right; width: 100%;">
            <button class="btn-secondary" @click="clearFilters">Clear Filters</button>
          </div>
        </div>

        <table class="table centered-table print-table">
          <thead>
            <tr><th>Date & Time</th><th>Event Title</th><th>Host</th><th>Venue</th><th>Status</th></tr>
          </thead>
          <tbody>
            <tr v-for="e in filteredEvents" :key="e.id">
              <td><strong>{{ e.date }}</strong><br><small>{{ e.start_time }} - {{ e.end_time }}</small></td>
              <td><strong>{{ e.title }}</strong></td>
              <td>{{ e.first_name }} {{ e.last_name }}</td>
              <td>{{ e.venue }} <br><small class="text-muted">{{ e.location }}</small></td>
              <td><span :class="['badge', getStatusClass(e)]">{{ e.status === 'cancelled' ? 'Cancelled' : getStatus(e) }}</span></td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- ================= CREATE STAFF (HOST/ADMIN) ================= -->
      <section v-if="activeSection === 'createHost'" class="card no-print">
        <h3 class="section-title">Create Staff Account</h3>
        <div class="form-container">
          <div class="form-group">
            <label>Account Type / Role</label>
            <select v-model="hostForm.role">
              <option value="host">Event Host</option>
              <option value="admin">System Administrator</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group half"><label>First Name</label><input v-model="hostForm.first_name" placeholder="e.g. Jane" /></div>
            <div class="form-group half"><label>Last Name</label><input v-model="hostForm.last_name" placeholder="e.g. Doe" /></div>
          </div>
          <div class="form-group"><label>Email Address</label><input v-model="hostForm.email" type="email" placeholder="jane.doe@university.ac.ke" /></div>
          <div class="form-row">
            <div class="form-group half"><label>Username</label><input v-model="hostForm.username" placeholder="janedoe" /></div>
            <div class="form-group half"><label>Password</label><input v-model="hostForm.password" type="password" placeholder="Temporary Password" /></div>
          </div>
          <button class="btn-primary full-width-btn" @click="handleCreateHost">Create {{ hostForm.role === 'admin' ? 'Admin' : 'Host' }}</button>
        </div>
      </section>

      <!-- ================= VIEW STAFF ================= -->
      <section v-if="activeSection === 'viewHosts'" class="card no-print">
        <h3 class="section-title">Registered Staff (Hosts & Admins)</h3>
        <table class="table centered-table">
          <thead><tr><th>Name</th><th>Email</th><th>Username</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="h in hosts" :key="h.id">
              <td><strong>{{ h.first_name }} {{ h.last_name }}</strong></td>
              <td><a :href="'mailto:' + h.email" class="text-link">{{ h.email }}</a></td>
              <td>@{{ h.username }}</td>
              <td><span class="badge badge-purple">{{ (h.role || 'HOST').toUpperCase() }}</span></td>
              <td><span :class="['badge', h.status === 'active' ? 'badge-ongoing' : 'badge-cancelled']">{{ h.status.toUpperCase() }}</span></td>
              <td class="action-buttons">
                <button class="btn-sm btn-edit" @click="openEditHostModal(h)">Edit</button>
                <!-- Prevent admin from deactivating themselves -->
                <button v-if="h.username !== user.username" :class="['btn-sm', h.status === 'active' ? 'btn-danger' : 'btn-info']" @click="handleToggleHost(h)">
                  {{ h.status === 'active' ? 'Deactivate' : 'Activate' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- ================= MANAGE LOCATIONS ================= -->
      <section v-if="activeSection === 'locations'" class="card no-print">
        <h3 class="section-title">Campus Locations (Buildings/Zones)</h3>
        <div class="form-container" style="max-width: 800px;">
          <div class="form-row" style="align-items: flex-end;">
            <div class="form-group" style="flex-grow: 1; margin-bottom: 0;">
              <label>Add New Location</label>
              <input v-model="locationName" placeholder="E.g., Engineering Block, Main Library..." style="margin-bottom: 0;" />
            </div>
            <button class="btn-primary" @click="handleAddLocation" style="padding: 0.75rem 2rem;">Add</button>
          </div>
          <table class="table centered-table mt-2">
            <thead><tr><th>ID</th><th>Location Name</th></tr></thead>
            <tbody>
              <tr v-for="l in locations" :key="l.id"><td>{{ l.id }}</td><td><strong>🏢 {{ l.name }}</strong></td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ================= ADD VENUE ================= -->
      <section v-if="activeSection === 'addVenue'" class="card no-print">
        <h3 class="section-title">Add Specific Venue (Room/Hall)</h3>
        <div class="form-container">
          <div class="form-group">
            <label>Select Parent Location</label>
            <select v-model="venueForm.location_id">
              <option disabled value="">-- Choose a Location --</option>
              <option v-for="l in locations" :key="l.id" :value="l.id">{{ l.name }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group half"><label>Venue Name</label><input v-model="venueForm.name" placeholder="E.g., Room 101" /></div>
            <div class="form-group half"><label>Physical Capacity</label><input v-model="venueForm.capacity" type="number" placeholder="E.g., 50" /></div>
          </div>
          <button class="btn-primary full-width-btn" @click="handleAddVenue">Register Venue</button>
        </div>
      </section>

      <!-- ================= VIEW VENUES (GROUPED) ================= -->
      <section v-if="activeSection === 'viewVenues'" class="card no-print">
        <h3 class="section-title">Campus Facilities Directory</h3>
        <div v-if="Object.keys(venuesByLocation).length === 0" class="empty-state">No venues registered yet.</div>
        
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

    <!-- ================= MODALS ================= -->

    <!-- ✨ REDESIGNED: MY PROFILE MODAL ✨ -->
    <div v-if="showProfileModal" class="modal no-print" @click.self="showProfileModal = false">
      <div class="modal-content profile-modal">
        <div class="modal-header profile-header">
          <h2><span style="font-size: 1.5rem;">⚙️</span> Account Settings</h2>
          <button class="close-btn" @click="showProfileModal = false">✖</button>
        </div>
        
        <div class="modal-body form-group" style="padding: 2rem;">
          
          <!-- Role Badge -->
          <div class="profile-badge-container">
            <span class="badge badge-purple" style="font-size: 0.9rem; padding: 5px 15px;">{{ user?.role.toUpperCase() }} PRIVILEGES</span>
          </div>

          <!-- Section 1: Personal Details -->
          <div class="profile-section">
            <h4 class="section-subtitle">Personal Information</h4>
            <div class="form-row">
              <div class="form-group half"><label>First Name</label><input v-model="profileForm.first_name" /></div>
              <div class="form-group half"><label>Last Name</label><input v-model="profileForm.last_name" /></div>
            </div>
            <div class="form-row">
              <div class="form-group half"><label>Email Address</label><input v-model="profileForm.email" type="email" /></div>
              <div class="form-group half"><label>Username</label><input v-model="profileForm.username" /></div>
            </div>
          </div>
          
          <!-- Section 2: Security -->
          <div class="profile-section security-section">
            <h4 class="section-subtitle" style="color: #e74c3c;">Security</h4>
            <label>Change Password <span style="font-weight: normal; color: #7f8c8d;">(Leave blank to keep current)</span></label>
            <input v-model="profileForm.new_password" type="password" placeholder="Enter a new secure password" style="margin-bottom: 0;" />
          </div>
          
          <!-- Actions -->
          <div class="modal-actions profile-actions">
            <div>
              <button class="btn-primary" @click="updateProfile" style="margin-right: 10px;">💾 Save Changes</button>
              <button class="btn-secondary" @click="showProfileModal = false">Cancel</button>
            </div>
            <button class="btn-danger" @click="logout">🚪 Logout</button>
          </div>
        </div>
      </div>
    </div>

    <!-- EDIT STAFF MODAL -->
    <div v-if="showEditHostModal" class="modal no-print" @click.self="closeHostModal">
      <div class="modal-content">
        <div class="modal-header"><h2>✏️ Edit Staff: {{ selectedHost.first_name }}</h2></div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group half"><label>First Name</label><input v-model="selectedHost.first_name" /></div>
            <div class="form-group half"><label>Last Name</label><input v-model="selectedHost.last_name" /></div>
          </div>
          <div class="form-group"><label>Email</label><input v-model="selectedHost.email" type="email" /></div>
          <div class="form-row">
            <div class="form-group half"><label>Username</label><input v-model="selectedHost.username" /></div>
            <div class="form-group half"><label>New Password (Optional)</label><input v-model="selectedHost.password" type="password" /></div>
          </div>
          <div class="modal-actions" style="justify-content: center;">
            <button class="btn-primary" @click="submitHostEdit" style="margin-right:10px;">Save Changes</button>
            <button class="btn-secondary" @click="closeHostModal">Cancel</button>
          </div>
        </div>
      </div>
    </div>

    <!-- VENUE SCHEDULE MODAL -->
    <div v-if="showVenueModal" class="modal no-print" @click.self="closeVenueModal">
      <div class="modal-content venue-modal-content">
        <div class="modal-header">
          <h2>📍 {{ selectedVenue }}</h2>
          <button class="close-btn" @click="closeVenueModal">✖</button>
        </div>
        <div class="modal-body">
          <h3 style="margin-top: 0; color: #7f8c8d; font-size: 1rem; text-transform: uppercase;">Upcoming Schedule</h3>
          <div v-if="venueSchedule.length === 0" class="empty-state-small">No upcoming events scheduled.</div>
          <ul v-else class="venue-schedule-list">
            <li v-for="e in venueSchedule" :key="e.id">
              <div class="vs-date">
                <strong>{{ e.date }}</strong><br>
                <span :class="['badge-sm', getStatusClass(e)]">{{ getStatus(e) }}</span>
              </div>
              <div class="vs-details">
                <div class="vs-title">{{ e.title }}</div>
                <div class="vs-time">⏰ {{ e.start_time }} - {{ e.end_time }}</div>
                <div class="vs-host">👤 By: {{ e.first_name }} {{ e.last_name }}</div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "../services/api";
import { useNotification } from "../services/notificationService";

const router = useRouter();
const { showNotification } = useNotification();
const user = JSON.parse(localStorage.getItem("user"));

const activeSection = ref("reports");

const hosts = ref([]);
const locations = ref([]);
const venues = ref([]);
const allEvents = ref([]);

const hostForm = ref({ first_name: "", last_name: "", email: "", username: "", password: "", role: "host" });
const venueForm = ref({ name: "", location_id: "", capacity: "" });
const locationName = ref("");

const showVenueModal = ref(false);
const selectedVenue = ref("");

const showEditHostModal = ref(false);
const selectedHost = ref({});

// Profile logic
const showProfileModal = ref(false);
const profileForm = ref({ first_name: user?.first_name || "", last_name: user?.last_name || "", email: user?.email || "", username: user?.username || "", new_password: "" });

const filters = ref({ startDate: "", endDate: "", status: "All" });

onMounted(async () => { await loadAllData(); });

const loadAllData = async () => {
  try {
    venues.value = (await api.get("/venues")).data;
    allEvents.value = (await api.get("/events")).data;
    hosts.value = (await api.get("/hosts")).data;
    locations.value = (await api.get("/locations")).data;
  } catch (err) { console.error("Failed to load data"); }
};

/* --- REPORT LOGIC --- */
const getStatus = (e) => {
  const now = new Date();
  const start = new Date(`${e.date}T${e.start_time}`);
  const end = new Date(`${e.date}T${e.end_time}`);
  if (now < start) return "Upcoming";
  if (now <= end) return "Ongoing";
  return "Completed";
};

const getStatusClass = (e) => {
  const status = e.status === 'cancelled' ? 'Cancelled' : getStatus(e);
  return { "Upcoming": "badge-upcoming", "Ongoing": "badge-ongoing", "Completed": "badge-completed", "Cancelled": "badge-cancelled" }[status];
};

const filteredEvents = computed(() => {
  let result = allEvents.value;
  if (filters.value.status !== "All") result = result.filter(e => (e.status === 'cancelled' ? 'Cancelled' : getStatus(e)) === filters.value.status);
  if (filters.value.startDate) result = result.filter(e => new Date(e.date) >= new Date(filters.value.startDate));
  if (filters.value.endDate) result = result.filter(e => new Date(e.date) <= new Date(filters.value.endDate));
  return result.sort((a, b) => new Date(`${b.date}T${b.start_time}`) - new Date(`${a.date}T${a.start_time}`)); // Newest first
});

const clearFilters = () => { filters.value = { startDate: "", endDate: "", status: "All" }; };
const printReport = () => window.print();

/* --- STAFF LOGIC --- */
const handleCreateHost = async () => {
  if (!hostForm.value.username || !hostForm.value.password || !hostForm.value.email || !hostForm.value.first_name || !hostForm.value.last_name) {
    return showNotification("Please fill out all fields before creating an account.", "error");
  }
  try {
    const res = await api.post("/create_host", hostForm.value);
    showNotification(res.data.message, "success");
    hostForm.value = { first_name: "", last_name: "", email: "", username: "", password: "", role: "host" }; 
    activeSection.value = "viewHosts";
    await loadAllData();
  } catch (err) { showNotification(err.response?.data?.message || "Failed to create account.", "error"); }
};

const handleToggleHost = async (host) => {
  const action = host.status === 'active' ? 'deactivate' : 'activate';
  if (!confirm(`Are you sure you want to ${action} ${host.first_name}?`)) return;
  try {
    const res = await api.put(`/toggle_host/${host.id}`);
    showNotification(res.data.message, "success");
    await loadAllData();
  } catch (err) { showNotification("Error updating status", "error"); }
};

const openEditHostModal = (host) => { selectedHost.value = { ...host, password: "" }; showEditHostModal.value = true; };
const closeHostModal = () => { showEditHostModal.value = false; };

const submitHostEdit = async () => {
  if (!selectedHost.value.username) return showNotification("Username is required", "error");
  try {
    const res = await api.put(`/update_host/${selectedHost.value.id}`, selectedHost.value);
    showNotification(res.data.message, "success");
    closeHostModal();
    await loadAllData();
  } catch (err) { showNotification(err.response?.data?.message || "Error updating host", "error"); }
};

/* --- LOCATIONS & VENUES LOGIC --- */
const handleAddLocation = async () => {
  if (!locationName.value) return showNotification("Location name required", "error");
  try {
    const res = await api.post("/add_location", { name: locationName.value });
    showNotification(res.data.message, "success");
    locationName.value = "";
    await loadAllData();
  } catch (err) { showNotification(err.response?.data?.message || "Error adding location", "error"); }
};

const handleAddVenue = async () => {
  if (!venueForm.value.name || !venueForm.value.location_id || !venueForm.value.capacity) return showNotification("All fields required.", "error"); 
  try {
    const res = await api.post("/add_venue", venueForm.value);
    showNotification(res.data.message, "success");
    venueForm.value = { name: "", location_id: "", capacity: "" };
    activeSection.value = "viewVenues";
    await loadAllData();
  } catch (err) { showNotification(err.response?.data?.message || "Error adding venue", "error"); }
};

const venuesByLocation = computed(() => {
  const grouped = {};
  venues.value.forEach(v => {
    if (!grouped[v.location]) grouped[v.location] = [];
    grouped[v.location].push(v);
  });
  return grouped;
});

/* --- PROFILE & EXTRAS --- */
const updateProfile = async () => {
  try {
    const res = await api.put("/update_profile", profileForm.value);
    showNotification(res.data.message, "success");
    localStorage.setItem("user", JSON.stringify(res.data.user));
    window.location.reload(); 
  } catch (err) { showNotification(err.response?.data?.message || "Failed to update profile", "error"); }
};

const openVenueSchedule = (name) => { selectedVenue.value = name; showVenueModal.value = true; };
const closeVenueModal = () => { showVenueModal.value = false; selectedVenue.value = ""; };
const venueSchedule = computed(() => allEvents.value.filter(e => e.venue === selectedVenue.value && e.status !== "cancelled").sort((a, b) => new Date(`${a.date}T${a.start_time}`) - new Date(`${b.date}T${b.start_time}`)));

const logout = () => { localStorage.clear(); router.push("/login"); };
</script>

<style scoped>
/* BASE STYLES */
.navbar { display: flex; justify-content: space-between; align-items: center; background: #2c3e50; padding: 1rem 2rem; color: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
.nav-logo { font-weight: bold; font-size: 1.2rem; }
.nav-menu { list-style: none; display: flex; margin: 0; padding: 0; gap: 10px; }
.nav-item { position: relative; margin-left: 1.5rem; cursor: pointer; padding: 0.5rem; }
.cursor-pointer { cursor: pointer; }
.dropdown-menu { display: none; position: absolute; background: #34495e; list-style: none; padding: 0.5rem 0; top: 100%; right: 0; min-width: 150px; border-radius: 4px; z-index: 10;}
.nav-item:hover .dropdown-menu { display: block; }
.dropdown-menu li { padding: 0.5rem 1rem; color: #fff; cursor: pointer; border-bottom: 1px solid #2c3e50;}
.dropdown-menu li:hover { background: #1a252f; }

/* ✨ AESTHETIC UPGRADE: Centered Layout */
.centered-layout { display: flex; flex-direction: column; align-items: center; padding: 2rem; }
.card { width: 100%; max-width: 1000px; background: #fff; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
.section-title { text-align: center; color: #2c3e50; margin-top: 0; margin-bottom: 1.5rem; font-size: 1.5rem; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }

/* FORMS (Centered Content) */
.form-container { max-width: 600px; margin: 0 auto; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-weight: bold; color: #34495e; margin-bottom: 5px; font-size: 0.95rem; }
.form-group input, .form-group select { display: block; margin-bottom: 1rem; padding: 0.75rem; width: 100%; box-sizing: border-box; border: 1px solid #ccc; border-radius: 6px; outline: none; }
.form-group input:focus, .form-group select:focus { border-color: #3498db; }
.form-row { display: flex; gap: 15px; width: 100%; margin-bottom: 1rem;}
.form-row input, .form-row select { margin-bottom: 0; width: 100%; }
.flex-row { display: flex; gap: 10px; align-items: flex-start; }
.flex-grow { flex-grow: 1; }
.half { flex: 1; }

.btn-primary { background: #3498db; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; font-weight: bold; transition: background 0.2s;}
.btn-secondary { background: #95a5a6; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; font-weight: bold; transition: background 0.2s;}
.btn-info { background: #3498db; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; }
.btn-danger { background: #e74c3c; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; }
.btn-edit { background: #f39c12; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; }
.btn-sm { margin-right: 5px; font-size: 0.8rem; }
.btn-primary:hover { background: #2980b9; }
.btn-secondary:hover { background: #7f8c8d; }
.full-width-btn { width: 100%; padding: 1rem; font-size: 1.1rem; margin-top: 10px;}
.mt-2 { margin-top: 1rem; }

/* TABLES & CONTROLS */
.controls-section { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 1rem; background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; border: 1px solid #ecf0f1; }
.report-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ecf0f1; padding-bottom: 1rem; margin-bottom: 1.5rem;}
.centered-table { width: 100%; border-collapse: collapse; margin-top: 1rem; box-shadow: 0 0 10px rgba(0,0,0,0.02); }
.centered-table th, .centered-table td { border: 1px solid #ecf0f1; padding: 1.2rem; text-align: center; } 
.centered-table th { background: #f8f9fa; color: #2c3e50; font-weight: bold; }
.text-link { color: #3498db; text-decoration: none; }
.text-link:hover { text-decoration: underline; }
.text-muted { color: #7f8c8d; }

/* ✨ AESTHETIC UPGRADE: Grouped Locations */
.location-group { margin-bottom: 2.5rem; }
.location-header { background: #2c3e50; color: white; padding: 10px 15px; border-radius: 8px 8px 0 0; }
.location-header h4 { margin: 0; font-size: 1.2rem; letter-spacing: 0.5px; }
.location-table { margin-top: 0; border-top: none; }

/* BADGES */
.badge { padding: 0.35rem 0.75rem; border-radius: 15px; font-size: 0.85rem; font-weight: bold; color: white; }
.badge-upcoming { background-color: #3498db; }
.badge-ongoing { background-color: #f1c40f; color: #333; }
.badge-completed { background-color: #95a5a6; }
.badge-cancelled { background-color: #e74c3c; }
.badge-purple { background-color: #9b59b6; }
.badge-sm { padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.7rem; color: white; margin-top: 5px; display: inline-block; }

.clickable-venue { color: #3498db; font-weight: bold; cursor: pointer; border-bottom: 1px dashed #3498db; transition: color 0.2s; }
.clickable-venue:hover { color: #2980b9; border-bottom: 1px solid #2980b9; }

/* MODALS */
.modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); display: flex; justify-content: center; align-items: center; z-index: 1000; padding: 1rem; }
.modal-content { background: white; padding: 2rem; border-radius: 12px; width: 100%; max-width: 550px; }
.venue-modal-content { padding: 0; max-height: 80vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
.modal-header { background: #2c3e50; color: white; padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center; }
.modal-header h2 { margin: 0; font-size: 1.3rem; }
.close-btn { background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer; }
.modal-body { padding: 1.5rem; overflow-y: auto; background: #f8f9fa; }
.modal-actions { margin-top: 1.5rem; display: flex; gap: 10px;}
.empty-state-small { text-align: center; color: #95a5a6; padding: 2rem 0; font-style: italic; }

/* ✨ REDESIGNED PROFILE MODAL CSS */
.profile-modal { max-width: 600px; padding: 0; overflow: hidden; }
.profile-header { background: #34495e; padding: 1.5rem; }
.profile-badge-container { text-align: center; margin-top: -3rem; margin-bottom: 1.5rem; }
.profile-section { background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #ecf0f1; margin-bottom: 1.5rem; }
.security-section { border-left: 4px solid #e74c3c; }
.section-subtitle { margin-top: 0; margin-bottom: 1rem; color: #34495e; font-size: 1.1rem; border-bottom: 1px solid #ecf0f1; padding-bottom: 5px; }
.profile-actions { display: flex; justify-content: space-between; margin-top: 0; }

.venue-schedule-list { list-style: none; padding: 0; margin: 0; }
.venue-schedule-list li { background: white; border: 1px solid #ecf0f1; border-radius: 8px; margin-bottom: 1rem; display: flex; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.vs-date { background: #ecf0f1; padding: 1rem; text-align: center; border-right: 1px solid #bdc3c7; border-radius: 8px 0 0 8px; min-width: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.vs-details { padding: 1rem; display: flex; flex-direction: column; justify-content: center; }
.vs-title { font-weight: bold; color: #34495e; margin-bottom: 0.3rem; font-size: 1.05rem; }

/* PRINTING */
@media print {
  .no-print { display: none !important; }
  body { background: white; font-size: 12pt; }
  .container { padding: 0; margin: 0; max-width: 100%; }
  .card { box-shadow: none; border: none; margin: 0; padding: 0; }
  .print-table { width: 100%; border: 1px solid #000; }
  .print-table th, .print-table td { border: 1px solid #000; padding: 8px; }
  .badge { border: 1px solid #000; color: #000 !important; background: transparent !important; }
}
</style>