import streamlit as st
import pandas as pd
import os

# إعدادات رسمية وبسيطة
st.set_page_config(page_title="نظام المسار الذكي", layout="wide")

DB_FILE = "data_storage.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            return df.to_dict('records')
        except:
            pass
    initial = []
    for sec, count in [("قسم الخروج", 14), ("قسم الدخول", 14), ("قسم صالة القدوم", 8)]:
        for i in range(1, count + 1):
            initial.append({"القسم": sec, "المسار": i, "الحالة": "فارغ", "الموظف": "-", "النوع": "عادي"})
    pd.DataFrame(initial).to_csv(DB_FILE, index=False)
    return initial

if 'main_db' not in st.session_state:
    st.session_state.main_db = load_data()

def save_db():
    pd.DataFrame(st.session_state.main_db).to_csv(DB_FILE, index=False)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("بوابة المسار الذكي")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "admin" and p == "123":
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("خطأ")
else:
    # التبويبات نصية فقط كما طلبت
    tab1, tab2 = st.tabs(["العمليات الميدانية", "التقارير والطباعة"])
    
    with tab1:
        sec = st.radio("القسم الحالي:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"], horizontal=True)
        lanes = [r for r in st.session_state.main_db if r['القسم'] == sec]
        cols = st.columns(4 if "صالة القدوم" in sec else 7)
        
        for i, row in enumerate(lanes):
            with cols[i % (4 if "صالة القدوم" in sec else 7)]:
                # كود عرض مبسط جداً لتجنب خطأ TypeError
                st.write(f"مسار {row['المسار']}")
                st.write(f"الحالة: {row['الحالة']}")
                
                if row["الحالة"] == "فارغ":
                    if st.button("استلام", key=f"in_{sec}_{i}"):
                        row['الحالة'] = "مشغول"
                        row['الموظف'] = "admin"
                        save_db()
                        st.rerun()
                elif row["الحالة"] == "مشغول":
                    if st.button("تسليم", key=f"out_{sec}_{i}"):
                        row['الحالة'] = "فارغ"
                        row['الموظف'] = "-"
                        save_db()
                        st.rerun()

    with tab2:
        st.header(f"تقرير {sec}")
        st.table(pd.DataFrame(lanes)[['المسار', 'الحالة', 'الموظف']])
