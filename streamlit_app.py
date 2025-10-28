import streamlit as st
import json
import hashlib
from datetime import datetime
import os

# ===============================
# Fungsi untuk membuat hash SHA-256
# ===============================
def generate_hash(data):
    """Menghasilkan hash SHA-256 dari data JSON"""
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

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
.subtitle {
    text-align: center;
    font-size: 18px;
    color: white;
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

# Judul & Subjudul di tengah
st.markdown("<h1>🎓 Verifiable Credential System</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Sistem Kredensial Digital Aman & Terverifikasi (Hash-based)</p>", unsafe_allow_html=True)
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

    if generate_btn:
        if not name or not course or not grade:
            st.error("Semua field harus diisi!")
        else:
            # Membuat struktur credential
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

            # 🔐 Tambahkan hash
            vc_hash = generate_hash(vc)
            vc["proof"] = {
                "type": "HashSHA256Proof",
                "created": datetime.utcnow().isoformat() + "Z",
                "verificationMethod": "did:univ:1234#hash",
                "hashValue": vc_hash
            }

            filename = f"credential_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            st.success("✅ Credential berhasil dibuat dan dilindungi dengan hash!")
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
            proof = vc.get("proof", None)

            if proof and "hashValue" in proof:
                stored_hash = proof["hashValue"]
                # Buang bagian proof sebelum hashing ulang
                vc.pop("proof")
                recalculated_hash = generate_hash(vc)

                if stored_hash == recalculated_hash:
                    st.success("🎉 Verifikasi Berhasil! Credential valid dan belum dimodifikasi.")
                    st.json(vc)
                else:
                    st.error("❌ Credential tidak valid atau telah dimodifikasi.")
            else:
                st.warning("⚠️ File tidak memiliki hash untuk diverifikasi.")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat verifikasi: {e}")
