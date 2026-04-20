<template>

<div>

<h2>Add Event</h2>

<input v-model="title" placeholder="Event Title">
<input v-model="venue" placeholder="Venue">

<input type="date" v-model="date">
<input type="time" v-model="start_time">
<input type="time" v-model="end_time">

<button @click="addEvent">Add Event</button>

<p>{{message}}</p>

</div>

</template>

<script>

import axios from "axios"

export default {

data(){
return{
title:"",
venue:"",
date:"",
start_time:"",
end_time:"",
message:""
}
},

methods:{

async addEvent(){

const response = await axios.post(
"http://localhost:5000/add_event",
{
title:this.title,
venue:this.venue,
date:this.date,
start_time:this.start_time,
end_time:this.end_time
}
)

this.message = response.data.message

}

}

}

</script>