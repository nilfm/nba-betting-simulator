var user = new Vue({
    el: '#user',
    delimiters: ['<%', '%>'],
    data: {
        loaded: false,
        is_current: true,
        shown_days: [],
    },
    methods: {
        get_user_info: function() {
            url_split = window.location.pathname.split('/');
            username = url_split[url_split.length-1];
            endpoint = '/api/user/' + username;
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
