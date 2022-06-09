document.getElementById("name-dsh").addEventListener('change',function () {
    if( this.value == ''){
        this.removeAttribute('class');
        this.classList.add('border-danger');
    }
    else {
        this.classList.add('border-success');
    }
})
document.getElementById("link-dsh").addEventListener('change',function () {
    if( this.value == ''){
        this.classList.remove('border-success');
        this.classList.add('border-danger');
    }
    else {
        this.classList.remove('border-danger');
        this.classList.add('border-success');
    }
})

function add_some(value) {
    var ddmd = document.getElementById('dropdownMenuDash');

    if(value == 'Все'){
        ddmd.value=value;
        ddmd.classList.remove('border-danger');
        ddmd.classList.add('border-success');
    }
    else{
        if(ddmd.value.includes( 'Все')){
            ddmd.value=value + ' ';
            ddmd.classList.remove('border-danger');
            ddmd.classList.add('border-success');
         }
        else{
            if(ddmd.value.includes(value)){
                var $alert = $('#alert_id');
                $alert.text('Группа уже выбрана!')
                $alert.removeClass('alert-success alert-warning');
                $alert.show().addClass('alert').addClass('alert-warning');
                $alert.delay(4000).hide(100)
                document.getElementById("alert_id").scrollIntoView();
            }
            else {
                ddmd.value=ddmd.value + value + ' ';

                ddmd.classList.remove('border-danger');
                ddmd.classList.add('border-success');
            }
        }

    }

}



