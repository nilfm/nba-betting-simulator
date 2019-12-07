$(document).ready(function(){	
    $.ajax({
        url: "/users",
        async: true,
        dataType: 'json',
        success: function (data) {
            //send parse data to autocomplete function
            console.log(data);
            loadSuggestions(data);
        }
    });
    function loadSuggestions(options) {
        $('#autocomplete').autocomplete({
            triggerSelectOnValidInput: false,
            lookup: options,
            groupBy: 'category',
            lookupLimit: 5,
            onSelect: function (suggestion) {
                $('#selected_option').html(suggestion.value);
                $('#searchbox').submit();
            }
        });
    }
});
