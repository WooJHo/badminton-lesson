import streamlit as st
import gspread

# ---------------------------------------------------------
# [UI 추가 1] 브라우저 탭 설정 (반드시 코드 최상단에 있어야 합니다!)
st.set_page_config(
    page_title="대왕클럽 주말 레슨 예약",
    page_icon="🏸",
    layout="centered"
)
# ---------------------------------------------------------

@st.cache_resource
def init_connection():
    if "gcp_service_account" in st.secrets:
        # 인터넷(스트림릿 클라우드)에 올라갔을 때 금고에서 마스터키를 꺼내오는 방식
        return gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    else:
        # 지금처럼 내 컴퓨터에서 테스트할 때 폴더에 있는 파일을 읽는 방식
        return gspread.service_account(filename='secrets.json')

gc = init_connection()
doc = gc.open('대왕클럽_주말레슨')
worksheet = doc.sheet1

# ---------------------------------------------------------
# [UI 추가 2] 메인 타이틀 & 환영 인사 꾸미기
st.title('🏸 대왕클럽 주말반 레슨 예약')
st.markdown('**우지호 코치님**의 주말 레슨, 선착순으로 빠르게 예약하세요! 🔥')

# [UI 추가 3] 접었다 펴는 공지사항 박스
with st.expander("📢 레슨 예약 필독 공지사항 (클릭해서 확인)"):
    st.info("""
    - **예약 원칙:** 1인당 1개의 타임만 신청 가능합니다.
    - **시간 변경:** 기존 예약을 먼저 취소한 뒤 다른 시간을 선택해 주세요.
    """)
# ---------------------------------------------------------

data = worksheet.get_all_records()

st.write("---") # st.divider()와 같은 역할, 얇은 가로줄

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
    # [UI 추가 4] 취소 박스 디자인 개선
    st.success(f"✅ **{user_name}**님은 현재 **[{user_booked_slot}]** 타임에 예약되어 있습니다.")
    
    if st.button('🚨 내 예약 취소하기', use_container_width=True): # 버튼을 화면 너비에 꽉 차게!
        worksheet.update_cell(user_row_idx, user_col_idx, "")
        st.rerun()

st.write("---")
st.subheader('⏰ 실시간 레슨 시간표')
st.caption('원하는 시간대의 [예약하기] 버튼을 눌러주세요.') # 작은 글씨 안내문 추가

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
    
    # [UI 추가 5] 시간표와 버튼 비율을 모바일에 더 맞게 조정
    col1, col2 = st.columns([2.5, 1.5]) 
    
    with col1:
        st.write(f"**{time_slot}** ({current_count}/{max_cap}명)")
        if current_count > 0:
            # 이름 텍스트 색상을 회색으로 약간 흐리게
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
            
    st.write("") # 각 시간대별로 약간의 여백 추가