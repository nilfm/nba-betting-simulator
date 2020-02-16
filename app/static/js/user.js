const PAGE_SIZE = 3;
// Is true when the url is of the form /user/<username> and not /user/<username>/stats or anything else
const LOAD_BETS = (window.location.pathname.split('/').indexOf("user")  == window.location.pathname.split('/').length-2);
// Is true when all data has been loaded
complete = false;
last_requested_bets = -1;

var user = new Vue({
    el: '#user',
    delimiters: ['<%', '%>'],
    data: {
        url_user: null,
        url_stats: null,
        current_mode: -1,
        loaded: false,
        is_current: true,
        shown_until: 0,
        shown_days: [],
        stats_to_show: {},
        data: {},
    },
    methods: {
        get_user_info: function() {
            let url_split = window.location.pathname.split('/');
            let username_index = url_split.indexOf("user") + 1;
            let username = url_split[username_index];
            this.url_user = "/user/" + username;
            this.url_stats = this.url_user + "/stats";
            let endpoint = '/api/user/' + username;
            fetch(endpoint)
                .then((response) => {
                    return response.json();
                })
                .then((user_json) => {
                    this.data = user_json;
                    this.extract_stats();
                    this.sort_stats(0);
                })
                .then(() => {
                    if (LOAD_BETS) {
                        this.get_bets_info(this.shown_until);
                    }
                    this.loaded = true;
                })
        },
        get_bets_info: function(current_size) {
            // Another request is already serving this data
            last_requested_bets = this.shown_until;
            let url_split = window.location.pathname.split('/');
            let username = this.data.username;
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
                            days[i].balance = this.calculate_balance(days[i]);
                            days[i].display_balance = this.calculate_display_balance(days[i].balance);
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
        team_stats_comparison_bet_for: function(t1, t2) {
            if (t1.bet_for.total_balance > t2.bet_for.total_balance) return -1;
            if (t1.bet_for.total_balance < t2.bet_for.total_balance) return 1;
            return 0;
        },
        team_stats_comparison_bet_against: function(t1, t2) {
            if (t1.bet_against.total_balance > t2.bet_against.total_balance) return -1;
            if (t1.bet_against.total_balance < t2.bet_against.total_balance) return 1;
            return 0;
        },
        team_stats_comparison_total: function(t1, t2) {
            if (t1.total.total_balance > t2.total.total_balance) return -1;
            if (t1.total.total_balance < t2.total.total_balance) return 1;
            return 0;
        },
        extract_stats: function() {
            this.data.stats.by_team.sort(this.team_stats_comparison_bet_for);
            this.stats_to_show.best_team = this.data.stats.by_team[0];
            this.stats_to_show.worst_team = this.data.stats.by_team[this.data.stats.by_team.length-1];
            this.stats_to_show.by_team = this.data.stats.by_team;
            this.stats_to_show.won = this.data.stats.won;
            this.stats_to_show.lost = this.data.stats.lost;
            this.stats_to_show.pending = this.data.stats.pending;           
        },
        sort_stats: function(mode) {
            if (this.current_mode == mode) return;
            this.current_mode = mode;
            if (mode == 0) this.stats_to_show.by_team.sort(this.team_stats_comparison_bet_for);
            else if (mode == 1) this.stats_to_show.by_team.sort(this.team_stats_comparison_bet_against);
            else if (mode == 2) this.stats_to_show.by_team.sort(this.team_stats_comparison_total);    
        },
        get_bet_class: function(bet) {
            if (bet.won) return "won-bet";
            else return "lost-bet";
        },
        get_team_background_color(position) {
            // Start: Green (0, 255, 0, 0.2)
            // End: Red (255, 0, 0, 0.2)
            // Total: 30 teams (indexed 0-29)
            let red_component = position/29.0 * 255;
            let green_component = (29-position)/29.0 * 255;
            let style = "background-color: rgba(" + red_component + ", " + green_component + ", 0, 0.3) !important"
            return style;
        },
        calculate_balance: function(day) {
            let balance = 0;
            for (let i = 0; i < day.bets.length; i++) {
                let bet = day.bets[i];
                if (bet.finished) {
                    balance += bet.balance;
                }
            }
            return balance;
        },
        calculate_display_balance: function(balance) {
            if (balance <= 0) return balance.toString();
            else return '+' + balance;
        },
        follow: function() {
            let endpoint = '/api/follow/' + this.data.username;
            console.log(endpoint);
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
            }, 500);   
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
