function uuidv4() {
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  );
}

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
                    for (let i = 0; i < messages_json.length; i++) {
                        add_message(messages_json[i]);
                    }
                })
        },
        add_message: function(text) {
            msg_id = uuidv4();
            // Remove all equal messages
            this.remove_message_text(text);
            // Insert the new one
            this.messages.push({'id': msg_id, 'text': text});
            setTimeout(() => this.remove_message(msg_id), 10000);
        },
        remove_message: function(msg_id) {
            this.messages = this.messages.filter((msg) => msg.id != msg_id);
        },
        remove_message_text: function(text) {
            this.messages = this.messages.filter((msg) => msg.text != text);
        }
    }
})

flashed_messages.get_flashed_messages();




