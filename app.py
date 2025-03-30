import traceback

import certifi
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, Blueprint
from pymongo import MongoClient
from bson import ObjectId
import bcrypt, os
from datetime import datetime
from web3 import Web3
import json
from dotenv import load_dotenv
import config
from web3.exceptions import ContractLogicError, TransactionNotFound

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
provider = os.getenv("WEB3_PROVIDER")
contract_address = os.getenv("CONTRACT_ADDRESS")

auth = Blueprint("auth", __name__)

# Kết nối Web3 với Ganache
w3 = Web3(Web3.HTTPProvider(config.GANACHE_RPC_URL))

# Danh sách tài khoản cố định
accountList = [
    {"role": "ADMIN", "name": "Quản lý cuộc bầu cử", "address": "0xf1a31c5506355261E3D6898522F073d012d2281e"},
    {"role": "INSPECTOR", "name": "Người kiểm duyệt", "address": "0xbb7211e996F784EFD432Ce4bCc7b699d48218a74"},
]

# Lấy accounts từ ganache
def fetchAccounts():
    if w3.is_connected():
        return w3.eth.accounts
    return []

@auth.route("/login", methods=["GET", "POST"])
def login():
    ganache_accounts = fetchAccounts()  # Lấy danh sách tài khoản

    if request.method == "POST":
        address = request.form["address"]

        # Kiểm tra tài khoản có trong danh sách cố định
        user = next((acc for acc in accountList if acc["address"] == address), None)

        # Kiểm tra tài khoản có trong Ganache
        if user and address in ganache_accounts:
            session["user"] = user  # Lưu thông tin vào session
            return redirect(url_for("home"))
        else:
            return "Tài khoản không hợp lệ hoặc không có trong Ganache!", 400

    return render_template("index.html", accounts=accountList)

@auth.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("auth.login"))

def approve_user_endpoint(user_id):
    try:
        try:
            user_object_id = ObjectId(user_id)
        except Exception:
            print(f"User  ID không hợp lệ: {user_id}")
            return jsonify({'success': False, 'message': 'ID người dùng không hợp lệ'}), 400  # Bad Request

        # Tìm user trong collection dựa trên _id
        user = users_collection.find_one({'_id': user_object_id})
        if not user:
            print(f"Không tìm thấy người dùng với ID: {user_id}")
            return jsonify({'success': False, 'message': 'Không tìm thấy người dùng'}), 404  # Not Found

        # Cập nhật trường is_approved thành True
        result = users_collection.update_one(
            {'_id': user_object_id},
            {'$set': {'is_approved': True}}
        )

        if result.modified_count > 0:
            print(f"Đã phê duyệt người dùng thành công: {user_id}")
            return jsonify({'success': True, 'message': 'Phê duyệt người dùng thành công'}), 200  # OK
        else:
            print(f"Không thể phê duyệt người dùng (có thể đã được phê duyệt rồi): {user_id}")
            return jsonify({'success': False,
                            'message': 'Không thể phê duyệt người dùng. Có thể đã được phê duyệt trước đó.'}), 400  # Bad Request

    except Exception as e:
        print(f"Lỗi khi phê duyệt người dùng: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống khi phê duyệt người dùng: {str(e)}'}), 500

# Kết nối với Ganache
w3 = Web3(Web3.HTTPProvider(provider))

if w3.is_connected():
    print("Kết nối thành công với Ganache!")
    accounts = w3.eth.accounts
    if accounts:
        w3.eth.default_account = accounts[0]
        print("Tài khoản mặc định:", w3.eth.default_account)
    else:
        raise Exception("Không tìm thấy tài khoản nào trong Ganache!")
else:
    raise Exception("Kết nối Web3 thất bại!")

# Chuyển đổi địa chỉ contract sang dạng checksum
contract_address = w3.to_checksum_address(contract_address)
print("Địa chỉ smart contract:", contract_address)

# Tải ABI từ file Election.json
with open('build/contracts/Election.json', 'r', encoding='utf-8') as f:
    contract_data = json.load(f)
    abi = contract_data['abi']
    bytecode = contract_data.get('bytecode') or contract_data.get('data', '')

contract = w3.eth.contract(address=contract_address, abi=abi)  # Tạo instance của contract

app = Flask(__name__)
app.secret_key = os.urandom(24)

client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())

db = client.get_database('Block')
users_collection = db.users
elections_collection = db.elections
ungcuvien = db.candidates
app.config.from_object(config)
app.register_blueprint(auth)

@app.route("/")
def index():
    return redirect(url_for("auth.login"))

