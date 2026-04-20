// Preview ảnh đại diện
document.addEventListener('DOMContentLoaded', function () {
    const avatarInput = document.getElementById('avatar-input');
    const avatarPreview = document.getElementById('avatar-preview');

    if (avatarInput) {
        avatarInput.addEventListener('change', function (event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    avatarPreview.src = e.target.result;
                    avatarPreview.style.display = 'block';
                    console.log("Đã nạp ảnh thành công!");
                }
                reader.readAsDataURL(file);
            }
        });
    } else {
        console.error("Không tìm thấy ảnh đại diện");
    }
});


//Thêm bằng cấp
function addDegreeRow() {
    const container = document.getElementById('degree-container');
    const degreeId = Date.now();

    const div = document.createElement('div');
    div.className = 'degree-item animate__animated animate__fadeIn';
    div.innerHTML = `
        <button type="button" class="btn-close btn-remove-degree" onclick="this.parentElement.remove()"></button>
        <div class="row">
            <div class="col-md-6">
                <label class="small fw-bold">Tên bằng cấp/chứng chỉ</label>
                <input name="degree_names[]" required class="text-input mt-1" type="text" placeholder="VD: Thạc sĩ Khoa học máy tính..."/>
            </div>
            <div class="col-md-6">
                <label class="small fw-bold">File bằng cấp (PDF)</label>
                <input name="degree_files[]" required class="text-input mt-1" type="file" 
                       accept="application/pdf" onchange="previewPDF(this, '${degreeId}')"/>
                
                <div id="preview-container-${degreeId}" class="mt-2" style="display:none;">
                    <iframe id="preview-${degreeId}" src="" width="100%" height="200px" style="border:1px solid #ccc;"></iframe>
                </div>
            </div>
        </div>
    `;
    container.appendChild(div);
}


//Preview bằng cấp
function previewPDF(input, id) {
    const container = document.getElementById('preview-container-' + id);
    const preview = document.getElementById('preview-' + id);

    if (input.files && input.files[0]) {
        const file = input.files[0];

        if (file.type !== "application/pdf") {
            alert("Vui lòng chỉ chọn file PDF!");
            input.value = "";
            return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            container.style.display = 'block';
        }
        reader.readAsDataURL(file);
    }
}
