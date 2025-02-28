/* global industriessettings */
$(document).ready(() => {
    const industries = $('#materials');
    const blueprint_url = industriessettings.IndustryTestUrl.replace('0', industriessettings.blueprint_id);

    const industriesTable = industries.DataTable({
        ajax: {
            url: blueprint_url,
            type: 'GET',
            dataSrc: function (data) {
                if (Array.isArray(data.materials)) {
                    return data.materials;
                } else {
                    console.error('Unexpected data format:', data);
                    return [];
                }
            },
            error: function (xhr, error, thrown) {
                console.error('Error loading data:', error);
                industriesTable.clear().draw();
            }
        },
        stateSave: true, // Enable state saving
        columns: [
            {
                data: 'portrait',
                render: function (data, type, row) {
                    return data;
                }
            },
            {
                data: 'material_eve_type__name',
                render: function (data, type, row) {
                    return `<span data-tooltip-toggle="industries-tooltip" title="${row.description}">${data}</span>`;
                }
            },
            {
                data: 'quantity',
                render: function (data) {
                    return data.toLocaleString();
                }
            },
            {
                data: 'details',
                render: function (data) {
                    return data;
                }
            },
        ],
        order: [[1, 'asc']],
    });

    industriesTable.on('draw', function (row, data) {
        $('[data-tooltip-toggle="industries-tooltip"]').tooltip({
            trigger: 'hover',
        });
    });

    function renderSubmaterials(materials) {
        if (!materials || materials.length === 0) {
            return '';
        }
        let submaterialsHtml = '<ul>';
        materials.forEach(material => {
            submaterialsHtml += `<li>${material.material_eve_type__name} (${material.quantity.toLocaleString()})`;
            if (material.materials && material.materials.length > 0) {
                submaterialsHtml += renderSubmaterials(material.materials);
            }
            submaterialsHtml += '</li>';
        });
        submaterialsHtml += '</ul>';
        return submaterialsHtml;
    }
});
