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
        },
        clear_flashed_messages: function() {
            this.messages = [];
        }
    }
})

flashed_messages.get_flashed_messages();
setTimeout(flashed_messages.clear_flashed_messages, 10000);
//setInterval(flashed_messages.get_flashed_messages, 60000);




