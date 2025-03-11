/* global industriessettings */
$(document).ready(function() {
    const blueprint_searchUrl = industriessettings.IndustryBlueprintSearchUrl;

    $('#id_blueprint').autocomplete({
        source: blueprint_searchUrl,
        minLength: 3,
        autoFocus: true,
        select: function(event, ui){
            SearchTypeID(ui.item.label, ui.item.value);
            updateURLParameter('blueprint_id', ui.item.value);
            $('#blueprintform').submit();
            event.preventDefault();
        },
        focus: function(event, ui){
            event.preventDefault();
        },
    });

    // Handle form submission via AJAX
    $('#blueprintform').submit(function(event) {
        event.preventDefault(); // Prevent the default form submission

        const blueprint_id = $('#id_blueprint_id').val();
        const material_url = industriessettings.IndustryBlueprintUrl.replace('0', blueprint_id);

        // Update DataTable with new URL
        const industriesTable = $('#materials').DataTable();
        industriesTable.ajax.url(material_url).load();

        // Update the URL with the blueprint_id parameter
        updateURLParameter('blueprint_id', blueprint_id);
    });
});

function SearchTypeID(eve_type_name, eve_type_id) {
    $('#id_blueprint_id').val(eve_type_id);
    $('#id_blueprint').val(eve_type_name);
};

function updateURLParameter(param, value) {
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    window.history.replaceState({}, '', url);
}
