
$('#dataTableSms').DataTable({
    order: [],
})


$('#dataTable1').DataTable()
$('#dataTable2').DataTable()
$('#dataTable3').DataTable()

$(document).ready(function() {
    /*
    $('#th_groups').each( function () {
        var title = $(this).text();
        $(this).html( '<input type="text" placeholder="Search '+title+'" />' );
    } );*/

    $('#dataTableConfirm').DataTable()

    $('#dataTableScheduleAll').DataTable()

    $('#dataTableSchedule').DataTable( {
        initComplete: function () {
            this.api().columns([0, 1]).every( function () {
                var column = this;
                var select = $('<select class="form-control"><option value="">Все</option></select>')
                    .appendTo( $(column.footer()).empty() )
                    .on( 'change', function () {
                        var val = $.fn.dataTable.util.escapeRegex(
                            $(this).val()
                        );

                        column
                            .search( val ? '^'+val+'$' : '', true, false )
                            .draw();
                    } );

                column.data().unique().sort().each( function ( d, j ) {
                    select.append( '<option >'+d+'</option>' )
                } );
            } );
        }
    } );

    $('#dataTable0').DataTable( {
        initComplete: function () {


            this.api().columns([0, 2, 3]).every( function () {
                var column = this;
                var select = $('<select class="form-control"><option value="">all</option></select>')
                    .appendTo( $(column.footer()).empty() )
                    .on( 'change', function () {
                        var val = $.fn.dataTable.util.escapeRegex(
                            $(this).val()
                        );

                        column
                            .search( val ? '^'+val+'$' : '', true, false )
                            .draw();
                    } );

                column.data().unique().sort().each( function ( d, j ) {
                    select.append( '<option >'+d+'</option>' )
                } );
            } );
        }
    } );
/*
    document.getElementById("txtSearch").addEventListener("input", function () {
        $('#dataTable0')
            .DataTable()
            .search($('#txtSearch').val(), false, true)
            .draw();
    });*/
} );


$('.compact').DataTable(
    {
        "paging":   false,
        "ordering": false,
        "info":     false
    }
)


$('.dataTables_filter input[type="search"]').css(
     {'width':'400px','display':'inline-block', 'height':'25px'}
     );
