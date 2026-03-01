import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام المسار الذكي - الرابط الدائم", layout="wide")

# --- إدارة البيانات الدائمة ---
DB_FILE = "data_storage.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE).to_dict('records')
    else:
        initial = []
        for sec, count in [("قسم الخروج", 14), ("قسم الدخول", 14), ("قسم صالة القدوم", 8)]:
            for i in range(1, count + 1):
                dtype = "🚛 شحن" if i == 13 and sec != "قسم صالة القدوم" else "⭐ خاص" if i == 14 and sec != "قسم صالة القدوم" else "عادي"
                initial.append({"القسم": sec, "المسار": i, "الحالة": "فارغ", "الموظف": "-", "النوع": dtype, "الفني": "-"})
        pd.DataFrame(initial).to_csv(DB_FILE, index=False)
        return initial

def sync_data(data):
    pd.DataFrame(data).to_csv(DB_FILE, index=False)

# تحميل البيانات
if 'main_db' not in st.session_state:
    st.session_state.main_db = load_data()

# --- واجهة تسجيل الدخول ---
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

if st.session_state.logged_in_user is None:
    st.title("🔐 بوابة المسار الذكي الرسمية")
    u = st.text_input("المستخدم")
    p = st.text_input("الرمز", type="password")
    if st.button("دخول"):
        if u == "admin" and p == "123": # يمكنك إضافة يوزرات أكثر هنا
            st.session_state.logged_in_user = u
            st.rerun()
else:
    # سيظهر هنا كود العمليات الميدانية الذي برمجناه سابقاً
    # مع إضافة sync_data(st.session_state.main_db) بعد كل "استلام" أو "عطل"
    st.sidebar.success(f"متصل: {st.session_state.logged_in_user}")
    if st.sidebar.button("خروج"):
        st.session_state.logged_in_user = None
        st.rerun()
    
    st.write("✅ النظام الآن يعمل على رابط دائم ومحفوظ.")

