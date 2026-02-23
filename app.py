import streamlit as st
import config
from content_generator import ContentGenerator
from image_generator import ImageGenerator
import os
import templates
import re

# Page Config
st.set_page_config(
    page_title="티스토리 블로그 자동생성기",
    page_icon="✍️",
    layout="wide"
)

def get_word_count_details(html_content):
    """
    Returns a dictionary with various word count details.
    """
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    
    # Total characters (including spaces)
    total_with_spaces = len(clean_text)
    
    # Characters excluding whitespaces
    total_no_spaces = len(re.sub(r'\s+', '', clean_text))
    
    # Korean characters only (Hangul syllables/jamo)
    korean_only = len(re.findall(r'[가-힣ㄱ-ㅎㅏ-ㅣ]', clean_text))
    
    return {
        "total_no_spaces": total_no_spaces,
        "korean_only": korean_only,
        "total_with_spaces": total_with_spaces
    }

def generate_blog_post(topic, prompt_template, api_key=None):
    """
    Orchestrates the blog generation process.
    Returns: (blog_data, image_url, error_message)
    """
    # 1. Generate Content
    with st.spinner('🤖 AI가 글을 작성하고 있습니다...'):
        content_gen = ContentGenerator(api_key=api_key)
        blog_data, error_detail = content_gen.generate_blog_post(topic, prompt_template)
    
    if not blog_data:
        full_error = f"글 생성에 실패했습니다.\n\n**상세 원인:** {error_detail}"
        return None, None, full_error

    # 2. Generate Image URL
    with st.spinner('🎨 AI가 주제와 관련된 이미지를 생성하고 있습니다...'):
        image_gen = ImageGenerator()
        try:
            image_url = image_gen.get_image_url(blog_data['title'], blog_data.get('image_prompt'))
        except Exception as e:
            st.error(f"이미지 URL 생성 실패: {e}")
            image_url = None

    return blog_data, image_url, None

