var games = new Vue({
    el: '#games',
    delimiters: ['<%', '%>'],
    data: {
        loaded: false,
        data: {},
        shown_games: []
    },
    methods: {
        get_games_info: function() {
            fetch('/api/games')
                .then((response) => {
                    return response.json();
                })
                .then((games_json) => {
                    this.data = games_json;
                    this.loaded = true;
                    // Get timestamp of start
                    for (let i = 0; i < this.data.length; i++) {
                        this.data[i].start_timestamp = moment(this.data[i].date_time);
                    }
                    this.shown_games = this.data.filter(this.not_started);
                })
        },
        get_current_timestamp: function() {
            return moment.utc().subtract('8', 'hour');
        },
        not_started: function(game) {
            // Ignore timezones in comparison!
            game_start = game.start_timestamp.format('YYYY-MM-DD HH:mm:ss');
            now = this.get_current_timestamp().format('YYYY-MM-DD HH:mm:ss');
            return game_start > now;
        },
        get_amount: function(game_id, bet_on_home) {
            home_or_away = bet_on_home ? 'home' : 'away';
            amount_id = 'amount-' + home_or_away + '-' + game_id;
            value_str = document.getElementById(amount_id).value;
            if (value_str == "") value_str = '0';
            value = parseInt(value_str);
            return value;
        },
        clear_amount: function(game_id, bet_on_home) {
            home_or_away = bet_on_home ? 'home' : 'away';
            amount_id = 'amount-' + home_or_away + '-' + game_id;
            document.getElementById(amount_id).value = '';
            console.log(document.getElementById(amount_id).value);
        },
        validate_bet: function(value) {
            if (value <= 0) notifications.add_error('The bet amount has to be positive');
            else if (value > current_user.data.funds) notifications.add_error('You only have ' + current_user.data.funds + ' coins'); 
            else return true;
            return false;
        },
        place_bet: function(game_id, bet_on_home) {
            amount = this.get_amount(game_id, bet_on_home);
            if (!this.validate_bet(amount)) {
                this.clear_amount(game_id, bet_on_home);
                return;
            }
            payload = {
                'game_id': game_id,
                'bet_on_home': bet_on_home,
                'amount': amount
            };
            fetch('/api/place_bet', 
                {
                method: 'post',
                body: JSON.stringify(payload),
                })
                .then((response) => {
                    return response.json();
                })
                .then((resp) => {
                    if (resp.success) {
                        current_user.data.funds -= amount;
                        this.set_already_bet(game_id, bet_on_home);
                        notifications.add_success(resp.msg);
                    }
                    else {
                        notifications.add_error(resp.msg);    
                    }
                    this.clear_amount(game_id, bet_on_home);
                });
        },
        set_already_bet: function(game_id, bet_on_home) {
            for (let i = 0; i < this.data.length; i++) {
                if (this.data[i].game_id == game_id) {
                    if (bet_on_home) {
                        this.data[i].already_bet_home = true;
                    }
                    else {
                        this.data[i].already_bet_away = true;
                    }
                    return;
                }
            }
        }
    },
    filters: {
        pluralize: function(word, num) {
            if (num == 1) return word;
            else return word + 's';
        }
    },
    computed: {
        current_date: function() {
            return this.get_current_timestamp().format('YYYY-MM-DD');
        }
    }
})

games.get_games_info();
setTimeout(games.get_games_info, 600000); // Every 10 minutes check for new games or games that already started
