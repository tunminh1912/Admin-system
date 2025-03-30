// elections.js
document.addEventListener("DOMContentLoaded", function () {
    const btnThemCuocBauCu = document.getElementById("btnThemCuocBauCu");
    const formThemCuocBauCu = document.querySelector(".formThemCuocBauCu");
    const btnHuy = document.getElementById("btnHuy"); // Correctly select the "Hủy" button

    if (btnThemCuocBauCu && formThemCuocBauCu) {
        btnThemCuocBauCu.addEventListener("click", function () {
            document.querySelectorAll(".main > div").forEach(div => div.classList.remove("active"));
            formThemCuocBauCu.classList.add("active");
        });
    }

    if (btnHuy) {
        btnHuy.addEventListener("click", function () {
            formThemCuocBauCu.classList.remove("active");
        });
    }

    if (formThemCuocBauCu) {
        formThemCuocBauCu.classList.remove("active"); // Initially hide the form
    }

    fetchElections();
});

document.getElementById("electionForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    let tenCuocBauCu = document.getElementById("tenCuocBauCu").value;

    let tinhSelect = document.getElementById("tinh");
    let quanSelect = document.getElementById("quan");
    let phuongSelect = document.getElementById("phuong");

    let tinh = tinhSelect.options[tinhSelect.selectedIndex].text;
    let quan = quanSelect.options[quanSelect.selectedIndex].text;
    let phuong = phuongSelect.options[phuongSelect.selectedIndex].text;
    let thoiGianBatDau = document.getElementById("thoiGianBatDau").value;
    let thoiGianKetThuc = document.getElementById("thoiGianKetThuc").value;

    let ungCuVien = [];

    let data = {
        tenCuocBauCu,
        tinh,
        quan,
        phuong,
        ungCuVien,
        thoiGianBatDau,
        thoiGianKetThuc
    };

    try {
        let response = await fetch("/add_election", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        let result = await response.json();
        alert(result.message);
        window.location.reload();
    } catch (error) {
        console.error("Lỗi:", error);
    }
});

function fetchElections() {
    fetch("/get_elections")
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector(".elections tbody");
            tbody.innerHTML = ""; // Xóa dữ liệu cũ

            data.forEach((election, index) => {
                const row = `
                    <tr>
                        <td>${election.id}</td>
                        <td>${election.tenCuocBauCu}</td>
                        <td>${election.tinh}</td>
                        <td>${election.quan}</td>
                        <td>${election.phuong}</td>
                        <td>${election.ungCuVien}</td>
                        <td>${election.thoiGianBatDau}</td>
                        <td>${election.thoiGianKetThuc}</td>
                        <td><button onclick="Detail_elections('${election.id}')">Xem</button></td>
                    </tr>
                `;
                tbody.innerHTML += row;
            });
        })
        .catch(error => console.error("Lỗi khi tải danh sách cuộc bầu cử:", error));
}

async function Detail_elections(electionId) {
    try {
        const response = await fetch(`/get_elections/${electionId}`);
        const election = await response.json();

        if (election.error) {
            console.error("Lỗi:", election.error);
            return;
        }

        document.getElementById("modal_tenCuocBauCu").innerText = election.tenCuocBauCu;
        document.getElementById("modal_tinh").innerText = election.tinh;
        document.getElementById("modal_quan").innerText = election.quan;
        document.getElementById("modal_phuong").innerText = election.phuong;
        document.getElementById("modal_thoiGianBatDau").innerText = election.thoiGianBatDau;
        document.getElementById("modal_thoiGianKetThuc").innerText = election.thoiGianKetThuc;

        const tbody = document.getElementById("modal_ungCuVien");
        tbody.innerHTML = "";  // Xóa danh sách cũ

        election.ungCuVien.forEach((ucv, index) => {
            const row = `
                <tr>
                    <td>${ucv.id}</td>
                    <td>${ucv.full_name}</td>
                    <td>${ucv.dob}</td>
                    <td>${ucv.gender}</td>
                    <td>${ucv.nationality}</td>
                    <td>${ucv.ethnicity}</td>
                    <td>${ucv.religion}</td>
                    <td>${ucv.occupation}</td>
                    <td>${ucv.workplace}</td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
        document.getElementById("electionModal").setAttribute("data-id", electionId);
        document.getElementById("electionModal").style.display = "block";

         // Gọi lại để tạo mới danh sách ứng cử viên
        loadApprovedCandidates(electionId);

    } catch (error) {
        console.error("Lỗi khi lấy dữ liệu ứng viên:", error);
    }
}


function closeModal() {
    document.getElementById("electionModal").style.display = "none";
}