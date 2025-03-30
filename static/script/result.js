function fetchResult() {
    fetch("/get_elections")
        .then(response => response.json())
        .then(elections => {
            const tbody = document.querySelector(".results tbody");
            tbody.innerHTML = ""; // Xóa dữ liệu cũ

            elections.forEach(election => {
                // Tạo hàng trước để đảm bảo dữ liệu không bị lỗi khi fetch vote count
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${election.id}</td>
                    <td>${election.tenCuocBauCu}</td>
                    <td>${election.tinh}</td>
                    <td>${election.thoiGianBatDau}</td>
                    <td>${election.thoiGianKetThuc}</td>
                    <td class="vote-count">Đang tải...</td>
                    <td>${election.status}</td>
                    <td><button onclick="approveElection('${election.id}')">Duyệt</button></td>
                `;
                tbody.appendChild(row);
                getTotalCount(election.id, row)
            });
        })
        .catch(error => console.error("Lỗi khi tải danh sách cuộc bầu cử:", error));
}



function approveElection(electionId) {
    const privateKey = prompt("Nhập Private Key của bạn để duyệt:");

    if (!privateKey) {
        alert("Bạn cần nhập Private Key!");
        return;
    }

    fetch(`/approve_election/${electionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ privateKey: privateKey })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert("✅ " + data.message);
                fetchResult(); // Cập nhật lại danh sách
            } else {
                alert("❌ Lỗi: " + data.error);
            }
        })
        .catch(error => console.error("Lỗi:", error));
}

function getTotalCount(electionId, row) {
    fetch(`http://127.0.0.1:5000/get_vote_count/${electionId}`)
        .then(response => response.json())
        .then(data => {
            row.querySelector(".vote-count").textContent = data.vote_count || 0;
        })
        .catch(error => {
            console.error(`Lỗi khi lấy số phiếu cho election ${electionId}:`, error);
            row.querySelector(".vote-count").textContent = "Lỗi";
        });
}
