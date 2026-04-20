<template>
  <!-- NAV -->
  <nav class="navbar">
    <div class="nav-logo">Event Scheduler</div>

    <ul class="nav-menu">
      <li class="nav-item dropdown">
        <span>Events</span>
        <ul class="dropdown-menu">
          <li @click="switchSection('create')">Create Event</li>
          <li @click="switchSection('myEvents')">My Events</li>
        </ul>
      </li>

      <li class="nav-item dropdown">
        <span>Venues</span>
        <ul class="dropdown-menu">
          <li @click="switchSection('venues')">View Venues</li>
        </ul>
      </li>

      <li class="nav-item dropdown">
        <span>{{ user.username }}</span>
        <ul class="dropdown-menu">
          <li @click="logout">Logout</li>
        </ul>
      </li>
    </ul>
  </nav>

  <main class="container">

    <!-- CREATE EVENT -->
    <section v-if="activeSection === 'create'" class="card">
      <h3>Create Event</h3>

      <input v-model="eventName" placeholder="Event Title" />
      <input type="date" v-model="eventDate" />
      <input type="time" v-model="startTime" />
      <input type="time" v-model="endTime" />

      <select v-model="venueId">
        <option disabled value="">Select Venue</option>
        <option v-for="v in venues" :key="v.id" :value="v.id">
          {{ v.name }} (Capacity: {{ v.capacity }})
        </option>
      </select>

      <button @click="handleCreateEvent">Create Event</button>
    </section>

    <!-- MY EVENTS -->
    <section v-if="activeSection === 'myEvents'" class="card">
      <h3>My Events</h3>

      <table class="events-table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Date</th>
            <th>Time</th>
            <th>Venue</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="e in myEvents" :key="e.id">
            <td>{{ e.title }}</td>
            <td>{{ e.date }}</td>
            <td>{{ e.start_time }} - {{ e.end_time }}</td>
            <td>{{ e.venue }}</td>

            <td>
              <span :class="getStatusClass(e)">
                {{ getStatus(e) }}
              </span>
            </td>

            <td>
              <button @click="viewEvent(e)">View</button>
              <button @click="editEvent(e)">Edit</button>

              <button 
                class="cancel-btn"
                v-if="e.status !== 'cancelled'" 
                @click="handleCancel(e)"
              >
                Cancel
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- VENUES -->
    <section v-if="activeSection === 'venues'" class="card">
      <h3>Venues</h3>

      <table class="venues-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Location</th>
            <th>Capacity</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="v in venues" :key="v.id">
            <td>{{ v.name }}</td>
            <td>{{ v.location }}</td>
            <td>{{ v.capacity }}</td>
          </tr>
        </tbody>
      </table>
    </section>

  </main>

  <!-- MODAL -->
  <div v-if="selectedEvent" class="modal">
    <div class="modal-content">

      <h3>Event Details</h3>

      <!-- VIEW MODE -->
      <div v-if="!editMode">
        <p><strong>Title:</strong> {{ selectedEvent.title }}</p>
        <p><strong>Date:</strong> {{ selectedEvent.date }}</p>
        <p><strong>Time:</strong> {{ selectedEvent.start_time }} - {{ selectedEvent.end_time }}</p>
        <p><strong>Venue:</strong> {{ selectedEvent.venue }}</p>

        <button @click="editMode = true">Edit</button>
        <button @click="closeModal">Close</button>
      </div>

      <!-- EDIT MODE -->
      <div v-else>
        <input v-model="selectedEvent.title" />
        <input type="date" v-model="selectedEvent.date" />
        <input type="time" v-model="selectedEvent.start_time" />
        <input type="time" v-model="selectedEvent.end_time" />

        <select v-model="selectedEvent.venue_id">
          <option v-for="v in venues" :key="v.id" :value="v.id">
            {{ v.name }}
          </option>
        </select>

        <button @click="updateEventHandler">Save</button>
        <button @click="closeModal">Close</button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { getVenues } from "../services/adminService"
import { createEvent, getEvents, updateEvent, cancelEvent } from "../services/eventService"
import { useNotification } from "../services/notificationService"

const { showNotification } = useNotification()
const user = JSON.parse(localStorage.getItem("user"))

