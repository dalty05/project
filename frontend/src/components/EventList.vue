<template>

<div>

<h2>Scheduled Events</h2>

<ul>

<li v-for="event in events" :key="event.id">

{{event.title}} |
{{event.venue}} |
{{event.date}} |
{{event.start_time}} - {{event.end_time}}

</li>

</ul>

</div>

</template>

<script>

import axios from "axios"

export default {

data(){
return{
events:[]
}
},

async mounted(){

const response = await axios.get(
"http://localhost:5000/events"
)

this.events = response.data

}

}

</script>