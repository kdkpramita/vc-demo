import streamlit as st
import json
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import os

# ===============================
# Generate / Load Key Pair
# ===============================
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

# ===============================
# Streamlit UI
# ===============================
st.set_page_config(page_title="Verifiable Credential System", layout="wide")
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
h1 {
    color: white;
    text-align: center;
}
.stButton>button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    padding: 10px;
    font-weight: bold;
    margin-top: 10px;
}
.stButton>button:hover {
    transform: scale(1.02);
}
.stDownloadButton>button {
    background: #28a745;
    color: white;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("🎓 Verifiable Credential System")
st.write("Sistem Kredensial Digital yang Aman dan Terverifikasi")
st.write("---")

# Layout dua kolom
col1, col2 = st.columns(2)

# -------------------------------
# Generate Credential
# -------------------------------
with col1:
    st.subheader("✨ Buat Credential")
    with st.form("generate_form"):
        name = st.text_input("Nama Lengkap")
        course = st.text_input("Nama Course")
        grade = st.text_input("Grade / Nilai")
        generate_btn = st.form_submit_button("Generate Credential")

    if generate_btn:  # <- pindah ke luar form
        if not name or not course or not grade:
            st.error("Semua field harus diisi!")
        else:
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
            st.success("✅ Credential berhasil dibuat!")

            # ✅ Download button di luar form
            st.download_button(
                "📥 Download Credential",
                data=json.dumps(vc, indent=2),
                file_name=filename,
                mime="application/json"
            )

# -------------------------------
# Verify Credential
# -------------------------------
with col2:
    st.subheader("🔍 Verifikasi Credential")
    uploaded_file = st.file_uploader("Upload File Credential (JSON)", type="json")

    if uploaded_file:
        try:
            vc = json.load(uploaded_file)
            proof = vc.pop("proof")
            message = json.dumps(vc, sort_keys=True).encode()
            signature = bytes.fromhex(proof["signatureValue"])

            public_key.verify(
                signature,
                message,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            st.success("🎉 Verifikasi Berhasil! Credential valid dan asli.")
            st.json(vc)
        except Exception as e:
            st.error("❌ Credential tidak valid atau telah dimodifikasi.")
