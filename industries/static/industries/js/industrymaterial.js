/* global industriessettings */
$(document).ready(() => {
    const industries = $('#materials');
    const blueprint_url = industriessettings.IndustryBlueprintUrl.replace('0', industriessettings.blueprint_id);

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
                    const hasSubmaterials = row.is_submaterial;
                    const buttonHtml = hasSubmaterials ? `
                        <button class="btn btn-secondary industries-collapse" data-mtypeid="${row.material_eve_type_id}" data-quantity="${row.quantity}">
                            <i class="fas fa-chevron-right fa-sm"></i>
                        </button>
                    ` : '';
                    return `
                        ${buttonHtml}
                        <span data-tooltip-toggle="industries-tooltip" title="${row.description}">${data}</span>
                    `;
                }
            },
            {
                data: 'quantity',
                render: function (data) {
                    return data.toLocaleString();
                }
            },
        ],
        order: [[1, 'asc']],
    });

    industriesTable.on('draw', function () {
        $('[data-tooltip-toggle="industries-tooltip"]').tooltip({
            trigger: 'hover',
        });
    });

    // Event listener for collapse functionality
    $('#materials tbody').on('click', '.industries-collapse', function () {
        const button = $(this);
        const materialId = button.data('mtypeid');
        const quantity = button.data('quantity');
        const parentRow = button.closest('tr');
        const parentRowId = parentRow.attr('id') || `material-${materialId}`;

        const submaterialsRowId = `${parentRowId}-submaterials`;
        const submaterialsRow = $(`#${submaterialsRowId}`);

        if (submaterialsRow.length) {
            submaterialsRow.toggleClass('d-none');
            button.find('i').toggleClass('fa-chevron-right fa-chevron-down');
        } else {
            // Fetch submaterials dynamically
            const submaterialsUrl = `/industries/api/industry/${materialId}/quantity/${quantity}/view/industry/material/`;
            $.ajax({
                url: submaterialsUrl,
                type: 'GET',
                success: function (data) {
                    const submaterialsHtml = data.submaterial.map(submaterial => {
                        const submaterialRowId = submaterial.is_submaterial ? `${submaterialsRowId}-${submaterial.material_eve_type_id}` : '';
                        return `
                            <tr ${submaterialRowId ? `id="${submaterialRowId}" class="submaterials-row"` : ''}>
                                <td>${submaterial.portrait}</td>
                                <td>
                                    ${submaterial.is_submaterial ? `
                                        <button class="btn btn-secondary industries-collapse" data-mtypeid="${submaterial.material_eve_type_id}" data-quantity="${submaterial.quantity}">
                                            <i class="fas fa-chevron-right fa-sm"></i>
                                        </button>
                                    ` : ''}
                                    <span data-tooltip-toggle="industries-tooltip" title="${submaterial.description}">${submaterial.material_eve_type__name}</span>
                                </td>
                                <td>${submaterial.quantity}</td>
                            </tr>
                        `;
                    }).join('');

                    const newRowHtml = `
                        <tr id="${submaterialsRowId}" class="submaterials-row">
                            <td colspan="5">
                                <div style="padding-left: 2%;">
                                    <table class="table table-sm table-dark submaterials-table">
                                        <tbody>
                                            ${submaterialsHtml}
                                        </tbody>
                                    </table>
                                </div>
                            </td>
                        </tr>
                    `;

                    $(newRowHtml).insertAfter(button.closest('tr'));
                    button.find('i').toggleClass('fa-chevron-right fa-chevron-down');
                },
                error: function (xhr, error, thrown) {
                    console.error('Error loading submaterials:', error);
                }
            });
        }
    });
});
