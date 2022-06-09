window.addEventListener('DOMContentLoaded', function () {
    var image1 = document.getElementById('image1');
    var image2 = document.getElementById('image2');
    var file_load1 = document.getElementById('file_load_id1');
    var file_load2 = document.getElementById('file_load_id2');

    file_load1.addEventListener('change', function (e) {
        var files = e.target.files;
        var done = function (url) {
            image1.src = url;
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

        document.getElementById('delBtn').hidden = false;
    });

    file_load2.addEventListener('change', function (e) {
        var files = e.target.files;
        var done = function (url) {
            image2.src = url;
        };
        var reader;
        var file;
        //var url;
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

        document.getElementById('delBtn').hidden = false;
    });
});