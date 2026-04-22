const API = "daltyo5.pythonanywhere.com"

// CREATE EVENT
export const createEvent = async (data) => {
  const res = await fetch(`${API}/create_event`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  })
  return await res.json()
}

// UPDATE EVENT ✅
export const updateEvent = async (id, data) => {
  const res = await fetch(`${API}/update_event/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  })
  return await res.json()
}
export const getEvents = async () => {
  const res = await fetch(`${API}/events`)
  return await res.json()
}

// CANCEL EVENT
export const cancelEvent = async (id, userId) => {
  const res = await fetch(`${API}/cancel_event/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId })
  })
  return await res.json()
}
