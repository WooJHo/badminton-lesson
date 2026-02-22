import streamlit as st
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo

# 브라우저 설정
st.set_page_config(
    page_title="대왕클럽 주말 레슨 예약",
    page_icon="🏸",
    layout="centered"
)

@st.cache_resource
def init_connection():
    if "gcp_service_account" in st.secrets:
        return gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    else:
        return gspread.service_account(filename='secrets.json')

gc = init_connection()

# ---------------------------------------------------------
# [사이드바 메뉴 설정]
st.sidebar.title("🏸 대왕클럽 레슨 메뉴")
menu = st.sidebar.radio(
    "원하시는 회차를 선택하세요",
    ["2월 3회차", "3월 1회차", "3월 2회차", "3월 3회차"]
)

# [각 회차별 상세 정보 설정]
# (시트이름, 해당레슨날짜, 오픈날짜)
lesson_info = {
    "2월 3회차": {"sheet": "2월3회차", "date": "2월 28일", "open": datetime(2026, 2, 22, 9, 0)},
    "3월 1회차": {"sheet": "3월1회차", "date": "3월 7일", "open": datetime(2026, 3, 7, 9, 0)},
    "3월 2회차": {"sheet": "3월2회차", "date": "3월 14일", "open": datetime(2026, 3, 14, 9, 0)},
    "3월 3회차": {"sheet": "3월3회차", "date": "3월 21일", "open": datetime(2026, 3, 21, 9, 0)}
}

current_lesson = lesson_info[menu]
# ---------------------------------------------------------

st.title(f'🏸 대왕클럽 {menu} 예약 ({current_lesson["date"]})')

# [시간 체크 로직]
kst = ZoneInfo("Asia/Seoul")
now = datetime.now(kst)
open_time = current_lesson["open"].replace(tzinfo=kst)

if now < open_time:
    st.warning(f"⏳ **본 회차는 아직 예약 오픈 전입니다!**\n\n**오픈 예정:** {current_lesson['date']} 오전 9시 00분\n\n(현재 시간: {now.strftime('%m월 %d일 %H시 %M분')})")
    st.stop()

# --- 여기서부터는 오픈 시간이 지났을 때 실행되는 예약 화면 ---

st.markdown(f'**우지호 코치님**의 {current_lesson["date"]} 레슨, 선착순으로 예약하세요! 🔥')

with st.expander("📢 레슨 예약 필독 공지사항"):
    st.info("""
    - **예약 원칙:** 1인당 1개의 타임만 신청 가능합니다.
    - **시간 변경:** 기존 예약을 먼저 취소한 뒤 다른 시간을 선택해 주세요.
    - **취소 규정:** 당일 취소는 노쇼 처리될 수 있으니 주의 부탁드립니다.
    """)

# 선택된 회차의 시트 불러오기
try:
    doc = gc.open('대왕클럽_주말레슨')
    worksheet = doc.worksheet(current_lesson["sheet"])
    data = worksheet.get_all_records()
except Exception as e:
    st.error(f"시트를 불러오는 중 오류가 발생했습니다. 시트 이름이 [{current_lesson['sheet']}]인지 확인해주세요.")
    st.stop()

st.write("---") 

# 명단 (필요시 수정 가능)
student_list = ["이름을 선택하세요", "김효은", "김현", "이종희", "이대균", "이지후", "이윤성", "신주원", "한지수", "김가영"]
selected_name = st.selectbox('👇 본인 이름을 선택해주세요', student_list)

user_name = "" if selected_name == "이름을 선택하세요" else selected_name

# 사용자 예약 확인 로직
user_booked_slot = None
user_row_idx = None
user_col_idx = None

for i, row in enumerate(data):
    row_number = i + 2
    b1, b2 = str(row.get('예약자1', '')).strip(), str(row.get('예약자2', '')).strip()
    
    if user_name != "" and b1 == user_name:
        user_booked_slot, user_row_idx, user_col_idx = str(row.get('시간대', '')), row_number, 3
        break
    elif user_name != "" and b2 == user_name:
        user_booked_slot, user_row_idx, user_col_idx = str(row.get('시간대', '')), row_number, 4
        break

if user_booked_slot:
    st.success(f"✅ **{user_name}**님은 현재 **[{user_booked_slot}]** 타임에 예약되어 있습니다.")
    if st.button('🚨 내 예약 취소하기', use_container_width=True): 
        worksheet.update_cell(user_row_idx, user_col_idx, "")
        st.rerun()

st.write("---")
st.subheader('⏰ 실시간 레슨 시간표')

for i, row in enumerate(data):
    time_slot = str(row.get('시간대', ''))
    max_cap = int(row.get('최대인원', 1))
    b1, b2 = str(row.get('예약자1', '')).strip(), str(row.get('예약자2', '')).strip()
    
    row_number = i + 2 
    booked_names = [n for n in [b1, b2] if n != ""]
    current_count = len(booked_names)
    
    col1, col2 = st.columns([2.5, 1.5]) 
    with col1:
        st.write(f"**{time_slot}** ({current_count}/{max_cap}명)")
        if current_count > 0:
            st.caption(f"예약자: {', '.join(booked_names)}")
            
    with col2:
        if current_count < max_cap:
            if st.button('예약하기', key=f"btn_{menu}_{time_slot}", use_container_width=True):
                if user_name == "":
                    st.warning('이름을 먼저 선택해주세요!')
                elif user_booked_slot:
                    st.error('이미 예약 내역이 있습니다!')
                else:
                    target_col = 3 if b1 == "" else 4
                    worksheet.update_cell(row_number, target_col, user_name)
                    st.rerun()
        else:
            st.button('마감 완료', key=f"btn_{menu}_{time_slot}", disabled=True, use_container_width=True)

