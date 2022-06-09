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
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
      var avatar = document.getElementById('avatar');
      var image = document.getElementById('image');
      var input = document.getElementById('input');
      var $progress = $('.progress');
      var $progressBar = $('.progress-bar');
      var $alert = $('.alert');
      var $modal = $('#modal');
      var cropper;

      $('[data-toggle="tooltip"]').tooltip();

      input.addEventListener('change', function (e) {
        var files = e.target.files;
        var done = function (url) {
          input.value = '';
          image.src = url;
          $alert.hide();
          $modal.modal('show');
        };
        var reader;
        var file;
        var url;

        if (files && files.length > 0) {
          file = files[0];

          if (URL) {
            done(URL.createObjectURL(file));
          } else if (FileReader) {
            reader = new FileReader();
            reader.onload = function (e) {
              done(reader.result);
            };
            reader.readAsDataURL(file);
          }
        }
      });

      $modal.on('shown.bs.modal', function () {
        cropper = new Cropper(image, {
          aspectRatio: 'free',
          viewMode: 3,
        });
      }).on('hidden.bs.modal', function () {
        cropper.destroy();
        cropper = null;
      });

      document.getElementById('rotate').addEventListener('click', function () {
          cropper.rotate(90);
      });

      document.getElementById('crop').addEventListener('click', function () {
        var initialAvatarURL;
        var canvas;
        $modal.modal('hide');

        if (cropper) {
          canvas = cropper.rotate(0).getCroppedCanvas({
              maxWidth: 1024,
              maxHeight: 1024,
          });
          initialAvatarURL = avatar.src;
          avatar.src = canvas.toDataURL();
          $progress.show();
          canvas.toBlob(function (blob) {
            var formData = new FormData();

            formData.append('avatar', blob, 'avatar.jpg');
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
                $alert.show().addClass('alert-success').text('Загрузка прошла успешно!');
                document.getElementById("alert_id").scrollIntoView();
              },

              error: function (response) {
                avatar.src = initialAvatarURL;
                $alert.removeClass('alert-success alert-warning');
                $alert.show().addClass('alert-warning').text('Ошибка: ' + response);
                document.getElementById("alert_id").scrollIntoView();
              },

              complete: function () {
                $progress.hide();
              },
            });
          });
        }
      });
    });