const activeSection = ref("create")

const venues = ref([])
const myEvents = ref([])

const eventName = ref("")
const eventDate = ref("")
const startTime = ref("")
const endTime = ref("")
const venueId = ref("")

const selectedEvent = ref(null)
const editMode = ref(false)

/* LOADERS */
const loadVenues = async () => {
  venues.value = await getVenues()
}

const loadEvents = async () => {
  const events = await getEvents()
  myEvents.value = events.filter(e => e.host === user.username)
}

/* NAVIGATION */
const switchSection = async (section) => {
  activeSection.value = section

  if (section === "venues") await loadVenues()
  if (section === "myEvents") await loadEvents()
}

/* CREATE EVENT */
const handleCreateEvent = async () => {
  if (!eventName.value || !eventDate.value || !startTime.value || !endTime.value || !venueId.value) {
    showNotification("All fields are required", "error")
    return
  }

  try {
    const res = await createEvent({
      title: eventName.value,
      date: eventDate.value,
      start_time: startTime.value,
      end_time: endTime.value,
      venue_id: venueId.value,
      created_by: user.id
    })

    if (res.message.toLowerCase().includes("booked")) {
      showNotification(res.message, "error")
      return
    }

    showNotification(res.message, "success")

    // reset form
    eventName.value = ""
    eventDate.value = ""
    startTime.value = ""
    endTime.value = ""
    venueId.value = ""

    await loadEvents()

  } catch (err) {
    console.error(err)
    showNotification("Server error", "error")
  }
}

/* CANCEL */
const handleCancel = async (event) => {
  await cancelEvent(event.id, user.id)
  showNotification("Event cancelled", "success")
  await loadEvents()
}

/* VIEW / EDIT */
const viewEvent = (event) => {
  selectedEvent.value = { ...event }
  editMode.value = false
}

const editEvent = (event) => {
  selectedEvent.value = { ...event }
  editMode.value = true
}

const closeModal = () => {
  selectedEvent.value = null
  editMode.value = false
}

/* UPDATE */
const updateEventHandler = async () => {
  try {
    const res = await updateEvent(selectedEvent.value.id, {
      title: selectedEvent.value.title,
      date: selectedEvent.value.date,
      start_time: selectedEvent.value.start_time,
      end_time: selectedEvent.value.end_time,
      venue_id: selectedEvent.value.venue_id
    })

    if (res.message.toLowerCase().includes("conflict")) {
      showNotification(res.message, "error")
      return
    }

    showNotification(res.message, "success")

    closeModal()
    await loadEvents()

  } catch (err) {
    console.error(err)
    showNotification("Update failed", "error")
  }
}

/* STATUS */
function getStatus(event) {
  const now = new Date()
  const start = new Date(`${event.date}T${event.start_time}`)
  const end = new Date(`${event.date}T${event.end_time}`)

  if (now < start) return "Upcoming"
  if (now <= end) return "Ongoing"
  return "Completed"
}

function getStatusClass(event) {
  return {
    Upcoming: "status-upcoming",
    Ongoing: "status-ongoing",
    Completed: "status-completed"
  }[getStatus(event)]
}

const logout = () => {
  localStorage.removeItem("user")
  location.reload()
}

onMounted(() => {
  loadVenues()
  loadEvents()
})
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  background: #2c3e50;
  padding: 10px;
  color: white;
}

.nav-menu {
  list-style: none;
  display: flex;
}

.nav-item {
  margin-left: 15px;
  position: relative;
}

.dropdown-menu {
  display: none;
  position: absolute;
  background: #34495e;
  padding: 5px;
}

.nav-item:hover .dropdown-menu {
  display: block;
}

.container {
  padding: 20px;
}

.card {
  background: #ecf0f1;
  padding: 15px;
  border-radius: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  border: 1px solid #ccc;
  padding: 8px;
}

th {
  background: #95a5a6;
  color: white;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
}

button {
  margin-right: 5px;
  padding: 6px 10px;
  border: none;
  background: #3498db;
  color: white;
  cursor: pointer;
}

button:hover {
  background: #2980b9;
}

.cancel-btn {
  background: red;
}
</style>