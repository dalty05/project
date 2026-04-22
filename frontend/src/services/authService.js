const API = "daltyo5.pythonanywhere.com"

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
