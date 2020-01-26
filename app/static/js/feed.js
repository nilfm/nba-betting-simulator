const PAGE_SIZE = 3;
// Is true when all data has been loaded
complete = false;
last_requested_feed = -1;

var feed = new Vue({
    el: '#feed',
    delimiters: ['<%', '%>'],
    data: {
        loaded: false,
        shown_until: 0,
        shown_days: [],
    },
    methods: {
        get_feed_info: function() {
            last_requested_feed = this.shown_days.length;
            fetch('/api/feed?page=' + this.shown_until)
                .then((response) => {
                    return response.json();
                })
                .then((bets_json) => {
                    // Check if another request has already completed for this page
                    if (this.shown_until != last_requested_feed) return false;
                    if (bets_json.success) {
                        let days = bets_json.data;
                        this.loaded = true;
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
            if (!bet.finished) return "pending-bet";
            else if (bet.won) return "won-bet";
            else return "lost-bet";
        },
        infiniteHandler: function ($state) {
            let current = this.shown_until;
            setTimeout(() => {
                if (last_requested_feed < current) {
                    this.get_feed_info();
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

feed.get_feed_info();
