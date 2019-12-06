$(document).ready(function(){	
    $.ajax({
        url: "/users",
        async: true,
        dataType: 'json',
        success: function (data) {
            //send parse data to autocomplete function
            loadSuggestions(data);
        }
    });
    function loadSuggestions(options) {
        $('#autocomplete').autocomplete({
            triggerSelectOnValidInput: false,
            lookup: options,
            lookupLimit: 10,
            onSelect: function (suggestion) {
                $('#selected_option').html(suggestion.value);
                $('#searchbox').submit();
            }
        });
    }
});
