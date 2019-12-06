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
            lookup: options,
            onSelect: function (suggestion) {
                $('#selected_option').html(suggestion.value);
                $('#searchbox').submit();
            }
        });
    }
});
