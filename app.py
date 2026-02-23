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

def get_word_count(html_content):
    """
    Counts characters excluding HTML tags.
    """
    # Remove HTML tags using regex
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    # Remove extra whitespaces
    clean_text = " ".join(clean_text.split())
    return len(clean_text)

def generate_blog_post(topic, prompt_template):
    """
    Orchestrates the blog generation process.
    """
    # 1. Generate Content
    with st.spinner('🤖 AI가 글을 작성하고 있습니다... (약 10-20초 소요)'):
        content_gen = ContentGenerator()
        blog_data = content_gen.generate_blog_post(topic, prompt_template)
    
    if not blog_data:
        st.error("글 생성에 실패했습니다. API 설정을 확인해주세요.")
        return None

    # 2. Generate Image
    with st.spinner('🎨 썸네일 이미지를 생성하고 있습니다...'):
        output_dir = os.path.join("output", "streamlit_generated")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        image_gen = ImageGenerator(output_dir=output_dir)
        try:
            # Modified to disable text overlay as requested
            image_path = image_gen.generate_image(blog_data['title'], blog_data.get('image_prompt'), include_text=False)
        except Exception as e:
            st.error(f"이미지 생성 실패: {e}")
            image_path = None

    return blog_data, image_path

def main():
    st.title("✍️ 티스토리 블로그 자동생성기")
    st.markdown("""
    구글 Gemini AI를 활용하여 블로그 주제만 입력하면 **제목, 본문(HTML), 썸네일**을 자동으로 만들어줍니다.
    """)

    # Initialize session state
    if 'generated' not in st.session_state:
        st.session_state['generated'] = False

    # Sidebar for Config Check
    with st.sidebar:
        st.header("설정 상태")
        if config.GEMINI_API_KEY:
            st.success("✅ Gemini API Key 연동됨")
        else:
            st.error("❌ Gemini API Key 없음")
            st.info(".env 파일에 키를 입력해주세요.")
            
        st.divider()
        st.header("📝 서식 선택")
        template_choice = st.selectbox(
            "사용할 서식을 선택하세요:",
            ("수익형 HTML 템플릿 (코드 복붙용)", "수익형 블로그 규칙 (가이드라인)")
        )
        
        # Load default template based on choice
        if template_choice == "수익형 HTML 템플릿 (코드 복붙용)":
            default_template = templates.TEMPLATE_HTML
        else:
            default_template = templates.TEMPLATE_BASIC
        
        st.divider()
        st.header("🛠️ 특수 기능")
        st.info("글 생성 후에 아래 버튼을 사용하여 내용을 보완할 수 있습니다.")

    # Template Editor (Collapsible)
    with st.expander("🛠️ 서식(프롬프트) 직접 수정하기", expanded=False):
        st.info("AI에게 전달될 지침(프롬프트)입니다. 필요하다면 내용을 직접 수정해서 사용할 수 있습니다.")
        user_template = st.text_area("프롬프트 내용", value=default_template, height=300)

    # Input Area
    st.divider()
    topic = st.text_input("블로그 주제를 입력하세요", placeholder="예: 2024년 해외여행 추천지, 다이어트 식단 가이드")
    
    if st.button("🚀 글 생성하기", type="primary"):
        if not topic:
            st.warning("주제를 입력해주세요.")
            return

        if not config.GEMINI_API_KEY:
            st.error("API Key가 설정되지 않았습니다. 사이드바를 확인하세요.")
            return

        # Run Generation
        result = generate_blog_post(topic, user_template)
        
        if result:
            blog_data, image_path = result
            st.session_state['blog_data'] = blog_data
            st.session_state['image_path'] = image_path
            st.session_state['generated'] = True
            st.session_state['topic'] = topic

    # Display Results
    if st.session_state.get('generated'):
        st.divider()
        st.header("🎉 생성 결과")
        
        blog_data = st.session_state['blog_data']
        image_path = st.session_state['image_path']
        current_topic = st.session_state.get('topic', topic)

        # Refinement Actions
        col_act1, col_act2, col_act3 = st.columns(3)
        
        with col_act1:
            if st.button("🔍 최신 정보 검증 및 보완", use_container_width=True):
                with st.spinner("최신 정보를 확인 중입니다..."):
                    content_gen = ContentGenerator()
                    new_content = content_gen.verify_and_rewrite(blog_data['content'], current_topic)
                    if new_content:
                        st.session_state['blog_data']['content'] = new_content
                        st.success("정보 검증 및 보완 완료!")
                        st.rerun()

        with col_act2:
            if st.button("✍️ 맞춤법 검사 및 교정", use_container_width=True):
                with st.spinner("맞춤법을 교정 중입니다..."):
                    content_gen = ContentGenerator()
                    new_content = content_gen.spell_check_and_refine(blog_data['content'])
                    if new_content:
                        st.session_state['blog_data']['content'] = new_content
                        st.success("맞춤법 및 문장 교정 완료!")
                        st.rerun()

        with col_act3:
            word_count = get_word_count(blog_data['content'])
            st.metric("글자 수 (공백 제외)", f"{word_count}자")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("1. 썸네일 이미지")
            if image_path:
                st.image(image_path, caption="SEO 최적화 썸네일 (800x800, No Text)", use_column_width=True)
                
                with open(image_path, "rb") as file:
                    btn = st.download_button(
                        label="📥 이미지 다운로드",
                        data=file,
                        file_name="thumbnail.jpg",
                        mime="image/jpeg"
                    )

        with col2:
            st.subheader("2. 블로그 정보")
            st.session_state['blog_data']['title'] = st.text_input("제목", value=blog_data['title'])
            tags_str = st.text_input("태그", value=", ".join(blog_data.get('tags', [])))
            st.session_state['blog_data']['tags'] = [t.strip() for t in tags_str.split(",")]

        st.divider()
        
        st.subheader("3. 본문 HTML (복사용)")
        st.markdown("아래 코드를 복사해서 티스토리 에디터의 **HTML 모드**에 붙여넣으세요.")
        st.code(blog_data['content'], language='html')

        st.divider()
        st.subheader("4. 미리보기")
        
        # Clean markdown fences and indentation for preview
        preview_content = blog_data['content'].strip()
        
        # 1. Remove Markdown Code Fences (```html or ```)
        if preview_content.startswith("```"):
            lines = preview_content.split('\n')
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            preview_content = "\n".join(lines)
            
        # 2. Remove Indentation
        lines = preview_content.split('\n')
        cleaned_lines = [line.lstrip() for line in lines]
        preview_content = "\n".join(cleaned_lines)
            
        st.markdown(preview_content, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
