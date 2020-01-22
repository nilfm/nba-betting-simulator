$(document).ready(function(){
    fetch('/api/users')
    .then((response) => {
        return response.json();
    })
    .then((users_json) => {
        load_suggestions(users_json);
    })
    function load_suggestions(options) {
        $('#autocomplete').autocomplete({
            triggerSelectOnValidInput: false,
            lookup: options,
            groupBy: 'category',
            lookupLimit: 5,
            onSelect: function (suggestion) {
                $('#selected_option').html(suggestion.value);
                window.location.href = '/user/'+suggestion.value;
            }
        });
    }
});
