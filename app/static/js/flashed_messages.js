var flashed_messages = new Vue({
    el: '#flashed',
    delimiters: ['<%', '%>'],
    data: {
        messages: []
    },
    methods: {
        get_flashed_messages: function() {
            fetch('/api/flashed_messages')
                .then((response) => {
                    return response.json();
                })
                .then((messages_json) => {
                    this.messages = messages_json;
                })
        }
    }
})

flashed_messages.get_flashed_messages();
//setInterval(flashed_messages.get_flashed_messages, 60000);




