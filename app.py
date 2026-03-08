import streamlit as st
import config
from content_generator import ContentGenerator
from image_generator import ImageGenerator
import os
import templates
import re
import urllib.parse
import time
import base64
import requests
import io
import json
import streamlit.components.v1 as components

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

def generate_blog_post(topic, prompt_template, api_key=None, selected_model=None):
    """
    Orchestrates the blog generation process.
    Returns: (blog_data, image_url, error_message)
    """
    # 1. Generate Content
    with st.spinner('🤖 AI가 글을 작성하고 있습니다...'):
        content_gen = ContentGenerator(api_key=api_key, selected_model=selected_model)
        blog_data, error_detail = content_gen.generate_blog_post(topic, prompt_template)
    
    if not blog_data:
        full_error = f"글 생성에 실패했습니다.\n\n**상세 원인:** {error_detail}"
        return None, None, full_error

    # 2. Generate Image URL
    with st.spinner('🎨 AI가 주제와 관련된 이미지를 생성하고 있습니다...'):
        image_gen = ImageGenerator()
        try:
            # Prefer the concise thumbnail_title for thumbnails
            display_title = blog_data.get('thumbnail_title', blog_data['title'])
            
            # Pass keywords to improve relevance
            image_url = image_gen.get_image_url(
                display_title, 
                prompt=blog_data.get('image_prompt'),
                keywords=blog_data.get('image_keywords')
            )
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
        st.header("🤖 AI 모델 선택")
        model_options = (
            'gemini-3-flash',
            'gemini-2.5-flash',
            'gemini-2.5-pro',
            'gemini-2.0-flash', 
            'gemini-2.0-flash-lite', 
            'gemini-1.5-flash', 
            'gemini-1.5-pro', 
            '직접 입력 (Manual Entry)'
        )
        selected_option = st.selectbox(
            "사용할 Gemini 모델을 선택하세요:",
            model_options,
            index=0,
            help="AI Studio에서 할당량이 남은 모델을 선택하세요."
        )
        
        if selected_option == '직접 입력 (Manual Entry)':
            active_model = st.text_input("모델 이름을 직접 입력하세요:", value="gemini-3-flash", help="AI Studio에 표시된 정확한 모델명을 입력하세요.")
        else:
            active_model = selected_option
        
        st.divider()
        st.header("📝 서식 선택")
        
        # Cloud Sync Initialization
        from firebase_sync import FirebaseSync
        fb_sync = FirebaseSync()
        if fb_sync.db:
            st.sidebar.success("📊 Firebase 클라우드 동기화 활성")

        # Load custom templates (Local + Cloud Sync)
        CUSTOM_TEMPLATES_FILE = "custom_templates.json"
        
        def load_custom_templates():
            # 1. Start with local templates (로컬이 기준)
            local_templates = {}
            if os.path.exists(CUSTOM_TEMPLATES_FILE):
                with open(CUSTOM_TEMPLATES_FILE, "r", encoding="utf-8") as f:
                    try: local_templates = json.load(f)
                    except: local_templates = {}
            
            # 2. Sync with Firebase (클라우드에만 있는 서식을 로컬에 추가, 로컬 서식은 덮어쓰지 않음)
            cloud_templates = fb_sync.fetch_templates()
            if cloud_templates:
                for name, prompt in cloud_templates.items():
                    if name not in local_templates:  # 로컬에 없는 것만 추가
                        local_templates[name] = prompt
            
            return local_templates

        def save_custom_templates(templates_dict):
            # 1. Save locally
            with open(CUSTOM_TEMPLATES_FILE, "w", encoding="utf-8") as f:
                json.dump(templates_dict, f, ensure_ascii=False, indent=4)
            
            # 2. Save to Firebase
            fb_sync.save_templates(templates_dict)

        custom_templates = load_custom_templates()
        
        # Merge built-in and custom templates
        builtin_names = ("수익형 HTML 템플릿 (코드 복붙용)", "수익형 블로그 규칙 (가이드라인)")
        all_template_names = builtin_names + tuple(custom_templates.keys())
        
        template_choice = st.selectbox(
            "사용할 서식을 선택하세요:",
            all_template_names
        )
        
        # Sidebar Management UI
        with st.expander("🚀 서식 추가/관리"):
            new_title = st.text_input("새 서식 이름", placeholder="예: 맛집 리뷰 서식")
            
            # Pre-fill from direct edit if available
            initial_prompt = st.session_state.get('new_prompt_from_edit', "")
            new_prompt = st.text_area("서식 프롬프트 ( {topic} 포함 필수 )", value=initial_prompt, height=150, help="AI에게 전달할 상세 지시사항을 입력하세요. 주제가 들어갈 자리에 {topic}을 넣어주세요.")
            if st.button("➕ 서식 저장", use_container_width=True):
                if new_title and new_prompt:
                    if "{topic}" not in new_prompt:
                        st.error("{topic} 키워드가 프롬프트에 포함되어야 합니다.")
                    else:
                        custom_templates[new_title] = new_prompt
                        save_custom_templates(custom_templates)
                        st.success(f"'{new_title}' 서식이 저장되었습니다.")
                        st.rerun()
                else:
                    st.warning("이름과 프롬프트를 모두 입력해주세요.")
            
            if len(custom_templates) > 0:
                st.divider()
                del_title = st.selectbox("삭제할 서식 선택", tuple(custom_templates.keys()))
                if st.button("🗑️ 서식 삭제", use_container_width=True):
                    if del_title in custom_templates:
                        del custom_templates[del_title]
                        save_custom_templates(custom_templates)
                        st.success(f"'{del_title}' 서식이 삭제되었습니다.")
                        st.rerun()

            st.divider()
            st.markdown("### 📥 서식 구성 가이드")
            st.info("새 서식을 만들 때 아래 예시를 복사해서 수정해 보세요.")
            guide_example = """당신은 티스토리 블로그 전문가입니다. 
주제: "{topic}"에 대해 작성하세요.
말투: 친절한 해요체
필수 포함: 서론, 본문 제목(h2), 결론
분량: 매우 길게 작성"""
            st.code(guide_example, language="text")
            st.caption("⚠️ {topic} 이 반드시 포함되어야 합니다.")
            
            with st.expander("🔑 클라우드 저장 설정 (Firebase)"):
                st.markdown("""
                ### ☁️ 서식 영구 저장 방법
                Streamlit Cloud 환경에서는 앱이 재부팅될 때 파일이 지워집니다. 아래 설정을 완료하면 서식이 **영구적으로 보존**됩니다.
                
                1. [Firebase Console](https://console.firebase.google.com/)에서 프로젝트 생성
                2. **Project Settings > Service accounts** 로 이동
                3. **Generate new private key** 클릭하여 JSON 파일 저장
                4. 저장한 JSON 파일의 내용을 복사
                5. Streamlit Cloud의 **Manage App > Secrets** 메뉴에 아래와 같이 입력:
                ```toml
                firebase_key = '''
                { 여기에 복사한 JSON 내용 붙여넣기 }
                '''
                ```
                """)

        if template_choice == "수익형 HTML 템플릿 (코드 복붙용)":
            default_template = templates.TEMPLATE_HTML
        elif template_choice == "수익형 블로그 규칙 (가이드라인)":
            default_template = templates.TEMPLATE_BASIC
        else:
            default_template = custom_templates.get(template_choice, templates.TEMPLATE_BASIC)
        
        st.divider()
        st.write("💡 **팁**: 글 생성 후에 상단 버튼으로 내용을 한층 더 다듬을 수 있습니다.")

    # Template Editor
    with st.expander("🛠️ 서식(프롬프트) 직접 수정하기", expanded=False):
        user_template = st.text_area("프롬프트 내용", value=default_template, height=300)
        
        # Persistence Logic
        if template_choice in custom_templates:
            if st.button("💾 이 서식을 저장하기", use_container_width=True):
                # Update existing custom template
                custom_templates[template_choice] = user_template
                save_custom_templates(custom_templates)
                st.success(f"'{template_choice}' 서식이 업데이트되었습니다.")
                st.rerun()
        else:
            # Built-in template
            st.info("기본 서식입니다. 수정한 내용을 새 서식으로 저장하려면 이름을 입력해 주세요.")
            new_save_name = st.text_input("새 서식 이름 입력", key="new_save_name_editor", placeholder="예: 나만의 수익형 서식")
            if st.button("💾 새 서식으로 저장", use_container_width=True):
                if new_save_name and user_template:
                    if "{topic}" not in user_template:
                        st.error("{topic} 키워드가 프롬프트에 포함되어야 합니다.")
                    else:
                        custom_templates[new_save_name] = user_template
                        save_custom_templates(custom_templates)
                        st.success(f"'{new_save_name}' 서식이 저장되었습니다.")
                        st.rerun()
                else:
                    st.warning("새 서식의 이름을 입력해 주세요.")
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
        blog_data, image_path, error_message = generate_blog_post(topic, user_template, api_key=active_api_key, selected_model=active_model)
        
        if blog_data:
            if 'content' not in blog_data:
                st.error("AI 응답 형식이 올바르지 않습니다. (본문 내용 누락) 다시 시도해 주세요.")
                return
                
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
                        content_gen = ContentGenerator(api_key=active_api_key, selected_model=active_model)
                        new_content, error_msg = content_gen.verify_and_rewrite(blog_data['content'], current_topic)
                        if new_content:
                            st.session_state['blog_data']['content'] = new_content
                            st.session_state['fact_checked'] = True
                            st.success("정보 보완이 완료되었습니다!")
                            st.rerun()
                        else:
                            st.error(f"정보 보완에 실패했습니다. 원인: {error_msg}")

            with b_col2:
                btn_label = "✍️ 맞춤법 검사 및 교정"
                if st.session_state['spell_checked']:
                    btn_label += " (✅ 완료)"
                    
                if st.button(btn_label, key="spell_check_btn", use_container_width=True):
                    with st.spinner("맞춤법 및 문법을 교정 중입니다..."):
                        content_gen = ContentGenerator(api_key=active_api_key, selected_model=active_model)
                        new_content, error_msg = content_gen.spell_check_and_refine(blog_data['content'])
                        if new_content:
                            st.session_state['blog_data']['content'] = new_content
                            st.session_state['spell_checked'] = True
                            st.success("맞춤법 교정이 완료되었습니다!")
                            st.rerun()
                        else:
                            st.error(f"맞춤법 교정에 실패했습니다. 원인: {error_msg}")

        with act_col2:
            content_to_count = blog_data.get('content', '')
            counts = get_word_count_details(content_to_count)
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
                # Use native Streamlit image for better reliability
                st.image(image_path, use_container_width=True)
                
                # Keyword control for Stock Photos
                current_kw = blog_data.get('image_keywords', 'nature')
                # FORCE update label text to break caching
                new_kw = st.text_input("🔍 이미지 테마 키워드 (영문 검색어)", value=current_kw, help="스톡 사진 검색 시 사용될 키워드입니다. 콤마(,)로 구분하세요.")
                if new_kw != current_kw:
                    blog_data['image_keywords'] = new_kw

                # Image Action Buttons
                c1, c2 = st.columns(2)
                with c1:
                    is_data_url = image_path.startswith("data:image")
                    
                    if is_data_url:
                        # For self-generated JPGs or embedded images
                        try:
                            import base64
                            parts = image_path.split(",", 1)
                            if len(parts) == 2:
                                data = base64.b64decode(parts[1])
                                st.download_button(
                                    label="💾 JPG 이미지 컴퓨터에 저장",
                                    data=data,
                                    file_name=f"thumbnail_{int(time.time())}.jpg",
                                    mime="image/jpeg",
                                    use_container_width=True
                                )
                            else:
                                st.error("이미지 데이터를 해석할 수 없습니다.")
                        except Exception as e:
                            st.warning(f"저장 시도 중 오류: {e}")
                            st.link_button("🔗 브라우저에서 열기", image_path, use_container_width=True)
                    else:
                        # For stock photos (Unsplash/External JPG) - Be extremely robust
                        try:
                            headers = {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                            }
                            # allow_redirects=True is default but let's be explicit
                            response = requests.get(image_path, headers=headers, timeout=15, allow_redirects=True)
                            if response.status_code == 200:
                                st.download_button(
                                    label="💾 JPG 이미지 컴퓨터에 저장",
                                    data=response.content,
                                    file_name=f"stock_image_{int(time.time())}.jpg",
                                    mime="image/jpeg",
                                    use_container_width=True
                                )
                            else:
                                st.error(f"이미지 서버 응답 오류 ({response.status_code})")
                                st.link_button("🔗 원본 링크로 열기 (브라우저 차단 가능)", image_path, use_container_width=True)
                        except Exception as e:
                            st.error(f"다운로드 연결 실패: {e}")
                            st.link_button("🔗 원본 링크로 열기 (브라우저 차단 가능)", image_path, use_container_width=True)
                
                with c2:
                    if st.button("🔄 새로운 색상/배경으로 변경", type="primary", use_container_width=True):
                        image_gen = ImageGenerator()
                        display_title = blog_data.get('thumbnail_title', blog_data['title'])
                        st.session_state['image_path'] = image_gen.get_jpg_thumbnail(display_title)
                        st.rerun()

                # Robust Fallback Options
                st.markdown("---")
                st.markdown("##### 🛠️ 다른 스타일의 이미지가 필요하신가요?")
                
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    if st.button("✅ 텍스트 썸네일 (기본값)", use_container_width=True):
                        image_gen = ImageGenerator()
                        display_title = blog_data.get('thumbnail_title', blog_data['title'])
                        st.session_state['image_path'] = image_gen.get_jpg_thumbnail(display_title)
                        st.rerun()
                
                with f_col2:
                    # Show keywords being used for transparency
                    kw_to_show = blog_data.get('image_keywords', blog_data['title'])
                    if st.button("🖼️ 고화질 스톡 사진 (관련 이미지)", use_container_width=True, help=f"검색어: {kw_to_show}"):
                        image_gen = ImageGenerator()
                        st.session_state['image_path'] = image_gen.get_stock_image_url(
                            blog_data['title'], 
                            keywords=blog_data.get('image_keywords')
                        )
                        st.rerun()
                
                search_query = blog_data['title']
                search_url = f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(search_query)}"
                pixabay_url = f"https://pixabay.com/images/search/{urllib.parse.quote(blog_data.get('image_keywords', search_query))}/"
                
                st.markdown(f"""
                <div style="display: flex; gap: 10px; margin-top: 5px;">
                    <a href="{search_url}" target="_blank" style="flex: 1; text-align: center; background-color: #4285f4; color: white; padding: 10px; border-radius: 5px; text-decoration: none; font-size: 14px;">🔍 Google 이미지 검색</a>
                    <a href="{pixabay_url}" target="_blank" style="flex: 1; text-align: center; background-color: #05a081; color: white; padding: 10px; border-radius: 5px; text-decoration: none; font-size: 14px;">🖼️ Pixabay 무료 이미지</a>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("이미지 정보가 없습니다.")
                if st.button("🖼️ 이미지 다시 생성", use_container_width=True):
                    image_gen = ImageGenerator()
                    st.session_state['image_path'] = image_gen.get_jpg_thumbnail(st.session_state.get('topic', 'Blog'))
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
            # Robust Preview using components.html to solve code-leak/rendering bugs
            preview_content = blog_data['content'].strip()
            
            # 1. Strip triple backticks if the AI wrapped the entire JSON/HTML
            if preview_content.startswith("```"):
                lines = preview_content.split('\n')
                if lines[0].strip().startswith("```"): lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"): lines = lines[:-1]
                preview_content = "\n".join(lines)
            
            # Simple sanitization or placeholder replacement if needed
            # (Keeping it as is for transparency since user confirmed)
            
            # 2. Add modern CSS for Tistory-like feel
            styled_html = f"""
            <div style="font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; line-height: 1.7; color: #333; max-width: 100%; overflow-x: hidden;">
                {preview_content}
            </div>
            <style>
                img {{ max-width: 100%; height: auto; border-radius: 10px; margin: 20px 0; }}
                h2, h3 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 30px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f8f9fa; }}
                blockquote {{ border-left: 5px solid #eee; padding-left: 20px; color: #666; font-style: italic; }}
            </style>
            """
            
            # Render in an iframe to prevent CSS leakage and solve st.markdown issues
            components.html(styled_html, height=800, scrolling=True)

if __name__ == "__main__":
    main()
