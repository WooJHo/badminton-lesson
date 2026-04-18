import streamlit as st
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="대왕클럽 주말레슨 예약", page_icon="🏸", layout="centered")

@st.cache_resource
def init_connection():
    if "gcp_service_account" in st.secrets:
        return gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    else:
        return gspread.service_account(filename='secrets.json')

gc = init_connection()

st.sidebar.title("🏸 대왕클럽 레슨 메뉴")

menu = st.sidebar.radio("원하시는 회차를 선택하세요", ["3월 3회차", "4월 1회차", "4월 2회차", "4월 3회차", "4월 4회차"])

lesson_info = {
    "3월 3회차": {"sheet": "3월3회차", "date": "3월 28일", "open": datetime(2026, 3, 28, 9, 0)},
    "4월 1회차": {"sheet": "4월1회차", "date": "4월 4일", "open": datetime(2026, 4, 4, 9, 0)},
    "4월 2회차": {"sheet": "4월2회차", "date": "4월 11일", "open": datetime(2026, 4, 11, 9, 0)},
    "4월 3회차": {"sheet": "4월3회차", "date": "4월 18일", "open": datetime(2026, 4, 18, 9, 0)},
    "4월 4회차": {"sheet": "4월4회차", "date": "4월 25일", "open": datetime(2026, 4, 25, 9, 0)}
}
current_lesson = lesson_info[menu]

st.title(f'🏸 {menu} 예약 ({current_lesson["date"]})')

kst = ZoneInfo("Asia/Seoul")
now = datetime.now(kst)
open_time = current_lesson["open"].replace(tzinfo=kst)

if now < open_time:
    st.warning(f"⏳ 예약 오픈 전입니다! 오픈 예정: {current_lesson['date']} 오전 9시")
    st.stop()

try:
    doc = gc.open('대왕클럽_주말레슨')
    worksheet = doc.worksheet(current_lesson["sheet"])
    data = worksheet.get_all_records()
    
    try:
        game_col_values = worksheet.col_values(6)
    except:
        game_col_values = ["게임레슨"]
except:
    st.error("시트를 불러올 수 없습니다.")
    st.stop()

# 게임 레슨은 3월 3회차에만 활성화되도록 수정
is_game_lesson_week = menu in ["3월 3회차", "4월 4회차"]
all_booked_names = []

for row in data:
    all_booked_names.extend([str(row.get('예약자1', '')).strip(), str(row.get('예약자2', '')).strip()])
    
game_lesson_names = [name.strip() for name in game_col_values[1:] if name.strip()]

if is_game_lesson_week:
    all_booked_names.extend(game_lesson_names)
    
all_booked_names = [n for n in all_booked_names if n != ""]

student_list = ["이름을 선택하세요", "김효은", "김현", "김대중", "이대균", "이지후", "이윤성", "신주원", "한지수", "김가영"]
selected_name = st.selectbox('👇 본인 이름을 선택하고 아래 레슨을 클릭하세요', student_list)
user_name = "" if selected_name == "이름을 선택하세요" else selected_name

# ----------------- 게임 레슨 영역 -----------------
if is_game_lesson_week:
    st.write("---")
    st.subheader('🔥 게임 레슨 신청 (인원 제한 없음)')
    
    # 참가자 목록 및 직관적인 [취소] 버튼 출력
    if game_lesson_names:
        st.markdown(f"**현재 참가자 ({len(game_lesson_names)}명)**")
        
        for idx, g_name in enumerate(game_lesson_names):
            c1, c2 = st.columns([0.7, 0.3]) # 가로 비율 설정
            c1.markdown(f"👤 **{g_name}**")
            # 이름 바로 옆에 취소 버튼 생성
            if c2.button("취소", key=f"del_game_{menu}_{idx}"):
                row_idx = game_col_values.index(g_name) + 1
                worksheet.update_cell(row_idx, 6, "")
                st.rerun()
    else:
        st.info("**현재 참가자:** 아직 신청자가 없습니다.")
        
    st.write("##") # 간격 띄우기

    # 게임 레슨 신청 로직
    if user_name == "":
        st.button('👉 게임 레슨 신청하기', disabled=True, use_container_width=True)
        st.caption("위에서 이름을 먼저 선택해주세요.")
    elif user_name in game_lesson_names:
        st.success(f"✅ **{user_name}**님은 게임 레슨에 신청 완료되었습니다.")
    elif user_name in all_booked_names:
        st.warning("이미 헌볼 레슨에 예약되어 있습니다. 게임 레슨을 원하시면 헌볼 레슨을 먼저 취소해주세요.")
        st.button('👉 게임 레슨 신청하기', disabled=True, use_container_width=True)
    else:
        if st.button('👉 게임 레슨 신청하기', key="book_game", type="primary", use_container_width=True):
            next_row = len(game_col_values) + 1
            worksheet.update_cell(next_row, 6, user_name)
            st.rerun()

# ----------------- 헌볼 레슨 영역 -----------------
st.write("---")
st.subheader('⏰ 헌볼 레슨 시간표 및 예약 현황')
st.caption('헌볼 레슨과 게임 레슨 중 하나만 선택 가능합니다.' if is_game_lesson_week else '')

for i, row in enumerate(data):
    time_slot = str(row.get('시간대', '')).strip()
    
    # [에러 방지 1] 시간대가 비어있는 줄(빈 줄)은 무시하고 건너뜁니다.
    if not time_slot:
        continue
        
    with st.container():
        # [에러 방지 2] 최대인원 칸이 비어있으면 기본값 1로 처리합니다.
        raw_max_cap = str(row.get('최대인원', 1)).strip()
        max_cap = int(raw_max_cap) if raw_max_cap.isdigit() else 1
        
        b1 = str(row.get('예약자1', '')).strip()
        b2 = str(row.get('예약자2', '')).strip()
        row_num = i + 2

        col1, col2 = st.columns([2.5, 1.5])
        
        with col1:
            st.markdown(f"#### 📅 {time_slot}")
            st.caption(f"인원 현황: {len([n for n in [b1, b2] if n])}/{max_cap}명")
            
            if b1:
                c1, c2 = st.columns([0.6, 0.4])
                c1.markdown(f"👤 **{b1}**")
                if c2.button("취소", key=f"del1_{menu}_{i}"):
                    worksheet.update_cell(row_num, 3, "")
                    st.rerun()
            
            if b2:
                c1, c2 = st.columns([0.6, 0.4])
                c1.markdown(f"👤 **{b2}**")
                if c2.button("취소", key=f"del2_{menu}_{i}"):
                    worksheet.update_cell(row_num, 4, "")
                    st.rerun()
                    
        with col2:
            st.write("##") 
            if len([n for n in [b1, b2] if n]) < max_cap:
                if st.button('예약하기', key=f"reg_{menu}_{i}", use_container_width=True, type="primary"):
                    if user_name == "":
                        st.warning('이름을 먼저 선택해주세요!')
                    elif user_name in all_booked_names:
                        st.error('이미 다른 레슨(헌볼 또는 게임)에 예약되어 있습니다!')
                    else:
                        target_col = 3 if b1 == "" else 4
                        worksheet.update_cell(row_num, target_col, user_name)
                        st.rerun()
            else:
                st.button('마감 완료', key=f"full_{menu}_{i}", disabled=True, use_container_width=True)
        
        st.divider()