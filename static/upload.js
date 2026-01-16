document.getElementById("uploadForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const fileInput = document.getElementById("fileInput");
    if (!fileInput.files.length) return;

    const speedText = document.getElementById("speedText");
    const progressBar = document.getElementById("progressBar");
    const progressContainer = document.querySelector(".progress");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload", true);

    if (progressContainer) progressContainer.style.display = 'flex';

    let startTime = Date.now();
    let lastLoaded = 0;
    let lastTime = startTime;

    xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total * 100).toFixed(1));
            
            progressBar.style.width = percent + "%";
            progressBar.innerText = percent + "%";
            document.getElementById("progressText").innerText = `${percent}% (${(e.loaded/1024/1024).toFixed(1)} / ${(e.total/1024/1024).toFixed(1)} MB)`;
            
            const now = Date.now();
            const deltaBytes = e.loaded - lastLoaded;
            const deltaTime = (now - lastTime) / 1000;

            if (deltaTime > 0){
                const speed = deltaBytes / deltaTime / 1024 / 1024;
                speedText.textContent = `Upload speed: ${speed.toFixed(2)} MB/s`;
            }

            lastLoaded = e.loaded;
            lastTime = now;
        }
    };

    xhr.onload = function () {
        if (xhr.status === 200) {
            document.getElementById("progressText").innerText = "완료";
            setTimeout(() => location.reload(), 1000);
        }
    };

    xhr.send(formData);
});