@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    return render_template("home.html", user=session["user"])

@app.route('/users', methods=['GET'])
def get_users():
    try:
        users = users_collection.find({'is_admin': False})
        user_list = [{
            "_id": str(user["_id"]),
            "is_approved": user.get("is_approved", False),
            "fullname": user.get("fullname", "Không có tên"),
            "date_of_birth": user.get("date_of_birth", "Chưa cập nhật"),
            "hometown": user.get("hometown", "Chưa cập nhật"),
            "phone": user.get("phone", "Chưa cập nhật"),
            "id_document_path": user.get("id_document_path", "Chưa cập nhật"),
            "blockchain_hash": user.get("blockchain_hash", "Chưa cập nhật")
        } for user in users]
        return jsonify(user_list)
    except Exception as e:
        return jsonify({"error": f"Lỗi khi lấy dữ liệu: {str(e)}"}), 500

app.add_url_rule('/admin/approve_user/<user_id>', view_func=approve_user_endpoint, methods=['POST'])

@app.route("/add_election", methods=["POST"])
def create_election():
    data = request.json
    try:
        # Lấy dữ liệu từ request
        tenCuocBauCu = data.get('tenCuocBauCu')
        tinh = data.get('tinh')
        quan = data.get('quan')
        phuong = data.get('phuong')
        thoiGianBatDau_str = data.get('thoiGianBatDau')
        thoiGianKetThuc_str = data.get('thoiGianKetThuc')

        # Kiểm tra dữ liệu đầu vào
        if not all([tenCuocBauCu, tinh, quan, phuong, thoiGianBatDau_str, thoiGianKetThuc_str]):
            return jsonify({"error": "Vui lòng cung cấp đầy đủ thông tin cuộc bầu cử."}), 400

        try:
            start_time = datetime.strptime(thoiGianBatDau_str, "%Y-%m-%dT%H:%M").timestamp()
            end_time = datetime.strptime(thoiGianKetThuc_str, "%Y-%m-%dT%H:%M").timestamp()
        except ValueError as ve:
            return jsonify({"error": f"Định dạng thời gian không hợp lệ: {str(ve)}"}), 400

        # Kiểm tra thời gian hợp lệ
        if end_time <= start_time:
            return jsonify({"error": "Thời gian kết thúc phải lớn hơn thời gian bắt đầu."}), 400

        # Lấy địa chỉ người gọi và chuyển sang checksum
        sender_address = w3.eth.default_account
        try:
            sender_address = w3.to_checksum_address(sender_address)
        except ValueError:
            return jsonify({"error": "Địa chỉ người gửi không hợp lệ."}), 400

        # Kiểm tra số dư tài khoản
        try:
            balance = w3.eth.get_balance(sender_address)
            if balance < 5000000000000000:  # 0.005 ETH
                return jsonify({"error": "Tài khoản không đủ ETH để thực hiện giao dịch."}), 400
        except Exception as e:
            return jsonify({"error": f"Không thể kiểm tra số dư: {str(e)}"}), 500

        try:
            role = contract.functions.participantRoles(sender_address).call()
            if session.get("user", {}).get("role") != "ADMIN":
                return jsonify({"error": "Only ADMIN can approve candidates"}), 403
        except Exception as e:
            return jsonify({"error": f"Không thể xác định vai trò: {str(e)} - Có thể địa chỉ chưa được đăng ký?"}), 500

        try:
            tx_hash = contract.functions.createElection(
                tenCuocBauCu, tinh, quan, phuong,
                int(start_time), int(end_time)
            ).transact({'from': sender_address, 'gas': 3000000})

            # Chờ xác nhận giao dịch
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt["status"] == 0:  # Transaction failed
                return jsonify({"error": "Giao dịch thất bại trên blockchain.", "receipt": receipt}), 500

        except ContractLogicError as e:
            return jsonify({"error": f"Lỗi logic trong contract: {str(e)}", "details": str(e)}), 400
        except Exception as e:
            return jsonify({"error": f"Lỗi khi gọi smart contract: {str(e)}", "details": str(e)}), 500

        # Lưu vào MongoDB
        data['thoiGianBatDau'] = start_time
        data['thoiGianKetThuc'] = end_time
        result = elections_collection.insert_one(data)

        return jsonify({
            "message": "Cuộc bầu cử đã được tạo thành công!",
            "id": str(result.inserted_id),
            "transaction_hash": tx_hash.hex()
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

def format_datetime(dt_value):
    if isinstance(dt_value, float) or isinstance(dt_value, int):
        dt = datetime.fromtimestamp(dt_value)  # Chuyển timestamp (float/int) thành datetime
    elif isinstance(dt_value, str):
        dt = datetime.strptime(dt_value, "%Y-%m-%dT%H:%M")
    else:
        return "Không xác định"
    return dt.strftime("%d/%m/%Y %H:%M")

@app.route('/get_elections', methods=['GET'])
def get_elections():
    try:
        election_count = contract.functions.electionCount().call()
        elections_list = []

        for i in range(1, election_count + 1):
            election = contract.functions.getElection(i).call()
            elections_list.append({
                "id": election[0],
                "tenCuocBauCu": election[1],
                "tinh": election[2],
                "quan": election[3],
                "phuong": election[4],
                "thoiGianBatDau": format_datetime(election[5]),
                "thoiGianKetThuc": format_datetime(election[6]),
            })

        return jsonify(elections_list), 200
    except Exception as e:
        return jsonify({"error": f"Lỗi khi lấy danh sách cuộc bầu cử: {str(e)}"}), 500

@app.route('/get_candidates', methods=['GET'])
def get_all_candidates():
    try:
        print("Bắt đầu lấy danh sách ứng cử viên...")  # Kiểm tra xem route có được gọi không

        candidate_count = contract.functions.candidateCount().call()
        print(f"Số lượng ứng cử viên: {candidate_count}")  # Kiểm tra số lượng ứng cử viên

        candidate_list = []
        for i in range(1, candidate_count + 1):
            print(f"Đang lấy thông tin ứng cử viên có ID: {i}")  # Kiểm tra ID đang được lấy
            candidate = contract.functions.getCandidate(i).call()

            candidate_data = {
                "id": candidate[0],
                "full_name": candidate[1],
                "birth_date": candidate[2],
                "gender": candidate[3],
                "nationality": candidate[4],
                "ethnicity": candidate[5],
                "hometown": candidate[6],
                "education": candidate[7],
                "degree": candidate[8],
                "occupation": candidate[9],
                "workplace": candidate[10],
                "status": candidate[11]
            }
            print(f"Thông tin ứng cử viên {i}: {candidate_data}")  # Kiểm tra thông tin ứng cử viên
            candidate_list.append(candidate_data)

        print(f"Danh sách ứng cử viên trả về: {candidate_list}")  # Kiểm tra danh sách cuối cùng
        return jsonify(candidate_list), 200

    except Exception as e:
        print(f"Lỗi khi lấy danh sách ứng cử viên: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/candidate_count', methods=['GET'])
def candidate_count():
    try:
        count = contract.functions.candidateCount().call()
        return jsonify({"candidate_count": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add_candidate', methods=['POST'])
def add_candidate():
    try:
        # Check if the user is ADMIN
        if session.get("user", {}).get("role") != "ADMIN":
            return jsonify({"error": "Only ADMIN can add candidates"}), 403

        candidate_data = request.json
        full_name = candidate_data.get('full_name', '')
        dob = candidate_data.get('dob', '')
        gender = candidate_data.get('gender', '')
        nationality = candidate_data.get('nationality', '')
        ethnicity = candidate_data.get('ethnicity', '')
        hometown = candidate_data.get('hometown', '')
        education = candidate_data.get('education', '')
        degree = candidate_data.get('degree', '')
        occupation = candidate_data.get('occupation', '')
        workplace = candidate_data.get('workplace', '')
        status = "pending"

        try:
            tx_hash = contract.functions.addCandidate(
                full_name,
                dob,
                gender,
                nationality,
                ethnicity,
                hometown,
                education,
                degree,
                occupation,
                workplace            ).transact({'from': w3.eth.default_account, 'gas': 3000000})

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt['status'] == 1:
                print("Transaction successful!  Receipt:", receipt)  # DEBUG
                return jsonify({"message": "Candidate added successfully!", "transaction_hash": tx_hash.hex()}), 200

            else:
                print("Transaction failed! Receipt:", receipt)
                return jsonify({"error": "Smart contract execution failed", "receipt": receipt}), 500

        except ContractLogicError as e:
            print(f"Contract Logic Error: {e}")
            return jsonify({"error": f"Smart contract rejected transaction: {str(e)}"}), 400  # Indicate a smart contract failure

        except TransactionNotFound as e:
            print(f"Transaction Not Found: {e}")
            return jsonify({"error": f"Transaction not found on the blockchain: {str(e)}"}), 500

    except Exception as e:  # Catch other errors
        print(f"Unexpected Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_elections/<_id>", methods=["GET"])
def get_election_detail(_id):
    try:
        # Lấy thông tin cuộc bầu cử từ smart contract
        election = contract.functions.getElection(int(_id)).call()

        if not election or election[0] == 0:
            return jsonify({"error": "Election not found"}), 404

        # Lấy danh sách ứng cử viên trong cuộc bầu cử từ smart contract
        candidates = contract.functions.getCandidatesInElection(int(_id)).call()

        # Định dạng dữ liệu cuộc bầu cử
        election_detail = {
            "id": election[0],
            "tenCuocBauCu": election[1],
            "tinh": election[2],
            "quan": election[3],
            "phuong": election[4],
            "thoiGianBatDau": format_datetime(election[5]),
            "thoiGianKetThuc": format_datetime(election[6]),
            "ungCuVien": []
        }

        # Định dạng dữ liệu ứng cử viên
        for c in candidates:
            election_detail["ungCuVien"].append({
                "id": c[0],
                "full_name": c[1],
                "dob": c[2],
                "gender": c[3],
                "nationality": c[4],
                "ethnicity": c[5],
                "religion": c[6],
                "hometown": c[7],
                "current_residence": c[8],
                "occupation": c[9],
                "workplace": c[10]
            })

        return jsonify(election_detail), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_candidate_hometown/<_id>", methods=["GET"])
def get_candidate_hometown(_id):
    # Lấy thông tin cuộc bầu cử từ smart contract
    election = contract.functions.getElection(int(_id)).call()
    if not election or election[0] == 0:
        return jsonify({"error": "Election not found"}), 404

    tinh = election[2]

    # Gọi smart contract để lấy danh sách ứng viên đã được phê duyệt theo quê quán
    try:
         # Gọi smart contract để lấy ứng viên đã được phê duyệt theo tỉnh
        approved_candidates = contract.functions.getApprovedCandidatesByHometown(tinh).call()
        candidates_list = []
        for candidate in approved_candidates:
            candidates_list.append({
                "id": candidate[0],
                "full_name": candidate[1],
                "birth_date": candidate[2],
                "gender": candidate[3],
                "nationality": candidate[4],
                "ethnicity": candidate[5],
                "hometown": candidate[6],
                "education": candidate[7],
                "degree": candidate[8],
                "occupation": candidate[9],
                "workplace": candidate[10],
                "status": candidate[11]
            })

        return jsonify(candidates_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/add_candidate_to_election", methods=["POST"])
def add_candidate_to_election():
    try:
        data = request.json
        election_id = int(data.get("election_id"))
        candidate_id = int(data.get("candidate_id"))

        # Kiểm tra cuộc bầu cử tồn tại
        election = contract.functions.getElection(election_id).call()
        if not election or election[0] == 0:
            return jsonify({"error": "Election not found"}), 404

        # Kiểm tra ứng viên đã được duyệt
        candidate = contract.functions.getCandidate(candidate_id).call()
        if not candidate or candidate[0] == 0:
            return jsonify({"error": "Candidate not found"}), 404
        if candidate[11] != "approved":
            return jsonify({"error": "Candidate must be approved"}), 400

        # Gửi giao dịch để thêm ứng viên vào cuộc bầu cử
        tx_hash = contract.functions.addCandidateToElection(election_id, candidate_id).transact({"from": w3.eth.default_account})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return jsonify({"message": "Candidate added successfully", "transaction": receipt.transactionHash.hex()}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/approve_candidate/<candidate_id>", methods=["POST"])
def approve_candidate(candidate_id):
    try:
        # Check if the user is an INSPECTOR
        if session.get("user", {}).get("role") != "INSPECTOR":
            return jsonify({"error": "Only INSPECTOR can approve candidates"}), 403

        # Get the account address of the logged-in user
        user_address = session.get("user", {}).get("address")

        if not user_address:
            return jsonify({"error": "User address not found in session.  Are you logged in?"}), 401
        try:
            candidate_id = int(candidate_id)  # Convert to integer
        except ValueError:
            return jsonify({"error": "Invalid candidate_id. Must be an integer."}), 400

        try:
            tx_hash = contract.functions.approveCandidate(candidate_id).transact({'from': user_address})
            w3.eth.wait_for_transaction_receipt(tx_hash)

        except Exception as contract_err:
            print(f"Contract error: {contract_err}")
            return jsonify({"error": f"Error interacting with contract: {contract_err}"}), 500

        return jsonify({"message": f"Candidate with ID {candidate_id} approved successfully!"}), 200

    except Exception as e:
        print(f"Error approving candidate (approve_candidate): {e}")
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True, port=8800)