import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64

# --- إعدادات النظام الرسمية ---
st.set_page_config(page_title="نظام المسار الذكي - التشغيل الرسمي", layout="wide")

# --- إدارة قاعدة البيانات ---
DB_FILE = "data_storage.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE).to_dict('records')
    else:
        initial = []
        for sec, count in [("قسم الخروج", 14), ("قسم الدخول", 14), ("قسم صالة القدوم", 8)]:
            for i in range(1, count + 1):
                dtype = "🚛 شحن" if i == 13 and sec != "قسم صالة القدوم" else "⭐ خاص" if i == 14 and sec != "قسم صالة القدوم" else "عادي"
                initial.append({"القسم": sec, "المسار": i, "الحالة": "فارغ", "الموظف": "-", "النوع": dtype})
        pd.DataFrame(initial).to_csv(DB_FILE, index=False)
        return initial

def sync_data(data):
    pd.DataFrame(data).to_csv(DB_FILE, index=False)

if 'main_db' not in st.session_state:
    st.session_state.main_db = load_data()

# --- واجهة الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 بوابة المسار الذكي الرسمية")
    u = st.text_input("المستخدم")
    p = st.text_input("الرمز", type="password")
    if st.button("دخول"):
        if u == "admin" and p == "123":
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("بيانات الدخول غير صحيحة")
else:
    st.sidebar.success("تم تسجيل الدخول بنجاح")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()

    tab1, tab2 = st.tabs(["🎮 العمليات الميدانية", "📊 التقارير والطباعة"])
    
    with tab1:
        sec = st.radio("اختر القسم العملياتي:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"], horizontal=True)
        lanes = [r for r in st.session_state.main_db if r['القسم'] == sec]
        
        cols_count = 4 if "صالة القدوم" in sec else 7
        cols = st.columns(cols_count)
        
        for i, row in enumerate(lanes):
            with cols[i % cols_count]:
                # إصلاح خطأ الألوان هنا
                bg_color = "#28a745" if row["الحالة"] == "مشغول" else "#dc3545" if row["الحالة"] == "عطل" else "#6c757d"
                
                st.markdown(f"""
                    <div style='background-color:{bg_color}; color:white; padding:12px; border-radius:10px; text-align:center; margin-bottom:10px;'>
                        {row['النوع']} {row['المسار']}<br><b>{row['الموظف']}</b>
                    </div>
                """, unsafe_allow_case=True)
                
                if row["الحالة"] == "فارغ":
                    if st.button("استلام", key=f"in_{row['المسار']}_{sec}"):
                        row.update({"الحالة": "مشغول", "الموظف": "admin"})
                        sync_data(st.session_state.main_db)
                        st.rerun()
                elif row["الحالة"] == "مشغول":
                    if st.button("🚨 عطل", key=f"err_{row['المسار']}_{sec}"):
                        row.update({"الحالة": "عطل"})
                        sync_data(st.session_state.main_db)
                        st.rerun()
                    if st.button("تسليم", key=f"out_{row['المسار']}_{sec}"):
                        row.update({"الحالة": "فارغ", "الموظف": "-"})
                        sync_data(st.session_state.main_db)
                        st.rerun()

    with tab2:
        st.header("📋 كروكي الأقسام الرسمي")
        p_sec = st.selectbox("اختر القسم للطباعة:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"])
        p_df = pd.DataFrame([r for r in st.session_state.main_db if r['القسم'] == p_sec])
        st.table(p_df[['المسار', 'النوع', 'الحالة', 'الموظف']])
