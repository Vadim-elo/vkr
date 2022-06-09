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
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


function vk_search(vk_pic){
    var $progress = $('.progress');
    var $progressBar = $('.progress-bar');
    var progressbar_id = $('#progressbar_id');
    var data ='{"vk_path":' + '"/srv/project/ganymede/media' + vk_pic.src.split('/media')[1] + '"}';
    var formData = new FormData();
    formData.append('vk_data', data);

    var $alert = $('.alert');

    $.ajax({
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,

        xhr: function () {
            var xhr = new XMLHttpRequest();

            xhr.upload.onprogress = function (e) {
                var percent = '0';
                var percentage = '0%';
                if (e.lengthComputable) {
                    percent = Math.round((e.loaded / e.total) * 100);
                    percentage = percent + '%';
                    progressbar_id.val(percent).text('Загружено ' + percent + '%');
                    $progressBar.width(percentage).attr('aria-valuenow', percent).text(percentage);
                }
            };
            return xhr;
        },

        success: function (resp) {
            var jsonResponse=JSON.parse(JSON.stringify(resp));

            var i = 1;
            var j = 1;
            for (key in jsonResponse) {
                var curRow = document.getElementById("vkRow")
                var photos = jsonResponse[key]['details']['details']

                var aHeaderH = document.createElement("a");
                aHeaderH.href = jsonResponse[key]['url'];
                aHeaderH.target= "_blank";
                aHeaderH.textContent = jsonResponse[key]['url'] + '\n';

                var hHeader = document.createElement("h6");
                hHeader.classList.add("text-gray-800");
                hHeader.appendChild(aHeaderH);
                hHeader.append(jsonResponse[key]['firstname'] + '\n' + jsonResponse[key]['age'] + '\n' + jsonResponse[key]['city']);
                hHeader.style = "white-space: pre;!important;";

                var divHeader = document.createElement("div");
                divHeader.classList.add("card-header");
                divHeader.classList.add("py-3");
                divHeader.appendChild(hHeader);

                var divBlock = document.createElement("div");
                divBlock.classList.add("row");
                divBlock.classList.add("card-body");
                divBlock.value = j.toString()

                var divCardBlock = document.createElement("div")
                divCardBlock.classList.add("card");
                divCardBlock.classList.add("mb-4");
                divCardBlock.appendChild(divHeader);

                for (photo in photos){
                    console.log(photos[photo]['url']);
                    addElementVkPhoto (photos[photo]['url'],i,divCardBlock,divBlock);
                    i++;
                }
                j++;

            }
            function addElementVkPhoto (src_key,i,divCardBlock,divBlock) {
                var curRow = document.getElementById("vkRow")
                var divCol = document.createElement("div");
                divCol.classList.add("col-lg-1");
                divCol.value = i.toString()

                var divCard = document.createElement("div");
                divCard.classList.add("card");
                divCard.classList.add("shadow");

                var divForm = document.createElement("div");
                divForm.classList.add("t-face-form-small");

                var aBlank = document.createElement("a");
                aBlank.target="_blank";
                aBlank.href = src_key;

                var divImg = document.createElement("img");
                divImg.id = "image_small_" + i.toString()
                divImg.src = src_key;
                divImg.draggable="true";
                divImg.ondragstart = "drag(event)";

                divForm.appendChild(divImg);
                aBlank.appendChild(divForm);
                divCard.appendChild(aBlank);
                divCol.appendChild(divCard);

                divBlock.appendChild(divCol);
                divCardBlock.appendChild(divBlock)

                curRow.appendChild(divCardBlock);
            }
            document.getElementById("vkRow").scrollIntoView();
            $alert.removeClass('alert-success alert-warning');
            $alert.show().addClass('alert-success').text('Загрузка прошла успешно!');
            document.getElementById("rowSearch").hidden = false;
        },

        error: function (response) {
            $alert.removeClass('alert-success alert-warning');
            $alert.addClass('alert-warning').text('Ошибка: ' + response.responseText);
            document.getElementById("alert_id").scrollIntoView();
        },

        complete: function () {
            $progress.hide();
        },
    });
};

