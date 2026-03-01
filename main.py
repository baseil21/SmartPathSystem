import streamlit as st
import pandas as pd
import os
from datetime import datetime

# إعدادات احترافية
st.set_page_config(page_title="نظام المسار الذكي الرسمي", layout="wide")

# تصميم الواجهة (اللمسة الاحترافية)
st.markdown("""
    <style>
    .lane-box {
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 10px;
        font-weight: bold;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

DB_FILE = "final_db.csv"

def init_db():
    if not os.path.exists(DB_FILE):
        data = []
        for sec, count in [("قسم الخروج", 14), ("قسم الدخول", 14), ("قسم صالة القدوم", 8)]:
            for i in range(1, count + 1):
                dtype = "🚛 شحن" if i == 13 and sec != "قسم صالة القدوم" else "⭐ خاص" if i == 14 and sec != "قسم صالة القدوم" else "عادي"
                data.append({"القسم": sec, "المسار": i, "الحالة": "فارغ", "الموظف": "-", "النوع": dtype, "الوقت": "-", "البلاغ": "سليم"})
        pd.DataFrame(data).to_csv(DB_FILE, index=False)

init_db()

# الدخول الثابت (لا مجال للخطأ)
if 'auth' not in st.session_state: st.session_state.auth = None

if not st.session_state.auth:
    st.title("🔐 بوابة المسار الذكي - دخول المسؤول")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("الرمز", type="password")
    if st.button("دخول للنظام"):
        if u == "admin" and p == "123":
            st.session_state.auth = "المسؤول"
            st.rerun()
        else: st.error("خطأ في البيانات")
else:
    tab1, tab2 = st.tabs(["🎮 العمليات الميدانية", "📋 التقارير والطباعة"])
    db = pd.read_csv(DB_FILE)

    with tab1:
        sec = st.radio("اختر القسم العملياتي:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"], horizontal=True)
        lanes = db[db['القسم'] == sec]
        
        # تنظيم الكاونترات بشكل عرضي احترافي
        cols_count = 4 if "صالة القدوم" in sec else 7
        cols = st.columns(cols_count)
        
        for i, (idx, row) in enumerate(lanes.iterrows()):
            with cols[i % cols_count]:
                color = "#28a745" if row["الحالة"] == "مشغول" else "#dc3545" if row["الحالة"] == "عطل" else "#6c757d"
                st.markdown(f'<div class="lane-box" style="background-color:{color};">{row["النوع"]} {row["المسار"]}<br>{row["الموظف"]}</div>', unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                if row["الحالة"] == "فارغ":
                    if st.button("استلام", key=f"in_{idx}"):
                        db.at[idx, 'الحالة'], db.at[idx, 'الموظف'], db.at[idx, 'الوقت'] = "مشغول", "admin", datetime.now().strftime("%H:%M")
                        db.to_csv(DB_FILE, index=False); st.rerun()
                elif row["الحالة"] == "مشغول":
                    if c1.button("تسليم", key=f"out_{idx}"):
                        db.at[idx, 'الحالة'], db.at[idx, 'الموظف'], db.at[idx, 'الوقت'] = "فارغ", "-", "-"
                        db.to_csv(DB_FILE, index=False); st.rerun()
                    if c2.button("🚨 عطل", key=f"err_{idx}"):
                        db.at[idx, 'الحالة'], db.at[idx, 'البلاغ'] = "عطل", "عطل فني"
                        db.to_csv(DB_FILE, index=False); st.rerun()
                elif row["الحالة"] == "عطل":
                    if st.button("✅ إصلاح", key=f"fix_{idx}"):
                        db.at[idx, 'الحالة'], db.at[idx, 'البلاغ'] = "فارغ", "سليم"
                        db.to_csv(DB_FILE, index=False); st.rerun()

    with tab2:
        st.header(f"📋 كروكي {sec} الرسمي")
        st.table(db[db['القسم'] == sec][['المسار', 'النوع', 'الحالة', 'الموظف', 'الوقت', 'البلاغ']])
        st.write("---")
        st.write(f"توقيع رئيس المناوبة: ........................ | الختم الرسمي: [ {sec} ]")
        if st.button("تصفير كافة المسارات"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()