def main():
    st.title("✍️ 티스토리 블로그 자동생성기")
    st.markdown("""
    구글 Gemini AI를 활용하여 블로그 주제만 입력하면 **제목, 본문(HTML), 최적화된 이미지**를 자동으로 만들어줍니다.
    """)

    # Initialize session state
    if 'generated' not in st.session_state:
        st.session_state['generated'] = False
    if 'fact_checked' not in st.session_state:
        st.session_state['fact_checked'] = False
    if 'spell_checked' not in st.session_state:
        st.session_state['spell_checked'] = False

    # Sidebar for Config & API Key
    with st.sidebar:
        st.header("⚙️ 설정 및 도구")
        
        # API Key Input
        user_api_key = st.text_input(
            "Gemini API Key 입력", 
            value="", 
            type="password",
            placeholder="여기에 키를 입력하면 우선 적용됩니다."
        )
        
        active_api_key = user_api_key if user_api_key else config.GEMINI_API_KEY
        
        if active_api_key:
            st.success("✅ Gemini API 연결됨")
        else:
            st.error("❌ API Key 필요")
            st.info("비어있을 시 .env 또는 Secrets의 키를 사용합니다.")
            
        st.warning("⚠️ **무료 버전 제한**: 일일 약 20회 정도의 글 생성이 가능하며, 초과 시 내일 다시 이용하거나 새로운 API 키를 발급받아야 합니다.")
        
        st.divider()
        st.header("📝 서식 선택")
        # ... (rest of sidebar code stays similar)
        template_choice = st.selectbox(
            "사용할 서식을 선택하세요:",
            ("수익형 HTML 템플릿 (코드 복붙용)", "수익형 블로그 규칙 (가이드라인)")
        )
        
        if template_choice == "수익형 HTML 템플릿 (코드 복붙용)":
            default_template = templates.TEMPLATE_HTML
        else:
            default_template = templates.TEMPLATE_BASIC
        
        st.divider()
        st.write("💡 **팁**: 글 생성 후에 상단 버튼으로 내용을 한층 더 다듬을 수 있습니다.")

    # Template Editor
    with st.expander("🛠️ 서식(프롬프트) 직접 수정하기", expanded=False):
        user_template = st.text_area("프롬프트 내용", value=default_template, height=300)

    # Input Area
    st.divider()
    topic = st.text_input("블로그 주제를 입력하세요", placeholder="예: 2026년 해외여행 추천지, 다이어트 식단 가이드")
    
    if st.button("🚀 블로그 글 생성 시작", type="primary"):
        if not topic:
            st.warning("주제를 입력해주세요.")
            return

        if not active_api_key:
            st.error("API Key 설정이 필요합니다.")
            return

        # Clear previous generation results and reset states
        st.session_state['generated'] = False
        st.session_state['blog_data'] = None
        st.session_state['image_path'] = None
        st.session_state['fact_checked'] = False
        st.session_state['spell_checked'] = False

        # Run Generation
        blog_data, image_path, error_message = generate_blog_post(topic, user_template, api_key=active_api_key)
        
        if blog_data:
            st.session_state['blog_data'] = blog_data
            st.session_state['image_path'] = image_path
            st.session_state['generated'] = True
            st.session_state['topic'] = topic
        else:
            st.error(error_message)

    # Display Results
    if st.session_state.get('generated'):
        st.divider()
        st.header("🎉 생성 결과")
        
        blog_data = st.session_state['blog_data']
        image_path = st.session_state['image_path']
        current_topic = st.session_state.get('topic', topic)

        # Action Area
        act_col1, act_col2 = st.columns([2, 1])
        
        with act_col1:
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                btn_label = "🔍 최신 정보 검증 및 보완"
                if st.session_state['fact_checked']:
                    btn_label += " (✅ 완료)"
                
                if st.button(btn_label, key="fact_check_btn", use_container_width=True):
                    with st.spinner("최신 정보를 확인하고 내용을 보강 중입니다..."):
                        content_gen = ContentGenerator()
                        new_content = content_gen.verify_and_rewrite(blog_data['content'], current_topic)
                        if new_content:
                            st.session_state['blog_data']['content'] = new_content
                            st.session_state['fact_checked'] = True
                            st.success("정보 보완이 완료되었습니다!")
                            st.rerun()

            with b_col2:
                btn_label = "✍️ 맞춤법 검사 및 교정"
                if st.session_state['spell_checked']:
                    btn_label += " (✅ 완료)"
                    
                if st.button(btn_label, key="spell_check_btn", use_container_width=True):
                    with st.spinner("맞춤법 및 문법을 교정 중입니다..."):
                        content_gen = ContentGenerator()
                        new_content = content_gen.spell_check_and_refine(blog_data['content'])
                        if new_content:
                            st.session_state['blog_data']['content'] = new_content
                            st.session_state['spell_checked'] = True
                            st.success("맞춤법 교정이 완료되었습니다!")
                            st.rerun()

        with act_col2:
            counts = get_word_count_details(blog_data['content'])
            # Modern word count display
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6;">
                <p style="margin-bottom: 2px; font-size: 0.8rem; color: #6c757d;">글자 수 (공백 제외)</p>
                <p style="margin: 0; font-size: 1.8rem; font-weight: bold; color: #0d6efd;">{counts['total_no_spaces']} <span style="font-size: 1rem; font-weight: normal; color: #212529;">자</span></p>
                <p style="margin: 0; font-size: 0.75rem; color: #adb5bd;">(한글: {counts['korean_only']}자 / 전체: {counts['total_with_spaces']}자)</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("1. 썸네일 이미지")
            if image_path:
                # Optimized Rendering with fallback check
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 10px; overflow: hidden; background-color: #f0f2f6; min-height: 200px; display: flex; align-items: center; justify-content: center;">
                    <img src="{image_path}" style="width: 100%; height: auto; display: block;" 
                         onerror="this.style.display='none'; this.nextSibling.style.display='block';" alt="Image">
                    <div style="display:none; padding: 20px; text-align: center; color: #666;">
                        ⚠️ 이미지를 불러올 수 없습니다. (서비스 일시 장애)<br>
                        아래 '스톡 사진으로 변경' 버튼을 눌러주세요.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.caption("AI 또는 스톡 서비스에서 제공하는 저작권 걱정 없는 이미지")

                # Action Buttons
                @st.cache_data(ttl=600)
                def fetch_image_bytes(url):
                    try:
                        import requests
                        return requests.get(url, timeout=5).content
                    except: return None

                c1, c2 = st.columns(2)
                with c1:
                    img_bytes = fetch_image_bytes(image_path)
                    if img_bytes:
                        st.download_button("📥 이미지 저장", data=img_bytes, file_name="thumnbail.jpg", mime="image/jpeg", use_container_width=True)
                    else:
                        st.button("📥 (우클릭 저장)", disabled=True, use_container_width=True)
                
                with c2:
                    if st.button("🔄 AI로 다시 생성", use_container_width=True):
                        with st.spinner("AI 이미지 생성 중..."):
                            image_gen = ImageGenerator()
                            st.session_state['image_path'] = image_gen.get_ai_image_url(blog_data['title'], blog_data.get('image_prompt'))
                            st.rerun()

                if st.button("🖼️ 고품질 스톡 사진으로 변경 (가장 확실함)", type="secondary", use_container_width=True):
                    with st.spinner("스톡 사진 불러오는 중..."):
                        image_gen = ImageGenerator()
                        st.session_state['image_path'] = image_gen.get_stock_image_url(blog_data['title'])
                        st.rerun()
                
                with st.expander("🔗 이미지 주소 및 복사"):
                    st.code(image_path)
                    st.info("위 주소를 브라우저에 직접 붙여넣어 이미지가 나오는지 확인해보세요.")
            else:
                st.warning("이미지 생성에 실패했습니다.")
                if st.button("🖼️ 스톡 사진으로 바로 생성"):
                    image_gen = ImageGenerator()
                    st.session_state['image_path'] = image_gen.get_stock_image_url(st.session_state.get('topic', 'Blog'))
                    st.session_state['generated'] = True
                    st.rerun()

        with col2:
            st.subheader("2. 블로그 정보")
            st.session_state['blog_data']['title'] = st.text_input("블로그 제목", value=blog_data['title'])
            tags_str = st.text_input("해시태그", value=", ".join(blog_data.get('tags', [])))
            st.session_state['blog_data']['tags'] = [t.strip() for t in tags_str.split(",")]
            
            st.info("💡 제목과 태그를 수정한 뒤 HTML 코드를 복사하세요.")

        st.divider()
        
        tab1, tab2 = st.tabs(["📝 본문 HTML 코드", "👀 포스팅 미리보기"])
        
        with tab1:
            st.markdown("아래 코드를 복사해서 티스토리 에디터의 **HTML 모드**에 붙여넣으세요.")
            st.code(blog_data['content'], language='html')

        with tab2:
            # Clean preview content
            preview_content = blog_data['content'].strip()
            if preview_content.startswith("```"):
                lines = preview_content.split('\n')
                if lines[0].strip().startswith("```"): lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"): lines = lines[:-1]
                preview_content = "\n".join(lines)
            
            st.markdown(preview_content, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
