import streamlit as st
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="대왕클럽 주말 레슨 예약", page_icon="🏸", layout="centered")

@st.cache_resource
def init_connection():
    if "gcp_service_account" in st.secrets:
        return gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    else:
        return gspread.service_account(filename='secrets.json')

gc = init_connection()

# 사이드바 설정
st.sidebar.title("🏸 대왕클럽 레슨 메뉴")
menu = st.sidebar.radio("원하시는 회차를 선택하세요", ["2월 3회차 보강", "3월 1회차", "3월 2회차", "3월 3회차"])

lesson_info = {
    "2월 3회차 보강": {"sheet": "2월3회차 보강", "date": "3월 7일", "open": datetime(2026, 3, 7, 9, 0)},
    "3월 1회차": {"sheet": "3월1회차", "date": "3월 14일", "open": datetime(2026, 3, 14, 9, 0)},
    "3월 2회차": {"sheet": "3월2회차", "date": "3월 21일", "open": datetime(2026, 3, 21, 9, 0)},
    "3월 3회차": {"sheet": "3월3회차", "date": "3월 28일", "open": datetime(2026, 3, 28, 9, 0)}
}
current_lesson = lesson_info[menu]

st.title(f'🏸 {menu} 예약 ({current_lesson["date"]})')

# 시간 체크
kst = ZoneInfo("Asia/Seoul")
now = datetime.now(kst)
open_time = current_lesson["open"].replace(tzinfo=kst)

if now < open_time:
    st.warning(f"⏳ 예약 오픈 전입니다! 오픈 예정: {current_lesson['date']} 오전 9시")
    st.stop()

# 시트 불러오기
try:
    doc = gc.open('대왕클럽_주말레슨')
    worksheet = doc.worksheet(current_lesson["sheet"])
    data = worksheet.get_all_records()
except:
    st.error("시트를 불러올 수 없습니다.")
    st.stop()

# 전체 예약자 명단 수집 (중복 체크용)
all_booked_names = []
for row in data:
    all_booked_names.extend([str(row.get('예약자1', '')).strip(), str(row.get('예약자2', '')).strip()])
all_booked_names = [n for n in all_booked_names if n != ""]

# 상단 이름 선택 (신규 예약용)
student_list = ["이름을 선택하세요", "김효은", "김현", "이종희", "이대균", "이지후", "이윤성", "신주원", "한지수", "김가영"]
selected_name = st.selectbox('👇 본인 이름을 선택하고 아래 시간을 클릭하세요', student_list)
user_name = "" if selected_name == "이름을 선택하세요" else selected_name

st.write("---")
st.subheader('⏰ 실시간 시간표 및 예약 현황')

for i, row in enumerate(data):
    # 여기서부터 들여쓰기가 중요합니다! 각 타임대를 하나의 박스에 담습니다.
    with st.container():
        time_slot = str(row.get('시간대', ''))
        max_cap = int(row.get('최대인원', 1))
        b1 = str(row.get('예약자1', '')).strip()
        b2 = str(row.get('예약자2', '')).strip()
        row_num = i + 2

        # UI 구성: 시간대와 현황
        col1, col2 = st.columns([2.5, 1.5])
        
        with col1:
            # 시간대를 조금 더 강조해서 크게 표시
            st.markdown(f"#### 📅 {time_slot}")
            st.caption(f"인원 현황: {len([n for n in [b1, b2] if n])}/{max_cap}명")
            
            # 예약자 1 표시 및 취소 버튼
            if b1:
                c1, c2 = st.columns([0.6, 0.4])
                c1.markdown(f"👤 **{b1}**")
                if c2.button("취소", key=f"del1_{menu}_{i}"):
                    worksheet.update_cell(row_num, 3, "")
                    st.rerun()
            
            # 예약자 2 표시 및 취소 버튼
            if b2:
                c1, c2 = st.columns([0.6, 0.4])
                c1.markdown(f"👤 **{b2}**")
                if c2.button("취소", key=f"del2_{menu}_{i}"):
                    worksheet.update_cell(row_num, 4, "")
                    st.rerun()
                    
        with col2:
            # 버튼 위치를 시간대 타이틀과 맞추기 위해 투명한 빈칸(##) 추가
            st.write("##") 
            
            # 빈자리가 있고, 현재 선택한 유저가 아직 예약 전일 때만 [예약하기] 활성화
            if len([n for n in [b1, b2] if n]) < max_cap:
                # '예약하기' 버튼을 파란색(primary)으로 강조
                if st.button('예약하기', key=f"reg_{menu}_{i}", use_container_width=True, type="primary"):
                    if user_name == "":
                        st.warning('이름을 먼저 선택해주세요!')
                    elif user_name in all_booked_names:
                        st.error('이미 다른 타임에 예약되어 있습니다!')
                    else:
                        target_col = 3 if b1 == "" else 4
                        worksheet.update_cell(row_num, target_col, user_name)
                        st.rerun()
            else:
                st.button('마감 완료', key=f"full_{menu}_{i}", disabled=True, use_container_width=True)
        
        # 각 시간대 블록 아래에 확실한 구분선(가로줄)을 넣어서 간격을 벌려줍니다.
        st.divider()