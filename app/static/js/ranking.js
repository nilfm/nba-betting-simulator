const PAGE_SIZE = 10;
// Is true when all data has been loaded
complete = false;
last_requested_rank = -1;

var ranking = new Vue({
    el: '#ranking',
    delimiters: ['<%', '%>'],
    data: {
        loaded: false,
        loaded_user: false,
        is_authenticated: false,
        global: true,
        shown_users: [],
        shown_until: 0,
        rank_followed: -1,
        rank_global: -1,
        rank_current: -1,
        current_user: {},
        infiniteId: 0
    },
    methods: {
        toggle: function(global) {
            if (this.global == global) return;
            this.global = global;
            this.shown_until = 0;
            this.shown_users = [];
            last_requested_rank = -1;
            this.get_ranking_info();
            this.rank_current = (global ? this.rank_global : this.rank_followed);
            this.infiniteId++; //resets infinite loading when switching rankings
        },
        get_current_user_info: function() {
            fetch('/api/current_user')
                .then((response) => {
                    return response.json();
                })
                .then((user_json) => {
                    this.is_authenticated = user_json.is_authenticated;
                    if (this.is_authenticated) {
                        this.current_user.username = user_json.data.username;
                        this.current_user.ranking_funds = user_json.data.ranking_funds;
                    }
                })
                .then(() => {
                    fetch('/api/current_rank')
                        .then((response) => {
                            return response.json();
                        })
                        .then((resp) => {
                            this.rank_global = resp.rank_global;
                            this.rank_followed = resp.rank_followed;
                            this.rank_current = this.rank_global;
                        })
                    this.loaded_user = true;
                })
        },
        get_ranking_info: function() {
            last_requested_rank = this.shown_until;
            // Know whether to fetch from global or local
            let url_global = this.global ? 'global' : 'followed';
            
            fetch('/api/ranking/' + url_global + '?page=' + this.shown_until)
                .then((response) => {
                    return response.json();
                })
                .then((rank_json) => {
                    // Check if another request has already completed for this page
                    if (this.shown_until != last_requested_rank) return false;
                    if (rank_json.success) {
                        let users = rank_json.data.ranking;
                        for (let i = 0; i < PAGE_SIZE && i < users.length; i++) {
                            this.shown_until++;
                            this.shown_users.push(users[i]);
                        }
                    }
                    else {
                        notifications.add_error(bets_json.msg);
                    }
                    complete = rank_json.complete;
                    this.loaded = true;
                })
        },
        get_ranking_class: function(username, current_username) {
            if (username == current_username) return "current-user-ranking";
            else return "other-user-ranking";
        },
        infiniteHandler: function ($state) {
            let current = this.shown_until;
            setTimeout(() => {
                if (last_requested_rank < current) {
                    this.get_ranking_info();
                }
                if (complete) {
                    $state.complete();
                }
                else {
                    $state.loaded();
                }
            }, 500);   
        }
    },
})

ranking.get_current_user_info();
ranking.get_ranking_info();
