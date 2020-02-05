var current_user = new Vue({
    el: '#top_navbar',
    delimiters: ['<%', '%>'],
    data: {
        is_authenticated: false,
        data: {},
        loaded: false,
    },
    methods: {
        get_current_user_info: function() {
            fetch('/api/current_user')
                .then((response) => {
                    return response.json();
                })
                .then((user_json) => {
                    this.data = user_json.data;
                    this.is_authenticated = user_json.is_authenticated;
                    this.loaded = true;
                })
        }
    }
})

current_user.get_current_user_info();