function addElementVkSearch (src_key,i) {
    var curRow = document.getElementById("curRow")
    var divCol = document.createElement("div");
    divCol.classList.add("col-lg-1");
    divCol.value = i.toString()

    var divSimple = document.createElement("div");
    var lableSimple = document.createElement("lable");

    var inputCheck = document.createElement("input");
    inputCheck.type = "checkbox";
    inputCheck.classList.add("option-input");
    inputCheck.classList.add("checkbox");
    inputCheck.checked = false;
    inputCheck.id = "checked_" + i.toString()
    lableSimple.appendChild(inputCheck);
    divSimple.appendChild(lableSimple);

    var lableId = document.createElement("lable");
    lableId.classList.add("text-gray-800");
    lableId.textContent = i.toString() + ' фото'
    divSimple.appendChild(lableId);
    divCol.appendChild(divSimple);

    var divCard = document.createElement("div");
    divCard.classList.add("card");
    divCard.classList.add("shadow");

    var divForm = document.createElement("div");
    divForm.classList.add("t-face-form-small");

    var aBlank = document.createElement("a");
    aBlank.target = "_blank";
    aBlank.href = src_key;

    var divImg = document.createElement("img");
    divImg.id = "image_small_" + i.toString()
    divImg.src = src_key;

    divForm.appendChild(divImg);
    aBlank.appendChild(divForm);
    divCard.appendChild(aBlank);
    divCol.appendChild(divCard);

    var btnVK = document.createElement("button");
    btnVK.id = "btnVK_" + i.toString();
    btnVK.type = "button";
    btnVK.classList.add("t-face-button");
    btnVK.textContent = "vk поиск";
    btnVK.onclick = function () {
        document.getElementById("rowSearch").hidden = true;
        document.getElementById("vkRow").innerHTML = '';
        if (document.getElementById("checked_" + i.toString()).checked) {
            vk_search(vk_pic = document.getElementById("image_small_" + i.toString()));
        }
        else{
            var $alert = $('.alert');
            $alert.removeClass('alert-success alert-warning');
            $alert.show().addClass('alert-warning').text('Ошибка : Недостаточно фото для сравнения!');
            document.getElementById("alert_id").scrollIntoView();
        }
    };
    divCol.appendChild(btnVK)
    curRow.appendChild(divCol);
}

document.getElementById('delBtn').addEventListener('click', function () {
    $('.alert').hide();
    $('.progress-bar').hide();

    document.getElementById("curRow").innerHTML = '';
    document.getElementById("vkRow").innerHTML = '';
    this.hidden = true;
    document.getElementById("sendBtn").hidden = true;
    document.getElementById("curRowHead").hidden = true;
    document.getElementById("curRowCom").hidden = true;

    document.getElementById("rowSearch").hidden = true;
    document.getElementById("vkRow").hidden = true;
    document.getElementById('image1').src = "/static/face_verifier/avatar/first.svg"
    document.getElementById('image2').src = "/static/face_verifier/avatar/second.svg"

    document.getElementById("file_load_id1").value = '';
    document.getElementById("file_load_id2").value = '';
});

document.getElementById('verifyBtn').addEventListener('click', function () {
    var $progress = $('.progress');
    var $progressBar = $('.progress-bar');
    var progressbar_id = $('#progressbar_id');
    var formData = new FormData();
    var files_first = $("#file_load_id1")[0].files;
    var files_second = $("#file_load_id2")[0].files;
    var $alert = $('.alert');

    if ((files_first.length + files_second.length) > 0) {
        if (files_first.length > 0) {
            formData.append('first_pic', files_first[0], 'first_pic.jpg');
        }
        if (files_second.length > 0) {
            formData.append('second_pic', files_second[0], 'second_pic.jpg');
        }
        $.ajax({
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,

            xhr: function () {
                var xhr = new XMLHttpRequest();

                xhr.upload.onprogress = function (e) {
                    var percent = '0';
                    var percentage = '0%';
                    if (e.lengthComputable) {
                        percent = Math.round((e.loaded / e.total) * 100);
                        percentage = percent + '%';
                        progressbar_id.val(percent).text('Загружено ' + percent + '%');
                        $progressBar.width(percentage).attr('aria-valuenow', percent).text(percentage);
                    }
                };
                return xhr;
            },

            success: function (resp) {
                var jsonResponse=JSON.parse(JSON.stringify(resp));
                document.getElementById("sendBtn").hidden = false;
                document.getElementById("delBtn").hidden = false;
                document.getElementById("curRowHead").hidden = false;
                document.getElementById("curRowCom").hidden = false;
                var i = 1
                var curRow = document.getElementById("curRow")

                if (curRow.lastChild) {
                    var parsed = parseInt(curRow.lastChild.value);
                    if (parsed > -1) {
                        i = parsed + 1
                    }
                }

                for (key in jsonResponse) {
                    if (key != "texted"){
                        addElementVkSearch (jsonResponse[key],i)
                        i++;
                    }
                }

                $alert.removeClass('alert-success alert-warning');
                $alert.show().addClass('alert-success').text('Загрузка прошла успешно!'); //. Сообщение: ' + jsonResponse.texted
                document.getElementById("alert_id").scrollIntoView();
                /*
                setTimeout(function(){
                    $alert.hide();
                }, 2000);*/
            },

            error: function (response) {
                $alert.removeClass('alert-success alert-warning');
                $alert.show().addClass('alert-warning').text('Ошибка: ' + response.responseText);
                document.getElementById("alert_id").scrollIntoView();
            },

            complete: function () {
                $progress.hide();
            },
        });
    }
    else{
        $alert.removeClass('alert-success alert-warning');
        $alert.show().addClass('alert-warning').text('Ошибка: Не выбраны фото!');
        document.getElementById("alert_id").scrollIntoView();
    }
});
