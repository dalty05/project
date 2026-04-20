const API = "http://127.0.0.1:5000"

export const login = async (credentials) => {

  const res = await fetch(`${API}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(credentials)
  })

  return await res.json()
}