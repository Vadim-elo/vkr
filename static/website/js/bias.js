function getAddition(num, index,del_fio,bias_profile_url,adr) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrftoken = getCookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    var csrfmiddlewaretoken = getCookie('csrftoken')
    var $alert = $('#alert_id_db');
    $alert.removeClass('alert-success alert-warning');
    var formData = new FormData();
    formData.append('request_number', num);
    formData.append('request_address', adr);
    formData.append('del_fio', del_fio);
    formData.append('csrfmiddlewaretoken', csrfmiddlewaretoken);
    $.ajax({
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,

        success: function (response) {
            if (response !== 'empty'){
                var buttonFooter = document.createElement('div')
                buttonFooter.classList.add("btn");
                buttonFooter.classList.add("btn-secondary");
                buttonFooter.type='button'
                buttonFooter.setAttribute("data-dismiss", "modal");
                buttonFooter.textContent = 'Отмена';

                var divModalFooter = document.createElement('div')
                divModalFooter.classList.add("modal-footer");
                divModalFooter.appendChild(buttonFooter)

                var divModalBody = document.createElement('div')
                divModalBody.classList.add("modal-body");

                var elem_count = 0
                for (var data in response) {
                    var tbodyBody = document.createElement('tbody');
                    var responseData = response[data]
                    for (var item in responseData.fio){
                        elem_count++;
                        var tdFioBody = document.createElement('td');
                        var tdDateBody = document.createElement('td');
                        var tdPlaceBody = document.createElement('td');

                        tdDateBody.innerText = responseData.birthdate[item]
                        tdPlaceBody.innerText = responseData.birthplace[item]

                        var formBody = document.createElement('form');
                        formBody.target = "_blank";
                        formBody.method = "post";
                        formBody.action = bias_profile_url

                        var formBtn = document.createElement('button');
                        formBtn.classList.add("bias-profile-button");
                        formBtn.value = responseData.fio[item]
                        formBtn.name = "_fio"
                        formBtn.type = "submit"
                        formBtn.innerText = responseData.fio[item]

                        var formDate = document.createElement('input');
                        formDate.hidden = true;
                        formDate.type = "text";
                        formDate.name = "_birthdate_result";
                        formDate.value = responseData.birthdate[item]

                        var inputCsrf = document.createElement('input');
                        inputCsrf.type = 'hidden';
                        inputCsrf.name = 'csrfmiddlewaretoken';
                        inputCsrf.value = csrfmiddlewaretoken;

                        formBtn.classList.add("bias-profile-button");
                        formBtn.value = responseData.fio[item]
                        formBtn.name = "_fio"
                        formBtn.type = "submit"
                        formBtn.innerText = responseData.fio[item]

                        formBody.appendChild(formBtn)
                        formBody.appendChild(formDate)

                        if (num !== '') {
                            var formNum = document.createElement('input');
                            formNum.hidden = true;
                            formNum.type = "text";
                            formNum.name = "_input_phone";
                            formNum.value = num

                            formBody.appendChild(formNum)
                        }

                        if (adr !== '') {
                            var formAdr = document.createElement('input');
                            formAdr.hidden = true;
                            formAdr.type = "text";
                            formAdr.name = "_adr";
                            formAdr.value = adr

                            formBody.appendChild(formAdr)
                        }

                        formBody.appendChild(inputCsrf);

                        tdFioBody.appendChild(formBody)

                        var trFor = document.createElement('tr');
                        trFor.appendChild(tdFioBody)
                        trFor.appendChild(tdDateBody)
                        trFor.appendChild(tdPlaceBody)

                        tbodyBody.appendChild(trFor)
                    }

                    var thFioBody=document.createElement('th');
                    thFioBody.innerText = 'ФИО';
                    var thDateBody=document.createElement('th');
                    thDateBody.innerText = 'Дата рождения';
                    var thPlaceBody=document.createElement('th');
                    thPlaceBody.innerText = 'Место рождения;'

                    var trBody=document.createElement('tr');
                    trBody.appendChild(thFioBody)
                    trBody.appendChild(thDateBody)
                    trBody.appendChild(thPlaceBody)

                    var theadBody=document.createElement('thead');
                    theadBody.appendChild(trBody)

                    if (data === 'list_2') {
                        var pTable = document.createElement('p');
                        pTable.classList.add("font-weight-bold");
                        pTable.innerText = 'Возможно, Вы искали:';
                        divModalBody.appendChild(pTable);
                    }
                    var tableBody=document.createElement('table');
                    tableBody.classList.add("table");
                    tableBody.style = "font-size: 14px;";
                    tableBody.appendChild(theadBody)
                    tableBody.appendChild(tbodyBody)

                    divModalBody.appendChild(tableBody)
                }

                var buttonClose = document.createElement('button')
                buttonClose.classList.add("close");
                buttonClose.type='button'
                buttonClose.setAttribute("data-dismiss", "modal");
                buttonClose.setAttribute("aria-label", "Close");

                var hModalTitle = document.createElement('h5')
                hModalTitle.classList.add("modal-title");
                hModalTitle.id='modalLabel' + index;
                if (num!==''){
                    hModalTitle.innerText="Физические лица, связанные общим телефоном"
                }
                if (adr!==''){
                    hModalTitle.innerText="Физические лица, связанные общим адресом"
                }


                var divModalHeader = document.createElement('div')
                divModalHeader.classList.add("modal-header");
                divModalHeader.appendChild(hModalTitle)
                divModalHeader.appendChild(buttonClose)

                var divModalContent = document.createElement('div')
                divModalContent.classList.add("modal-content");
                divModalContent.appendChild(divModalHeader);
                divModalContent.appendChild(divModalBody);
                divModalContent.appendChild(divModalFooter);

                var divModalDialog = document.createElement('div')
                divModalDialog.classList.add("modal-dialog");
                divModalDialog.classList.add("bias-modal-dialog");
                divModalDialog.setAttribute("role", "document");
                divModalDialog.appendChild(divModalContent);

                var divFade = document.createElement('div')
                divFade.classList.add("modal");
                divFade.classList.add("fade");
                divFade.id='modal' + index;
                divFade.tabIndex="-1";
                divFade.setAttribute("role", "dialog");
                divFade.setAttribute("aria-labelledby", "modalLabel"+index);
                divFade.setAttribute("aria-hidden", "true");
                divFade.appendChild(divModalDialog);

                /*
                jQuery(tableBody).DataTable(
                {
                    "bFilter": false,
                    "paging": false,
                    "ordering": false,
                    "info": false
                })
                */
                var aPerson = document.getElementById("a" + index)

                var spanPerson =  document.createElement('span');
                spanPerson.classList.add("bias-user-style");

                var spanChildPerson = document.createElement('span');
                spanChildPerson.classList.add("fa");
                spanChildPerson.classList.add("fa-user");
                spanChildPerson.innerText= ' ' + elem_count.toString();

                spanPerson.appendChild(spanChildPerson);
                aPerson.appendChild(spanPerson);

                document.body.appendChild(divFade);
            }
        },


        /*
        success: function (response) {
            if (response !== 'empty'){
                var buttonFooter = document.createElement('div')
                buttonFooter.classList.add("btn");
                buttonFooter.classList.add("btn-secondary");
                buttonFooter.type='button'
                buttonFooter.setAttribute("data-dismiss", "modal");
                buttonFooter.textContent = 'Отмена';

                var divModalFooter = document.createElement('div')
                divModalFooter.classList.add("modal-footer");
                divModalFooter.appendChild(buttonFooter)

                var tbodyBody = document.createElement('tbody');

                var elem_count = 0
                for(var data in response) {
                    var responseData = response[data]
                    console.log(responseData)
                    for (var item in responseData.fio) {
                        elem_count++;
                        var tdFioBody = document.createElement('td');
                        var tdDateBody = document.createElement('td');
                        var tdPlaceBody = document.createElement('td');

                        tdDateBody.innerText = responseData.birthdate[item]
                        tdPlaceBody.innerText = responseData.birthplace[item]

                        var formBody = document.createElement('form');
                        formBody.target = "_blank";
                        formBody.method = "post";
                        formBody.action = bias_profile_url

                        var formBtn = document.createElement('button');
                        formBtn.classList.add("bias-profile-button");
                        formBtn.value = responseData.fio[item]
                        formBtn.name = "_fio"
                        formBtn.type = "submit"
                        formBtn.innerText = responseData.fio[item]

                        var formDate = document.createElement('input');
                        formDate.hidden = true;
                        formDate.type = "text";
                        formDate.name = "_birthdate_result";
                        formDate.value = responseData.birthdate[item]

                        var inputCsrf = document.createElement('input');
                        inputCsrf.type = 'hidden';
                        inputCsrf.name = 'csrfmiddlewaretoken';
                        inputCsrf.value = csrfmiddlewaretoken;

                        formBtn.classList.add("bias-profile-button");
                        formBtn.value = responseData.fio[item]
                        formBtn.name = "_fio"
                        formBtn.type = "submit"
                        formBtn.innerText = responseData.fio[item]

                        formBody.appendChild(formBtn)
                        formBody.appendChild(formDate)

                        if (num !== '') {
                            var formNum = document.createElement('input');
                            formNum.hidden = true;
                            formNum.type = "text";
                            formNum.name = "_input_phone";
                            formNum.value = num

                            formBody.appendChild(formNum)
                        }

                        if (adr !== '') {
                            var formAdr = document.createElement('input');
                            formAdr.hidden = true;
                            formAdr.type = "text";
                            formAdr.name = "_adr";
                            formAdr.value = adr

                            formBody.appendChild(formAdr)
                        }

                        formBody.appendChild(inputCsrf);

                        tdFioBody.appendChild(formBody)

                        var trFor = document.createElement('tr');
                        trFor.appendChild(tdFioBody)
                        trFor.appendChild(tdDateBody)
                        trFor.appendChild(tdPlaceBody)

                        tbodyBody.appendChild(trFor)
                    }
                }

                var thFioBody=document.createElement('th');
                thFioBody.innerText = 'ФИО';
                var thDateBody=document.createElement('th');
                thDateBody.innerText = 'Дата рождения';
                var thPlaceBody=document.createElement('th');
                thPlaceBody.innerText = 'Место рождения;'

                var trBody=document.createElement('tr');
                trBody.appendChild(thFioBody)
                trBody.appendChild(thDateBody)
                trBody.appendChild(thPlaceBody)

                var theadBody=document.createElement('thead');
                theadBody.appendChild(trBody)

                var tableBody=document.createElement('table');
                tableBody.classList.add("table");
                tableBody.style = "font-size: 14px;";
                tableBody.appendChild(theadBody)
                tableBody.appendChild(tbodyBody)

                var divModalBody = document.createElement('div')
                divModalBody.classList.add("modal-body");
                divModalBody.appendChild(tableBody)

                var buttonClose = document.createElement('button')
                buttonClose.classList.add("close");
                buttonClose.type='button'
                buttonClose.setAttribute("data-dismiss", "modal");
                buttonClose.setAttribute("aria-label", "Close");

                var hModalTitle = document.createElement('h5')
                hModalTitle.classList.add("modal-title");
                hModalTitle.id='modalLabel' + index;
                if (num!==''){
                    hModalTitle.innerText="Физические лица, связанные общим телефоном"
                }
                if (adr!==''){
                    hModalTitle.innerText="Физические лица, связанные общим адресом"
                }


                var divModalHeader = document.createElement('div')
                divModalHeader.classList.add("modal-header");
                divModalHeader.appendChild(hModalTitle)
                divModalHeader.appendChild(buttonClose)

                var divModalContent = document.createElement('div')
                divModalContent.classList.add("modal-content");
                divModalContent.appendChild(divModalHeader);
                divModalContent.appendChild(divModalBody);
                divModalContent.appendChild(divModalFooter);

                var divModalDialog = document.createElement('div')
                divModalDialog.classList.add("modal-dialog");
                divModalDialog.classList.add("bias-modal-dialog");
                divModalDialog.setAttribute("role", "document");
                divModalDialog.appendChild(divModalContent);

                var divFade = document.createElement('div')
                divFade.classList.add("modal");
                divFade.classList.add("fade");
                divFade.id='modal' + index;
                divFade.tabIndex="-1";
                divFade.setAttribute("role", "dialog");
                divFade.setAttribute("aria-labelledby", "modalLabel"+index);
                divFade.setAttribute("aria-hidden", "true");
                divFade.appendChild(divModalDialog);

                jQuery(tableBody).DataTable(
                {
                    "bFilter": false,
                    "paging": false,
                    "ordering": false,
                    "info": false
                })
                var aPerson = document.getElementById("a" + index)

                var spanPerson =  document.createElement('span');
                spanPerson.classList.add("bias-user-style");

                var spanChildPerson = document.createElement('span');
                spanChildPerson.classList.add("fa");
                spanChildPerson.classList.add("fa-user");
                spanChildPerson.innerText= ' ' + elem_count.toString();

                spanPerson.appendChild(spanChildPerson);
                aPerson.appendChild(spanPerson);

                document.body.appendChild(divFade);
            }
        },
         */

        error: function (response) {
            $alert.removeClass('alert-success alert-warning');
            $alert.show().addClass('alert-warning').text('Ошибка!');
            $alert.delay(2000).hide(100)
            document.getElementById("alert_id_db").scrollIntoView();
        },
    });
}
