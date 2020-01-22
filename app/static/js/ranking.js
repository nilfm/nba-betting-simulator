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
        toggle_global: function() {
            this.global = !this.global;
            this.shown_until = 10;
            const total = (this.global ? this.data.global : this.data.followed);
            this.shown_users = total.slice(0, this.shown_until); // could make infinitescroll stop working if completed earlier
            this.rank_current = (this.global ? this.rank_global : this.rank_followed);
            this.infiniteId++;
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
                    this.is_authenticated = ranking_json.is_authenticated;
                    if (this.is_authenticated) {
                        this.current_user.username = ranking_json.username;
                        this.current_user.ranking_funds = ranking_json.ranking_funds;
                        this.rank_followed = this.find(this.data.followed, this.username) + 1;
                        this.rank_global = this.find(this.data.global, this.username) + 1;
                        this.rank_current = this.rank_global;
                    }
                })
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
