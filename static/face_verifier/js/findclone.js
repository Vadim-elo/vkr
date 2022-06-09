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
    document.getElementById('delBtn').hidden = false;
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

      canvas.toBlob(function (blob) {
        var formData = new FormData();

        formData.append('avatar', blob, 'avatar.jpg');
        $.ajax({
          method: 'POST',
          data: formData,
          processData: false,
          contentType: false,

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
            avatar.src = initialAvatarURL;
            $alert.removeClass('alert-success alert-warning');
            $alert.show().addClass('alert-warning').text('Ошибка: ' + response.responseText);
            document.getElementById("alert_id").scrollIntoView();
          },
        });
      });
    }
  });

  document.getElementById('delBtn').addEventListener('click', function () {
        $('.alert').hide();

        document.getElementById("curRow").innerHTML = '';
        document.getElementById("vkRow").innerHTML = '';
        this.hidden = true;

        document.getElementById("rowSearch").hidden = true;
        document.getElementById("vkRow").hidden = true;
    });
});
