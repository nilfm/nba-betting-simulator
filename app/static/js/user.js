var user = new Vue({
    el: '#user',
    delimiters: ['<%', '%>'],
    data: {
        loaded: false,
        is_current: true,
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
                    this.loaded = true;
                    this.shown_until = 10;
                    this.shown_days = this.data.finished_bets.slice(0, this.shown_until);
                })
        },
        get_bet_class: function(bet) {
            if (bet.won) return "won-bet";
            else return "lost-bet";
        },
        follow: function() {
            console.log("OK");
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
            if (this.shown_until >= this.data.finished_bets.length) {
                $state.complete();
            }
            else {
                setTimeout(() => {
                    this.shown_days.push(this.data.finished_bets[this.shown_until]);
                    this.shown_until++;
                    $state.loaded();
                }, 500);   
            }
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
