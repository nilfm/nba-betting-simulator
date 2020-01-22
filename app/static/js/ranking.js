var ranking = new Vue({
    el: '#ranking',
    delimiters: ['<%', '%>'],
    data: {
        loaded: false,
        is_authenticated: false,
        global: true,
        shown_users: [],
        shown_until: 0,
        rank_followed: 0,
        rank_global: 0,
        rank_current: 0,
        current_user: {},
        infiniteId: 0
    },
    methods: {
        toggle: function(global) {
            if (this.global == global) return;
            this.global = global;
            this.shown_until = 10;
            const total = (this.global ? this.data.global : this.data.followed);
            this.shown_users = total.slice(0, this.shown_until); 
            this.rank_current = (this.global ? this.rank_global : this.rank_followed);
            this.infiniteId++; //resets infinite loading when switching rankings
        },
        find: function(arr, name) {
            for (let i = 0; i < arr.length; i++) {
                if (arr[i].username == name) return i;
            }
            return -1;
        },
        get_ranking_info: function() {
            fetch('/api/ranking')
                .then((response) => {
                    return response.json();
                })
                .then((ranking_json) => {
                    this.data = ranking_json;
                    this.loaded = true;
                    this.shown_until = 10;
                    this.shown_users = this.data.global.slice(0, this.shown_until);
                })
                .then(() => {
                    fetch('/api/current_user')
                        .then((response) => {
                            return response.json();
                        })
                        .then((user_json) => {
                            this.is_authenticated = user_json.is_authenticated;
                            if (this.is_authenticated) {
                                this.current_user.username = user_json.data.username;
                                this.current_user.ranking_funds = user_json.data.ranking_funds;
                                this.rank_followed = this.find(this.data.followed, this.current_user.username) + 1;
                                this.rank_global = this.find(this.data.global, this.current_user.username) + 1;
                                this.rank_current = this.rank_global;
                            }
                        })
                    })
        },
        get_ranking_class: function(username, current_username) {
            if (username == current_username) return "current-user-ranking";
            else return "other-user-ranking";
        },
        infiniteHandler: function ($state) {
            const total = (this.global ? this.data.global : this.data.followed);
            const limit = total.length;
            if (this.shown_until >= limit) {
                $state.complete();
            }
            else {
                setTimeout(() => {
                    for (let i = 0; i < 10 && this.shown_until < limit; i++) {
                        this.shown_users.push(total[this.shown_until]);
                        this.shown_until++;
                    }
                    $state.loaded();
                }, 500);   
            }
        }
    },
})

ranking.get_ranking_info();
