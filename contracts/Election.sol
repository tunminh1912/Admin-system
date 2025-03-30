// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Election {
    struct Candidate {
        uint256 id;
        string fullName;
        string birthDate;
        string gender;
        string nationality;
        string ethnicity;
        string hometown;
        string education;
        string degree;
        string occupation;
        string workplace;
        string status;
    }

    struct ElectionDetails {
        uint id;
        string name;
        string tinh;
        string quan;
        string phuong;
        uint startTime;
        uint endTime;
        mapping(uint => Candidate) candidates;
        Election_status status;
        uint candidateCount;
    }

    struct Participant {
        string name;
        string phone;
        string role; // "ADMIN", "INSPECTOR", "VOTER"
        bool isActive;
    }

    mapping(uint => ElectionDetails) public elections;
    uint public electionCount;

    mapping(address => Participant) public participants;
    address[] public participantAddresses;
    mapping(address => bool) public participantRegistered;

    mapping(uint256 => Candidate) public candidates;
    uint256 public candidateCount;

    event CandidateAdded(uint256 id, string fullName);
    event ElectionCreated(
        uint id,
        string name,
        string tinh,
        string quan,
        string phuong,
        uint startTime,
        uint endTime
    );
    event ParticipantRegistered(address participant, string name, string role);

    enum Role {
        NONE,
        ADMIN,
        INSPECTOR
    }
    mapping(address => Role) public participantRoles;

    function setParticipant(
        address _participant,
        string memory _name,
        string memory _phone,
        Role _role,
        bool _isActive
    ) public {
        if (!participantRegistered[_participant]) {
            participantAddresses.push(_participant);
            participantRegistered[_participant] = true;
        }
        participants[_participant] = Participant(
            _name,
            _phone,
            getRoleString(_role),
            _isActive
        );
        participantRoles[_participant] = _role;
        emit ParticipantRegistered(_participant, _name, getRoleString(_role));
    }

    function getRoleString(Role _role) public pure returns (string memory) {
        if (_role == Role.ADMIN) {
            return "ADMIN";
        } else if (_role == Role.INSPECTOR) {
            return "INSPECTOR";
        } else {
            return "NONE";
        }
    }
    
    enum Election_status { Created, Approved }
    function createElection(
        string memory _name,
        string memory _tinh,
        string memory _quan,
        string memory _phuong,
        uint _startTime,
        uint _endTime
    ) public {
        require(
            _endTime > _startTime,
            "Thoi gian ket thuc phai lon hon thoi gian bat dau"
        );
        require(
            participantRoles[msg.sender] == Role.ADMIN,
            "Only ADMIN can add candidates"
        );

        electionCount++;  // Tăng số lượng election
        uint newElectionId = electionCount;

        ElectionDetails storage newElection = elections[newElectionId];
        newElection.id = newElectionId;
        newElection.name = _name;
        newElection.tinh = _tinh;
        newElection.quan = _quan;
        newElection.phuong = _phuong;
        newElection.startTime = _startTime;
        newElection.endTime = _endTime;
        newElection.status = Election_status.Created;  // ✅ Mặc định là Created
        newElection.candidateCount = 0;

        emit ElectionCreated(
            newElectionId,
            _name,
            _tinh,
            _quan,
            _phuong,
            _startTime,
            _endTime
        );
    }

    function addCandidate(
        string memory _fullName,
        string memory _birthDate,
        string memory _gender,
        string memory _nationality,
        string memory _ethnicity,
        string memory _hometown,
        string memory _education,
        string memory _degree,
        string memory _occupation,
        string memory _workplace
    ) public {
        require(
            participantRoles[msg.sender] == Role.ADMIN,
            "Only ADMIN can add candidates"
        );

        candidateCount++;
        candidates[candidateCount] = Candidate(
            candidateCount,
            _fullName,
            _birthDate,
            _gender,
            _nationality,
            _ethnicity,
            _hometown,
            _education,
            _degree,
            _occupation,
            _workplace,
            "pending"
        );

        emit CandidateAdded(candidateCount, _fullName);
    }
    event LogCandidateId(uint256 candidateId);

    function getCandidate(uint256 _candidateId) public returns (
            uint256,
            string memory,
            string memory,
            string memory,
            string memory,
            string memory,
            string memory,
            string memory,
            string memory,
            string memory,
            string memory,
            string memory
        )
    {
        require(
            _candidateId > 0 && _candidateId <= candidateCount,
            "Candidate does not exist"
        );

        emit LogCandidateId(_candidateId);

        Candidate storage candidate = candidates[_candidateId];

        return (
            candidate.id,
            candidate.fullName,
            candidate.birthDate,
            candidate.gender,
            candidate.nationality,
            candidate.ethnicity,
            candidate.hometown,
            candidate.education,
            candidate.degree,
            candidate.occupation,
            candidate.workplace,
            candidate.status
        );
    }

    function approveCandidate(uint256 _candidateId) public {
        require(
            participantRoles[msg.sender] == Role.INSPECTOR,
            "Only INSPECTOR can approve candidates"
        );
        require(candidates[_candidateId].id != 0, "Candidate does not exist");

        candidates[_candidateId].status = "approved";
    }

    function getApprovedCandidatesByHometown(string memory _workplace) public view returns (Candidate[] memory) {
        uint count = 0;

        // Đếm số lượng ứng viên hợp lệ
        for (uint i = 1; i <= candidateCount; i++) {
            if (
                keccak256(bytes(candidates[i].hometown)) == keccak256(bytes(_workplace)) &&
                keccak256(bytes(candidates[i].status)) == keccak256(bytes("approved"))
            ) {
                count++;
            }
        }

        // Tạo danh sách ứng viên hợp lệ
        Candidate[] memory approvedCandidates = new Candidate[](count);
        uint index = 0;

        for (uint i = 1; i <= candidateCount; i++) {
            if (
                keccak256(bytes(candidates[i].hometown)) == keccak256(bytes(_workplace)) &&
                keccak256(bytes(candidates[i].status)) == keccak256(bytes("approved"))
            ) {
                approvedCandidates[index] = candidates[i];
                index++;
            }
        }

        return approvedCandidates;
    }


    function getElection(uint _id) public view returns (
        uint,
        string memory,
        string memory,
        string memory,
        string memory,
        uint,
        uint,
        uint
    ) {
        require(_id > 0 && _id <= electionCount, "Election does not exist");

        ElectionDetails storage election = elections[_id];

        return (
            election.id,
            election.name,
            election.tinh,
            election.quan,
            election.phuong,
            election.startTime,
            election.endTime,
            uint(election.status) // ✅ Chuyển enum thành uint
        );
    }

    function getCandidatesInElection(uint _electionId) public view returns (Candidate[] memory) {
        require(_electionId > 0 && _electionId <= electionCount, "Election does not exist");

        uint count = elections[_electionId].candidateCount;
        Candidate[] memory candidateList = new Candidate[](count);
        uint index = 0;

        for (uint i = 1; i <= count; i++) {
            candidateList[index] = elections[_electionId].candidates[i];
            index++;
        }

        return candidateList;
    }

    // Mapping để kiểm tra ứng viên đã có trong cuộc bầu cử chưa
    mapping(uint => mapping(uint => bool)) public isCandidateInElection;
        function addCandidateToElection(uint _electionId, uint _candidateId) public {
        require(participantRoles[msg.sender] == Role.ADMIN, "Only ADMIN can add candidates");
        require(elections[_electionId].id != 0, "Election not found");
        require(candidates[_candidateId].id != 0, "Candidate not found");
        require(keccak256(bytes(candidates[_candidateId].status)) == keccak256(bytes("approved")), "Candidate must be approved");
        require(!isCandidateInElection[_electionId][_candidateId], "Candidate is already in this election");

        ElectionDetails storage election = elections[_electionId];

        // Thêm ứng viên vào danh sách cuộc bầu cử
        election.candidateCount++;
        election.candidates[election.candidateCount] = candidates[_candidateId];

        // Đánh dấu ứng viên đã được thêm vào cuộc bầu cử này
        isCandidateInElection[_electionId][_candidateId] = true;

        emit CandidateAddedToElection(_electionId, _candidateId);
    }

    event CandidateAddedToElection(uint electionId, uint candidateId);
}