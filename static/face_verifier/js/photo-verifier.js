window.addEventListener('DOMContentLoaded', function () {
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

    document.getElementById('sendBtn').addEventListener('click', function () {
        var $progress = $('.progress');
        var $progressBar = $('.progress-bar');
        var progressbar_id = $('#progressbar_id');
        var curRow = document.getElementById("curRow"),
            descendents = curRow.getElementsByTagName('img'),
            checkboxes = curRow.getElementsByTagName('input');

        var data ='{';
        var j = 0
        for (i = 0; i < descendents.length; ++i) {
            if (checkboxes[i].checked){
                j ++;
                var desc = '/srv/project/ganymede/media' + descendents[i].src.split('/media')[1]
                if (j == 1){
                    data = data + '"' + (i + 1).toString()+ '":"' + desc
                }
                else{
                    data = data + '","' + (i + 1).toString()+ '":"' + desc
                }
            }
        }
        if (j == 0){
            data = data + '}'
        }
        else{
            data = data + '"}'
        }

        var formData = new FormData();
        formData.append('data', data);

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
                $alert.removeClass('alert-success alert-warning');
                $alert.show().addClass('alert-success').text('Загрузка прошла успешно! Сообщение: \n' + resp);
                document.getElementById("alert_id").scrollIntoView();
            },

            error: function (response) {
                $alert.removeClass('alert-success alert-warning');
                $alert.show().addClass('alert-warning').text('Ошибка : ' + response.responseText);
                document.getElementById("alert_id").scrollIntoView();
            },

            complete: function () {
                $progress.hide();
            },
        });
    });
});