const API = "daltyo5.pythonanywhere.com"

export const createHost = async (data) => {
  const res = await fetch(`${API}/create_host`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  })
  return await res.json()
}

export const addVenue = async (data) => {
  const res = await fetch(`${API}/add_venue`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  })
  return await res.json()
}

export const getVenues = async () => {
  const res = await fetch(`${API}/venues`)
  return await res.json()
}

export const getHosts = async () => {
  const res = await fetch("http://127.0.0.1:5000/hosts")
  return await res.json()
}
