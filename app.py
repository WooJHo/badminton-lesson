import streamlit as st
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo # 시간대를 한국 시간으로 맞추기 위한 내장 라이브러리

# [UI 추가 1] 브라우저 탭 설정 (반드시 최상단!)
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
# [기능 추가 1] 사이드바(왼쪽 메뉴)로 회차 선택하기
st.sidebar.title("🏸 대왕클럽 레슨 메뉴")
menu = st.sidebar.radio(
    "원하시는 레슨을 선택하세요",
    ["2월 1회차 레슨", "2월 2회차 레슨", "2월 3회차 레슨", "2월 4회차 레슨 (2/28)"]
)
# ---------------------------------------------------------

# 선택한 메뉴가 4회차가 아닐 경우 (1~3회차)
if menu != "2월 4회차 레슨 (2/28)":
    st.title(f"🏸 {menu}")
    st.info("🚧 이 회차의 레슨 예약은 아직 준비 중이거나 마감이 완료되었습니다. \n\n**'2월 4회차 레슨 (2/28)'**을 선택해주세요.")

# 선택한 메뉴가 4회차일 경우
else:
    st.title('🏸 대왕클럽 2월 4회차 예약 (2/28)')
    
    # ---------------------------------------------------------
    # [기능 추가 2] 티켓팅 오픈 시간 설정 (한국 시간 기준)
    kst = ZoneInfo("Asia/Seoul")
    now = datetime.now(kst)
    
    # 오픈 시간 세팅: 2026년 2월 28일 오전 9시 0분 (연도는 현재 연도에 맞게 수정 가능)
    open_time = datetime(2026, 2, 28, 9, 0, tzinfo=kst)
    
    # 아직 오픈 시간이 안 되었다면?
    if now < open_time:
        st.warning(f"⏳ **아직 예약 오픈 전입니다!**\n\n**오픈 예정 시간:** 2월 28일 오전 9시 00분\n\n(현재 시간: {now.strftime('%m월 %d일 %H시 %M분')})")
        # 여기서 코드를 강제로 멈춥니다! 아래의 예약 화면은 그려지지 않습니다.
        st.stop()
    # ---------------------------------------------------------

    # --- 여기서부터는 시간이 지났을 때만 보이는 진짜 예약 화면 ---
    st.markdown('**우지호 코치님**의 2월 28일 주말 레슨, 선착순으로 빠르게 예약하세요! 🔥')

    with st.expander("📢 레슨 예약 필독 공지사항 (클릭해서 확인)"):
        st.info("""
        - **예약 원칙:** 1인당 1개의 타임만 신청 가능합니다.
        - **시간 변경:** 기존 예약을 먼저 취소한 뒤 다른 시간을 선택해 주세요.
        """)

    # 4회차 전용 구글 시트 탭 연결 (현재는 시트1을 씀. 나중에 시트 이름을 바꾸면 여기도 수정!)
    doc = gc.open('대왕클럽_주말레슨')
    worksheet = doc.sheet1
    data = worksheet.get_all_records()

    st.write("---") 

    student_list = [
        "이름을 선택하세요", 
        "김효은", "김현", "이종희", "이대균", "이지후", "이윤성", "신주원", "한지수", "김가영"
    ]

    selected_name = st.selectbox('👇 본인 이름을 선택해주세요', student_list)

    if selected_name == "이름을 선택하세요":
        user_name = ""
    else:
        user_name = selected_name

    user_booked_slot = None
    user_row_idx = None
    user_col_idx = None

    for i, row in enumerate(data):
        row_number = i + 2
        booker1 = str(row.get('예약자1', '')).strip()
        booker2 = str(row.get('예약자2', '')).strip()
        
        if user_name != "" and booker1 == user_name:
            user_booked_slot = str(row.get('시간대', ''))
            user_row_idx = row_number
            user_col_idx = 3  
            break
        elif user_name != "" and booker2 == user_name:
            user_booked_slot = str(row.get('시간대', ''))
            user_row_idx = row_number
            user_col_idx = 4  
            break

    if user_booked_slot:
        st.success(f"✅ **{user_name}**님은 현재 **[{user_booked_slot}]** 타임에 예약되어 있습니다.")
        
        if st.button('🚨 내 예약 취소하기', use_container_width=True): 
            worksheet.update_cell(user_row_idx, user_col_idx, "")
            st.rerun()

    st.write("---")
    st.subheader('⏰ 실시간 레슨 시간표')
    st.caption('원하는 시간대의 [예약하기] 버튼을 눌러주세요.') 

    for i, row in enumerate(data):
        time_slot = str(row.get('시간대', ''))
        max_cap = int(row.get('최대인원', 1))
        booker1 = str(row.get('예약자1', '')).strip()
        booker2 = str(row.get('예약자2', '')).strip()
        
        row_number = i + 2 
        
        booked_names = []
        if booker1 != "": booked_names.append(booker1)
        if booker2 != "": booked_names.append(booker2)
        
        current_count = len(booked_names)
        
        col1, col2 = st.columns([2.5, 1.5]) 
        
        with col1:
            st.write(f"**{time_slot}** ({current_count}/{max_cap}명)")
            if current_count > 0:
                st.markdown(f"<span style='color:gray; font-size:0.9em;'>예약자: {', '.join(booked_names)}</span>", unsafe_allow_html=True)
                
        with col2:
            if current_count < max_cap:
                if st.button('예약하기', key=f"btn_{time_slot}", use_container_width=True):
                    if user_name == "":
                        st.warning('위에서 본인 이름을 먼저 선택해주세요!')
                    elif user_booked_slot is not None:
                        st.error('이미 예약 내역이 있습니다. 시간을 변경하려면 먼저 기존 예약을 취소해주세요!')
                    else:
                        target_col = 3 if booker1 == "" else 4
                        worksheet.update_cell(row_number, target_col, user_name)
                        st.rerun()
            else:
                st.button('마감 완료', key=f"btn_{time_slot}", disabled=True, use_container_width=True)
                
        st.write("")

