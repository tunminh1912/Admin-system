// users.js
function loadUsers() {
    fetch('/users')
        .then(response => response.json())
        .then(users => {
            const userTable = document.querySelector('.users tbody');
            userTable.innerHTML = users.map((user, index) => `
                <tr>
                    <td>${index + 1}</td>
                    <td>
                        <button
                            class="approve-button ${user.is_approved ? 'approved' : 'pending'}"
                            data-user-id="${user._id}"
                            onclick="toggleApproveUser('${user._id}')"
                            ${user.is_approved ? 'disabled' : ''}
                        >
                            ${user.is_approved ? 'Đã duyệt' : 'Chờ duyệt'}
                        </button>
                    </td>
                    <td>${user.fullname}</td>
                    <td>${user.date_of_birth || 'Chưa cập nhật'}</td>
                    <td>${user.hometown || 'Chưa cập nhật'}</td>
                    <td>${user.phone || 'Chưa cập nhật'}</td>
                    <td>${user.id_document_path || 'Chưa cập nhật'}</td>
                </tr>
            `).join('');
            document.querySelector('.users').classList.add('active');
        })
        .catch(error => console.error('Lỗi khi tải danh sách người dùng:', error));
}

function toggleApproveUser(userId) {
    fetch(`/admin/approve_user/${userId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('Phê duyệt người dùng thành công:', userId);

                const button = document.querySelector(`.approve-button[data-user-id="${userId}"]`);
                if (button) {
                    button.classList.remove('pending');
                    button.classList.add('approved');
                    button.textContent = 'Đã duyệt';
                    button.disabled = true; // Disable the button after approval
                }
            } else {
                console.error('Lỗi phê duyệt người dùng:', data.message);
                alert('Lỗi phê duyệt người dùng: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Lỗi khi gửi yêu cầu phê duyệt:', error);
            alert('Lỗi khi gửi yêu cầu phê duyệt.');
        });
}