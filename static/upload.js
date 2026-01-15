document.getElementById("uploadForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const fileInput = document.getElementById("fileInput");
    if (!fileInput.files.length) return;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload", true);

    xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total * 100).toFixed(1));
            document.getElementById("progressBar").value = percent;
            document.getElementById("progressText").innerText = `${percent}% (${(e.loaded/1024/1024).toFixed(1)} / ${(e.total/1024/1024).toFixed(1)} MB)`;
        }
    };

    xhr.onload = function () {
        if (xhr.status === 200) {
            document.getElementById("progressText").innerText = "완료";
        }
    };

    xhr.send(formData);
});