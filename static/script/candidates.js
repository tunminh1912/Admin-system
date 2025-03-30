// candidates.js

function loadUngCuVien() {
    fetch('/get_candidates')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const ungCuVienTableBody = document.getElementById('ungCuVienTableBody');
            ungCuVienTableBody.innerHTML = '';
            data.forEach((candidate, index) => {
                const row = `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${candidate.full_name}</td>
                        <td>${candidate.birth_date}</td>
                        <td>${candidate.gender}</td>
                        <td>${candidate.nationality}</td>
                        <td>${candidate.ethnicity}</td>
                        <td>${candidate.hometown}</td>
                        <td>${candidate.degree || ''}</td>
                        <td>${candidate.occupation}</td>
                        <td>${candidate.workplace || ''}</td>
                        <td>
                            <span class="${candidate.status === 'approved' ? 'approved' : 'pending'}">
                                ${candidate.status === 'approved' ? 'Đã duyệt' : 'Chờ duyệt'}
                            </span>
                        </td>
                        <td>
                            ${candidate.status !== 'approved' ? `<button onclick="approveCandidateForUngCuVienTable(${candidate.id})">Duyệt</button>` : ''} <!-- Use candidate.id, corrected status check -->
                        </td>
                    </tr>
                `;
                ungCuVienTableBody.innerHTML += row;
            });
        })
        .catch(error => console.error("Lỗi khi tải danh sách ứng cử viên:", error));
}

function approveCandidateForUngCuVienTable(candidateId) {
    const privateKey = prompt("Vui lòng nhập Private Key của bạn:");

    if (!privateKey) {
        alert("Bạn cần nhập Private Key để duyệt ứng cử viên.");
        return;
    }

    fetch(`/approve_candidate/${candidateId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ privateKey: privateKey })
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw err;
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error("Lỗi duyệt:", data.error);
                alert("Lỗi duyệt ứng cử viên: " + data.error);
            } else {
                console.log("Duyệt thành công:", data.message);
                alert("Duyệt ứng cử viên thành công!");
                loadUngCuVien();
            }
        })
        .catch(error => {
            console.error("Error approving candidate:", error);
            alert("Lỗi duyệt ứng cử viên: " + (error.error || error.message || error));
        });
}

document.addEventListener("DOMContentLoaded", function () {
    const btnThemUngCuVien = document.getElementById("btnThemUngCuVien");
    const formThemUngCuVien = document.querySelector(".formThemUngCuVien");
    const btnLuuUngCuVien = document.getElementById('btnLuuUngCuVien');
    const btnHuyUngCuVien = document.getElementById('btnHuyUngCuVien');

    if (btnLuuUngCuVien) {
        btnLuuUngCuVien.addEventListener("click", themUngCuVien);
    }

    loadUngCuVien();

    if (btnThemUngCuVien && formThemUngCuVien) {
        btnThemUngCuVien.addEventListener("click", function () {
            document.querySelectorAll(".main > div").forEach(div => div.classList.remove("active"));
            formThemUngCuVien.classList.add("active");
        });
    }

    if (btnHuyUngCuVien) {
        btnHuyUngCuVien.addEventListener("click", function () {
            formThemUngCuVien.classList.remove("active");
        });
    }

    if (formThemUngCuVien) {
        formThemUngCuVien.classList.remove("active");
    }
});

async function themUngCuVien(event) {
    event.preventDefault();

    const ungCuVienForm = document.getElementById("ungCuVienForm");

    if (!ungCuVienForm) {
        console.error("Không tìm thấy form ungCuVienForm");
        return;
    }

    const formData = new FormData(ungCuVienForm);
    const candidateData = {};

    formData.forEach((value, key) => {
        candidateData[key] = value;
    });

    try {
        let response = await fetch("/add_candidate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(candidateData)
        });

        let result = await response.json();

        if (response.ok) {
            alert("Ứng cử viên đã được thêm thành công!");
            document.querySelector(".formThemUngCuVien").classList.remove("active");
            loadUngCuVien();
            ungCuVienForm.reset();
        } else {
            alert("Lỗi: " + result.error);
        }
    } catch (error) {
        console.error("Lỗi:", error);
        alert("Có lỗi xảy ra khi thêm ứng cử viên.");
    }
}

async function loadApprovedCandidates(electionId) {
    try {
        const response = await fetch(`/get_candidate_hometown/${electionId}`);
        if (!response.ok) {
            throw new Error(`Lỗi khi lấy ứng viên: ${response.statusText}`);
        }
        const candidates = await response.json();
        // Xóa nội dung cũ và tạo lại div
        const parentDiv = document.getElementById("chooseCandidatesSection");
        parentDiv.innerHTML = `
            <h3>Chọn ứng cử viên:</h3>
            <div id="candidateList"></div>
            <button type="button" onclick="submitCandidates('${electionId}')">Thêm ứng cử viên đã chọn</button>
        `;

        const candidateListDiv = document.getElementById("candidateList");

        if (!candidates || candidates.length === 0) {
            candidateListDiv.innerHTML = "<p>Không có ứng viên phù hợp.</p>";
            return;
        }

        candidates.forEach(candidate => {
            const candidateDiv = document.createElement("div");
            candidateDiv.classList.add("candidate-item");

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.dataset.id = candidate.id;  // Dùng dataset để tránh undefined
            checkbox.value = candidate.full_name;  // Lưu tên ứng viên để debug

            const label = document.createElement("label");
            label.htmlFor = `candidate_${candidate.id}`;
            label.textContent = ` (${candidate.id || "Không rõ id"}) ${candidate.full_name}`;

            candidateDiv.appendChild(checkbox);
            candidateDiv.appendChild(label);
            candidateListDiv.appendChild(candidateDiv);
        });

    } catch (error) {
        document.getElementById("candidateList").innerHTML = "<p>Lỗi khi tải danh sách ứng viên.</p>";
    }
}


async function submitCandidates(electionId) {
    const selectedCandidates = [];
    const checkboxes = document.querySelectorAll('#candidateList input[type="checkbox"]:checked');

    checkboxes.forEach(checkbox => {
        const candidateId = checkbox.dataset.id; // Lấy ID từ dataset
        if (candidateId) {
            selectedCandidates.push(candidateId);
        }
    });

    if (selectedCandidates.length === 0) {
        alert("Vui lòng chọn ít nhất một ứng viên.");
        return;
    }

    try {
        let successCount = 0;

        for (let candidateId of selectedCandidates) {
            const data = { election_id: electionId, candidate_id: candidateId };
            console.log(`Gửi dữ liệu:`, data);

            const response = await fetch(`/add_candidate_to_election`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                alert(`Lỗi khi thêm ứng viên ${candidateId}: ${result.error}`);
            } else {
                successCount++;
            }
        }

        if (successCount > 0) {
            alert(`Thêm thành công ${successCount} ứng viên!`);
            Detail_elections(electionId);
            loadApprovedCandidates(electionId);
        }

    } catch (error) {
        alert("Lỗi khi thêm ứng viên. Xem console để biết thêm chi tiết.");
    }
}
