const PAGE_SIZE = 3;
// Is true when all data has been loaded
complete = false;
last_requested_bets = -1;

var user = new Vue({
    el: '#user',
    delimiters: ['<%', '%>'],
    data: {
        loaded: false,
        is_current: true,
        shown_until: 0,
        shown_days: [],
        data: {},
    },
    methods: {
        get_user_info: function() {
            let url_split = window.location.pathname.split('/');
            let username = url_split[url_split.length-1];
            let endpoint = '/api/user/' + username;
            fetch(endpoint)
                .then((response) => {
                    return response.json();
                })
                .then((user_json) => {
                    this.data = user_json;
                })
                .then(() => {
                    this.get_bets_info(this.shown_until);
                    this.loaded = true;
                })
        },
        get_bets_info: function(current_size) {
            // Another request is already serving this data
            last_requested_bets = this.shown_days.length;
            let url_split = window.location.pathname.split('/');
            let username = url_split[url_split.length-1];
            let endpoint = '/api/user/' + username + '/bets?page=' + this.shown_until;
            fetch(endpoint)
                .then((response) => {
                    return response.json();
                })
                .then((bets_json) => {
                    if (this.shown_until != last_requested_bets) return false;
                    if (bets_json.success) {
                        let days = bets_json.data;
                        for (let i = 0; i < PAGE_SIZE && i < days.length; i++) {
                            this.shown_until++;
                            this.shown_days.push(days[i]);
                        }
                    }
                    else {
                        notifications.add_error(bets_json.msg);
                    }
                    complete = bets_json.complete;
                })
        },
        get_bet_class: function(bet) {
            if (bet.won) return "won-bet";
            else return "lost-bet";
        },
        follow: function() {
            let endpoint = '/api/follow/' + this.data.username;
            fetch(endpoint,
                {
                method: 'post'
                })
                .then((response) => {
                    return response.json();
                })
                .then((resp) => {
                    if (resp.success) {
                        this.data.is_following = true;
                        notifications.add_success(resp.msg);
                    }
                    else {
                        notifications.add_error(resp.msg);    
                    }
                });
        },
        unfollow: function() {
            let endpoint = '/api/unfollow/' + this.data.username;
            fetch(endpoint,
                {
                method: 'post'
                })
                .then((response) => {
                    return response.json();
                })
                .then((resp) => {
                    if (resp.success) {
                        this.data.is_following = false;
                        notifications.add_success(resp.msg);
                    }
                    else {
                        notifications.add_error(resp.msg);    
                    }
                });
        },
        infiniteHandler: function ($state) {
            let current = this.shown_until;
            setTimeout(() => {
                if (last_requested_bets < current) {
                    this.get_bets_info(this.shown_until);
                }
                if (complete) {
                    $state.complete();
                }
                else {
                    $state.loaded();
                }
            }, 1000);   
        }
    },
    filters: {
        pluralize: function(word, num) {
            if (num == 1) return word;
            else return word + 's';
        }
    },
})

user.get_user_info();
