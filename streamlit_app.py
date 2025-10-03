from flask import Flask, request, render_template_string, send_file, jsonify
import json
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import os

app = Flask(__name__)

# Generate Key Pair
if not os.path.exists("issuer_private.pem"):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    with open("issuer_private.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open("issuer_public.pem", "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
else:
    with open("issuer_private.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    with open("issuer_public.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verifiable Credential System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .container {
            max-width: 900px;
            width: 100%;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
        }

        .card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            transition: transform 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
        }

        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .icon {
            font-size: 1.3em;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }

        input[type="text"],
        input[type="file"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }

        input[type="file"] {
            padding: 10px;
        }

        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.3s ease;
        }

        button:hover {
            transform: scale(1.02);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        button:active {
            transform: scale(0.98);
        }

        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            display: none;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .download-btn {
            display: inline-block;
            margin-top: 10px;
            padding: 10px 20px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.3s ease;
        }

        .download-btn:hover {
            background: #218838;
        }

        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            display: none;
            margin: 10px auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
            .cards {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Verifiable Credential System</h1>
            <p>Sistem Kredensial Digital yang Aman dan Terverifikasi</p>
        </div>

        <div class="cards">
            <!-- Card Generate -->
            <div class="card">
                <h2><span class="icon">✨</span> Buat Credential</h2>
                <form id="generateForm">
                    <div class="form-group">
                        <label for="name">Nama Lengkap</label>
                        <input type="text" id="name" name="name" required placeholder="Masukkan nama lengkap">
                    </div>
                    <div class="form-group">
                        <label for="course">Nama Course</label>
                        <input type="text" id="course" name="course" required placeholder="Contoh: Web Development">
                    </div>
                    <div class="form-group">
                        <label for="grade">Grade/Nilai</label>
                        <input type="text" id="grade" name="grade" required placeholder="Contoh: A / 95">
                    </div>
                    <button type="submit">Generate Credential</button>
                </form>
                <div class="loader" id="generateLoader"></div>
                <div class="result" id="generateResult"></div>
            </div>

            <!-- Card Verify -->
            <div class="card">
                <h2><span class="icon">🔍</span> Verifikasi Credential</h2>
                <form id="verifyForm">
                    <div class="form-group">
                        <label for="file">Upload File Credential (JSON)</label>
                        <input type="file" id="file" name="file" accept=".json" required>
                    </div>
                    <button type="submit">Verifikasi Credential</button>
                </form>
                <div class="loader" id="verifyLoader"></div>
                <div class="result" id="verifyResult"></div>
            </div>
        </div>
    </div>

    <script>
        // Generate Form
        document.getElementById('generateForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const loader = document.getElementById('generateLoader');
            const result = document.getElementById('generateResult');
            
            loader.style.display = 'block';
            result.style.display = 'none';
            
            const formData = new FormData(e.target);
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                loader.style.display = 'none';
                result.style.display = 'block';
                
                if (data.success) {
                    result.className = 'result success';
                    result.innerHTML = `
                        <strong>✅ Credential Berhasil Dibuat!</strong><br>
                        File: ${data.filename}<br>
                        <a href="/download/${data.filename}" class="download-btn">📥 Download Credential</a>
                    `;
                } else {
                    result.className = 'result error';
                    result.innerHTML = `<strong>❌ Gagal:</strong> ${data.message}`;
                }
            } catch (error) {
                loader.style.display = 'none';
                result.style.display = 'block';
                result.className = 'result error';
                result.innerHTML = '<strong>❌ Terjadi kesalahan!</strong>';
            }
        });

        // Verify Form
        document.getElementById('verifyForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const loader = document.getElementById('verifyLoader');
            const result = document.getElementById('verifyResult');
            
            loader.style.display = 'block';
            result.style.display = 'none';
            
            const formData = new FormData(e.target);
            
            try {
                const response = await fetch('/verify', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                loader.style.display = 'none';
                result.style.display = 'block';
                
                if (data.valid) {
                    result.className = 'result success';
                    result.innerHTML = `
                        <strong>🎉 Verifikasi Berhasil!</strong><br>
                        Credential valid dan asli!<br>
                        <small>Credential ini diterbitkan secara resmi dan belum diubah.</small>
                    `;
                } else {
                    result.className = 'result error';
                    result.innerHTML = `
                        <strong>❌ Verifikasi Gagal!</strong><br>
                        ${data.message}<br>
                        <small>Credential mungkin palsu atau telah dimodifikasi.</small>
                    `;
                }
            } catch (error) {
                loader.style.display = 'none';
                result.style.display = 'block';
                result.className = 'result error';
                result.innerHTML = '<strong>❌ Terjadi kesalahan saat verifikasi!</strong>';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/generate', methods=['POST'])
def generate_vc():
    try:
        name = request.form['name']
        course = request.form['course']
        grade = request.form['grade']

        vc = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "type": ["VerifiableCredential", "CourseCertificate"],
            "issuer": "did:univ:1234",
            "issuanceDate": datetime.utcnow().isoformat() + "Z",
            "credentialSubject": {
                "id": "did:student:5678",
                "name": name,
                "course": course,
                "grade": grade
            }
        }

        message = json.dumps(vc, sort_keys=True).encode()
        signature = private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        vc["proof"] = {
            "type": "RSASignature2018",
            "created": datetime.utcnow().isoformat() + "Z",
            "verificationMethod": "did:univ:1234#keys-1",
            "signatureValue": signature.hex()
        }

        filename = f"credential_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(vc, f, indent=2)

        return jsonify({"success": True, "filename": filename})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/verify', methods=['POST'])
def verify_vc():
    try:
        file = request.files['file']
        vc = json.load(file)

        proof = vc.pop("proof")
        message = json.dumps(vc, sort_keys=True).encode()
        signature = bytes.fromhex(proof["signatureValue"])

        public_key.verify(
            signature,
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return jsonify({"valid": True})
    except Exception as e:
        return jsonify({"valid": False, "message": "Credential tidak valid atau telah dimodifikasi"})


@app.route('/download/<filename>')
def download(filename):
    return send_file(filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)