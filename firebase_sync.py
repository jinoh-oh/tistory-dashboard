import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import json

class FirebaseSync:
    def __init__(self):
        self.db = None
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initializes Firebase using st.secrets if available."""
        try:
            if not firebase_admin._apps:
                # 1. Try to get credentials from Streamlit Secrets
                if "firebase_key" in st.secrets:
                    key_dict = json.loads(st.secrets["firebase_key"])
                    cred = credentials.Certificate(key_dict)
                    firebase_admin.initialize_app(cred)
                    self.db = firestore.client()
                else:
                    st.info("💡 Firebase 설정 전입니다. 로컬 모드로 작동합니다. (배포 시 Secrets 설정 필요)")
        except Exception as e:
            st.error(f"⚠️ Firebase 초기화 에러: {e}")

    def fetch_templates(self):
        """Fetches templates from Firestore."""
        if not self.db:
            return None
        
        try:
            doc_ref = self.db.collection("blog_generator").document("custom_templates")
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict().get("templates", {})
            return {}
        except Exception as e:
            st.warning(f"⚠️ 클라우드 데이터를 가져오는 중 오류가 발생했습니다: {e}")
            return None

    def save_templates(self, templates_dict):
        """Saves templates to Firestore."""
        if not self.db:
            return False
        
        try:
            doc_ref = self.db.collection("blog_generator").document("custom_templates")
            doc_ref.set({"templates": templates_dict})
            return True
        except Exception as e:
            st.error(f"⚠️ 클라우드 저장 실패: {e}")
            return False
