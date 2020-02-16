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
        bet_type: -1,
        select_by: -1,
        sort_by: -1,
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
                    this.set_mode("bet_for", "total", 0);
                    this.set_initial_stats();
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
        team_stats_comparison_balance: function(t1, t2) {
            if (t1.total_balance > t2.total_balance) return -1;
            if (t1.total_balance < t2.total_balance) return 1;
            return 0;
        },
        team_stats_comparison_num_wins: function(t1, t2) {
            if (t1.num_wins > t2.num_wins) return -1;
            if (t1.num_wins < t2.num_wins) return 1;
            return 0;
        },
        team_stats_comparison_num_bets: function(t1, t2) {
            if (t1.num_bets > t2.num_bets) return -1;
            if (t1.num_bets < t2.num_bets) return 1;
            return 0;
        },
        /*
        bet_type: 
            bet_for
            bet_against
            total
        select_by:
            total
            home
            away
            favorite
            underdog
        sort_by:
            0 -> balance
            1 -> wins
            2 -> total bets
        */
        set_mode: function(bet_type, select_by, sort_by) {
            if (this.bet_type == bet_type && this.select_by == select_by && this.sort_by == sort_by) return;
            this.bet_type = bet_type;
            this.select_by = select_by;
            this.sort_by = sort_by;
            let new_stats = [];
            for (let i = 0; i < 30; i++) {
                new_stats.push(this.data.stats.by_team[i][bet_type][select_by])
                new_stats[i].short_name = this.data.stats.by_team[i].short_name;
                new_stats[i].long_name = this.data.stats.by_team[i].long_name;
            }
            Vue.set(this.stats_to_show, 'by_team', new_stats);
            this.sort_stats(sort_by);
        },
        clear_actives: function(elem_id) {
            let parent = document.getElementById(elem_id);
            let children = parent.childNodes;
            for (let i = 0; i < children.length; i++) {
                if (children[i].classList) {
                    children[i].classList.remove("active");
                }
            }
        },
        set_type: function(bet_type) {
            this.set_mode(bet_type, this.select_by, this.sort_by);
            this.clear_actives("types");
            document.getElementById("type-"+bet_type).classList.add("active");
        }, 
        set_select: function(select_by) {
            this.set_mode(this.bet_type, select_by, this.sort_by);
            this.clear_actives("selects");
            document.getElementById("select-"+select_by).classList.add("active");
        }, 
        set_sort: function(sort_by) {
            this.set_mode(this.bet_type, this.select_by, sort_by);
            this.clear_actives("sorts");
            document.getElementById("sort-"+sort_by).classList.add("active");
        },
        sort_stats: function(mode) {
            if (mode == 0) this.stats_to_show.by_team.sort(this.team_stats_comparison_balance);
            else if (mode == 1) this.stats_to_show.by_team.sort(this.team_stats_comparison_num_wins);
            else if (mode == 2) this.stats_to_show.by_team.sort(this.team_stats_comparison_num_bets);    
        },
        set_initial_stats: function() {
            this.stats_to_show.best_team = this.stats_to_show.by_team[0];
            this.stats_to_show.worst_team = this.stats_to_show.by_team[29];
            this.stats_to_show.won = this.data.stats.won;
            this.stats_to_show.lost = this.data.stats.lost;
            this.stats_to_show.pending = this.data.stats.pending;           
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
