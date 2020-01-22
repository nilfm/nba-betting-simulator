var feed = new Vue({
    el: '#feed',
    delimiters: ['<%', '%>'],
    data: {
        loaded: false,
        shown_days: [],
        data: []
    },
    methods: {
        get_feed_info: function() {
            fetch('/api/feed')
                .then((response) => {
                    return response.json();
                })
                .then((bets_json) => {
                    this.data = bets_json;
                    this.loaded = true;
                    this.shown_until = 1;
                    this.shown_days = this.data.slice(0, this.shown_until);
                })
        },
        get_bet_class: function(bet) {
            if (!bet.finished) return "pending-bet";
            else if (bet.won) return "won-bet";
            else return "lost-bet";
        },
        infiniteHandler: function ($state) {
            if (this.shown_until >= this.data.length) {
                $state.complete();
            }
            else {
                setTimeout(() => {
                    this.shown_days.push(this.data[this.shown_until]);
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

feed.get_feed_info();
