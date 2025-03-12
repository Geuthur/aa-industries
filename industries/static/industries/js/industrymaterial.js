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
        columns: [
            {
                data: 'material',
                orderable: false,
                render: function (data, type, row) {
                    const hasSubmaterials = row.is_submaterial;
                    const buttonHtml = hasSubmaterials ? `
                        <button id="material" class="btn btn-secondary industries-collapse" data-mtypeid="${row.material_eve_type_id}" data-quantity="${row.quantity}">
                            <i class="fas fa-chevron-right fa-sm"></i>
                        </button>
                    ` : '';
                    return `
                        ${buttonHtml}
                        <span data-tooltip-toggle="industries-tooltip" title="">${data}</span>
                    `;
                }
            },
            {
                data: 'quantity',
                orderable: false,
                render: function (data) {
                    return data.toLocaleString();
                },
                className: 'quantity',
            },
            {
                data: 'in_stock',
                orderable: false,
                render: function (data, type, row) {
                    return `<input type="number" id="instock-${row.material_eve_type_id}" class="form-control instock-input w-25" value="${data}" min="0" />`;
                }
            },
            {
                data: 'price',
                orderable: false,
                render: function (data) {
                    return data;
                }
            }

        ],
        rowCallback: function (row, data) {
            $(row).attr('id', `material`);
            $(row).data('original-quantity', data.quantity); // Store the original quantity
        },
        order: [[0, 'asc']],
        paging: false,
        searching: false,
        info: false,
    });

    industriesTable.on('draw', function () {
        $('[data-tooltip-toggle="industries-tooltip"]').tooltip({
            trigger: 'hover',
        });
    });

    // Event listener for collapse functionality
    $(document).on('click', '.industries-collapse', function () {
        const button = $(this);
        const materialId = button.data('mtypeid');
        const quantity = button.data('quantity');
        const parentRow = button.closest('tr');

        let parentId = parentRow.attr('id');
        if (!parentId) {
            parentId = `material`;
            parentRow.attr('id', parentId);
        }

        const submaterialsRowId = `${parentId}-${materialId}`;
        const submaterialsRow = $(`#${submaterialsRowId}`);

        if (submaterialsRow.length) {
            button.find('i').toggleClass('fa-chevron-right fa-chevron-down');
            $(`.submaterials-row[id="${submaterialsRowId}"]`).not(parentRow).toggleClass('d-none');
        } else {
            const submaterialsUrl = `/industries/api/industry/${materialId}/quantity/${quantity}/view/industry/material/?unique_id=${submaterialsRowId}`;
            $.ajax({
                url: submaterialsUrl,
                type: 'GET',
                success: function (data) {
                    button.find('i').toggleClass('fa-chevron-right fa-chevron-down');
                    const newrow = $(data).insertAfter(parentRow);

                    // Get the padding of the previous submaterial td group
                    const submaterialPrevTd = parentRow.find('.submaterials-td');
                    let submaterialPrevCount = submaterialPrevTd.data('padding');

                    // If there is no previous submaterial group, set the padding to 0
                    if (!submaterialPrevCount) {
                        submaterialPrevCount = 0;
                    }

                    // Get the current submaterial td group
                    const submaterialTd = newrow.find('.submaterials-td')

                    // Set the padding for the current submaterial td group
                    const newPaddingLeft = submaterialPrevCount + 2;

                    // Add CSS to the submaterial td group
                    newrow.find('td#' + submaterialsRowId).css('padding-left', newPaddingLeft + '%');

                    // Set the new padding value for the current submaterial td group
                    submaterialTd.data('padding', newPaddingLeft);
                },
                error: function (xhr, error, thrown) {
                    console.error('Error loading submaterials:', error);
                }
            });
        }
    });

    // Event listener for in_stock input changes
    $(document).on('input', '.instock-input', function () {
        const input = $(this);
        const newInStock = parseInt(input.val(), 10) || 0;
        const row = input.closest('tr');
        const quantityCell = row.find('.quantity');
        // Store the original quantity
        const originalQuantity = row.data('original-quantity');
        // Ensure the new quantity is at least 0
        const newQuantity = Math.max(originalQuantity - newInStock, 0);

        quantityCell.text(newQuantity.toLocaleString());
    });
});
